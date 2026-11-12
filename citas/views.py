
from datetime import datetime, timedelta

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from fisioterapeutas.models import (
    Fisioterapeuta,
    HorarioDisponible,
)
from pacientes.models import Paciente

from .forms import CitaForm, EditarCitaForm
from .models import Cita


# ROLES AUTORIZADOS

ROLES_GESTION = (
    "ADMINISTRADOR",
    "RECEPCIONISTA",
)

ROLES_AGENDAR = (
    "ADMINISTRADOR",
    "RECEPCIONISTA",
    "PACIENTE",
)

MOTIVOS_CANCELACION = {
    "cambio_horario": "Cambio de horario",
    "problemas_personales": "Problemas personales",
    "ya_no_necesita": "Ya no necesito la cita",
    "otro": "Otro",
}


# OBTENER ROL

def obtener_rol(usuario):

    if usuario.is_superuser:
        return "ADMINISTRADOR"

    perfil = getattr(usuario, "perfil", None)

    if (
        perfil is None
        or not perfil.activo
        or not usuario.is_active
    ):
        raise PermissionDenied(
            "Tu cuenta no tiene un perfil activo."
        )

    return perfil.rol


# COMPROBAR PERMISOS

def exigir_rol(usuario, permitidos):

    rol = obtener_rol(usuario)

    if rol not in permitidos:
        raise PermissionDenied(
            "No tienes permiso para realizar esta operación."
        )

    return rol


# FILTRAR CITAS DEL USUARIO

def obtener_citas_permitidas(usuario):

    citas = Cita.objects.select_related(
        "paciente__usuario__usuario",
        "fisioterapeuta__usuario__usuario",
        "servicio",
        "motivo",
    )

    rol = obtener_rol(usuario)

    # Administración y recepción ven todas las citas.
    if rol in ROLES_GESTION:
        return citas

    # El fisioterapeuta ve únicamente sus citas.
    if rol == "FISIOTERAPEUTA":
        return citas.filter(
            fisioterapeuta__usuario=usuario.perfil
        )

    # El paciente ve únicamente sus citas.
    if rol == "PACIENTE":
        return citas.filter(
            paciente__usuario=usuario.perfil
        )

    raise PermissionDenied(
        "No tienes permiso para consultar citas."
    )


# ASIGNAR PACIENTE AL FORMULARIO

def configurar_paciente(formulario, request, rol):
    """
    Impide que un paciente reserve citas a nombre
    de otra persona.
    """

    if rol != "PACIENTE":
        return True

    paciente = Paciente.objects.filter(
        usuario=request.user.perfil,
        activo=True,
        usuario__activo=True,
    ).first()

    if paciente is None:
        return False

    campo = formulario.fields["paciente"]

    campo.queryset = Paciente.objects.filter(
        pk=paciente.pk
    )

    campo.widget = forms.HiddenInput()
    campo.disabled = True

    formulario.initial["paciente"] = paciente.pk

    return True


# VERIFICAR SI LA CITA ES FUTURA

def es_fecha_futura(cita):

    instante = timezone.make_aware(
        datetime.combine(
            cita.fecha,
            cita.hora,
        ),
        timezone.get_current_timezone(),
    )

    return instante > timezone.now()


# AGENDA GENERAL

@login_required
def agenda(request):

    citas = obtener_citas_permitidas(
        request.user
    ).order_by("fecha", "hora")

    rol = obtener_rol(request.user)

    return render(
        request,
        "citas/agenda.html",
        {
            "citas": citas,
            "puede_agendar": rol in ROLES_AGENDAR,
        },
    )


# MIS CITAS

@login_required
def mis_citas(request):

    exigir_rol(
        request.user,
        ("PACIENTE",),
    )

    citas = obtener_citas_permitidas(
        request.user
    ).order_by("-fecha", "-hora")

    ahora = timezone.localtime()

    proxima_cita = citas.filter(
        Q(fecha__gt=ahora.date())
        | Q(
            fecha=ahora.date(),
            hora__gte=ahora.time(),
        ),
        estado__in=(
            Cita.Estado.PROGRAMADA,
            Cita.Estado.CONFIRMADA,
        ),
    ).order_by(
        "fecha",
        "hora",
    ).first()

    return render(
        request,
        "citas/mis_citas.html",
        {
            "citas": citas,
            "proxima_cita": proxima_cita,
        },
    )


# AGENDAR CITA

@login_required
def agendar_cita(request):

    rol = exigir_rol(
        request.user,
        ROLES_AGENDAR,
    )

    if request.method == "POST":
        formulario = CitaForm(request.POST)

    else:
        inicial = {
            clave: request.GET[clave]
            for clave in (
                "fisioterapeuta",
                "fecha",
                "hora",
            )
            if request.GET.get(clave)
        }

        formulario = CitaForm(
            initial=inicial
        )

    if not configurar_paciente(
        formulario,
        request,
        rol,
    ):
        messages.error(
            request,
            "Primero debes tener un registro "
            "de paciente activo.",
        )

        return redirect(
            "usuarios:redireccion_por_rol"
        )

    if (
        request.method == "POST"
        and formulario.is_valid()
    ):
        cita = formulario.save(
            commit=False
        )

        if rol == "PACIENTE":
            cita.paciente = (
                request.user.perfil.paciente
            )

        cita.costo_estimado = (
            cita.servicio.precio_base
        )

        cita.estado = Cita.Estado.PROGRAMADA

        try:
            with transaction.atomic():
                cita.save()

        except IntegrityError:
            formulario.add_error(
                None,
                "El horario acaba de ocuparse; "
                "selecciona otro.",
            )

        else:
            messages.success(
                request,
                "Tu cita se programó correctamente.",
            )

            return redirect(
                "citas:detalle_cita",
                cita_id=cita.pk,
            )

    return render(
        request,
        "citas/agendar_cita.html",
        {
            "form": formulario,
        },
    )


# VER DETALLE DE CITA

@login_required
def detalle_cita(request, cita_id):

    cita = get_object_or_404(
        obtener_citas_permitidas(
            request.user
        ),
        pk=cita_id,
    )

    return render(
        request,
        "citas/detalle_cita.html",
        {
            "cita": cita,
        },
    )


# VERIFICAR SI PUEDE MODIFICAR UNA CITA

def puede_modificar_cita(usuario, cita):

    rol = exigir_rol(
        usuario,
        ROLES_AGENDAR,
    )

    return (
        rol in ROLES_GESTION
        or cita.paciente.usuario_id == usuario.perfil.pk
    )


# EDITAR CITA

@login_required
def editar_cita(request, cita_id):

    exigir_rol(
        request.user,
        ROLES_AGENDAR,
    )

    if request.method == "POST":

        with transaction.atomic():

            cita = get_object_or_404(
                obtener_citas_permitidas(
                    request.user
                ).select_for_update(),
                pk=cita_id,
            )

            if not puede_modificar_cita(
                request.user,
                cita,
            ):
                raise PermissionDenied

            if cita.estado not in (
                Cita.Estado.PROGRAMADA,
                Cita.Estado.CONFIRMADA,
            ):
                messages.error(
                    request,
                    "Esta cita ya no admite modificaciones.",
                )

                return redirect(
                    "citas:detalle_cita",
                    cita_id=cita.pk,
                )

            anterior = (
                cita.fisioterapeuta_id,
                cita.fecha,
                cita.hora,
                cita.servicio_id,
            )

            formulario = EditarCitaForm(
                request.POST,
                instance=cita,
            )

            if formulario.is_valid():

                editada = formulario.save(
                    commit=False
                )

                nuevo = (
                    editada.fisioterapeuta_id,
                    editada.fecha,
                    editada.hora,
                    editada.servicio_id,
                )

                if nuevo != anterior:
                    editada.estado = (
                        Cita.Estado.PROGRAMADA
                    )

                if (
                    editada.servicio_id
                    != anterior[3]
                ):
                    editada.costo_estimado = (
                        editada.servicio.precio_base
                    )

                try:
                    with transaction.atomic():
                        editada.save()

                except IntegrityError:
                    formulario.add_error(
                        None,
                        "El horario acaba de ocuparse.",
                    )

                else:
                    messages.success(
                        request,
                        "La cita se actualizó correctamente.",
                    )

                    return redirect(
                        "citas:detalle_cita",
                        cita_id=cita.pk,
                    )

    else:

        cita = get_object_or_404(
            obtener_citas_permitidas(
                request.user
            ),
            pk=cita_id,
        )

        if not puede_modificar_cita(
            request.user,
            cita,
        ):
            raise PermissionDenied

        if cita.estado not in (
            Cita.Estado.PROGRAMADA,
            Cita.Estado.CONFIRMADA,
        ):
            messages.error(
                request,
                "Esta cita ya no admite modificaciones.",
            )

            return redirect(
                "citas:detalle_cita",
                cita_id=cita.pk,
            )

        formulario = EditarCitaForm(
            instance=cita
        )

    return render(
        request,
        "citas/editar_cita.html",
        {
            "cita": cita,
            "form": formulario,
        },
    )


# CANCELAR CITA

@login_required
def cancelar_cita(request, cita_id):

    exigir_rol(
        request.user,
        ROLES_AGENDAR,
    )

    if request.method == "POST":

        with transaction.atomic():

            cita = get_object_or_404(
                obtener_citas_permitidas(
                    request.user
                ).select_for_update(),
                pk=cita_id,
            )

            if not puede_modificar_cita(
                request.user,
                cita,
            ):
                raise PermissionDenied

            if cita.estado not in (
                Cita.Estado.PROGRAMADA,
                Cita.Estado.CONFIRMADA,
            ):
                messages.error(
                    request,
                    "Esta cita ya no puede cancelarse.",
                )

                return redirect(
                    "citas:detalle_cita",
                    cita_id=cita.pk,
                )

            motivo = request.POST.get(
                "motivo_cancelacion",
                "",
            )

            if motivo in MOTIVOS_CANCELACION:

                detalle = request.POST.get(
                    "observaciones",
                    "",
                ).strip()[:500]

                cita.motivo_cancelacion = (
                    MOTIVOS_CANCELACION[motivo]
                )

                if detalle:
                    cita.motivo_cancelacion += (
                        f". {detalle}"
                    )

                cita.estado = (
                    Cita.Estado.CANCELADA
                )

                cita.save(
                    update_fields=[
                        "motivo_cancelacion",
                        "estado",
                        "fecha_actualizacion",
                    ]
                )

                messages.success(
                    request,
                    "La cita fue cancelada correctamente.",
                )

                return redirect(
                    "citas:detalle_cita",
                    cita_id=cita.pk,
                )

            messages.error(
                request,
                "Selecciona un motivo válido "
                "de cancelación.",
            )

    else:

        cita = get_object_or_404(
            obtener_citas_permitidas(
                request.user
            ),
            pk=cita_id,
        )

        if not puede_modificar_cita(
            request.user,
            cita,
        ):
            raise PermissionDenied

        if cita.estado not in (
            Cita.Estado.PROGRAMADA,
            Cita.Estado.CONFIRMADA,
        ):
            messages.error(
                request,
                "Esta cita ya no puede cancelarse.",
            )

            return redirect(
                "citas:detalle_cita",
                cita_id=cita.pk,
            )

    return render(
        request,
        "citas/cancelar_cita.html",
        {
            "cita": cita,
        },
    )


# CONFIRMAR CITA

@login_required
def confirmar_cita(request):

    exigir_rol(
        request.user,
        ROLES_GESTION,
    )

    if request.method == "POST":

        cita_id = request.POST.get(
            "cita_id",
            "",
        )

        if (
            not cita_id.isascii()
            or not cita_id.isdecimal()
            or len(cita_id) > 18
        ):
            messages.error(
                request,
                "Selecciona una cita válida.",
            )

            return redirect(
                "citas:confirmar_cita"
            )

        with transaction.atomic():

            cita = get_object_or_404(
                Cita.objects.select_for_update(),
                pk=cita_id,
            )

            if cita.estado != (
                Cita.Estado.PROGRAMADA
            ):
                messages.error(
                    request,
                    "La cita ya no está pendiente "
                    "de confirmación.",
                )

            elif not es_fecha_futura(cita):
                messages.error(
                    request,
                    "No puedes confirmar una cita pasada.",
                )

            else:
                cita.estado = (
                    Cita.Estado.CONFIRMADA
                )

                cita.save(
                    update_fields=[
                        "estado",
                        "fecha_actualizacion",
                    ]
                )

                messages.success(
                    request,
                    "Cita confirmada correctamente.",
                )

        return redirect(
            "citas:confirmar_cita"
        )

    citas = Cita.objects.filter(
        estado=Cita.Estado.PROGRAMADA
    ).select_related(
        "paciente__usuario__usuario",
        "fisioterapeuta__usuario__usuario",
        "servicio",
        "motivo",
    ).order_by(
        "fecha",
        "hora",
    )

    return render(
        request,
        "citas/confirmar_cita.html",
        {
            "citas": citas,
        },
    )


# CITA DE EMERGENCIA

@login_required
def cita_emergencia(request):

    exigir_rol(
        request.user,
        ROLES_AGENDAR,
    )

    # Los datos de contacto se configurarán
    # posteriormente desde Administración.

    return render(
        request,
        "citas/cita_emergencia.html",
        {
            "clinica": {},
        },
    )


# HORARIOS DISPONIBLES

@login_required
def horarios_disponibles(request):

    exigir_rol(
        request.user,
        ROLES_AGENDAR,
    )

    fisioterapeutas = (
        Fisioterapeuta.objects.filter(
            activo=True,
            usuario__activo=True,
        ).select_related(
            "usuario__usuario"
        )
    )

    fisio_id = request.GET.get(
        "fisioterapeuta",
        "",
    )

    fecha_str = request.GET.get(
        "fecha",
        "",
    )

    fisioterapeuta = None

    try:
        fecha = (
            parse_date(fecha_str)
            if fecha_str
            else None
        )
    except ValueError:
        fecha = None

    horarios = []
    error = ""

    if fisio_id or fecha_str:

        if not fisio_id or not fecha:
            error = (
                "Selecciona un fisioterapeuta "
                "y una fecha válida."
            )

        else:
            fisioterapeuta = (
                fisioterapeutas.filter(
                    pk=fisio_id
                ).first()
                if fisio_id.isdigit()
                else None
            )

            if not fisioterapeuta:
                error = (
                    "El fisioterapeuta seleccionado "
                    "no está disponible."
                )

            elif fecha < timezone.localdate():
                error = (
                    "No puedes consultar horarios "
                    "de una fecha pasada."
                )

            else:

                jornadas = (
                    HorarioDisponible.objects.filter(
                        fisioterapeuta=fisioterapeuta,
                        dia_semana=fecha.isoweekday(),
                        activo=True,
                    ).order_by("hora_inicio")
                )

                citas = list(
                    Cita.objects.filter(
                        fisioterapeuta=fisioterapeuta,
                        fecha=fecha,
                    ).exclude(
                        estado=Cita.Estado.CANCELADA
                    )
                )

                ahora = timezone.now()
                zona = timezone.get_current_timezone()
                vistos = set()

                for jornada in jornadas:

                    cursor = datetime.combine(
                        fecha,
                        jornada.hora_inicio,
                    )

                    limite = datetime.combine(
                        fecha,
                        jornada.hora_fin,
                    )

                    while (
                        cursor + timedelta(minutes=60)
                        <= limite
                    ):

                        clave = cursor.time().strftime(
                            "%H:%M"
                        )

                        if clave not in vistos:

                            vistos.add(clave)

                            inicio = timezone.make_aware(
                                cursor,
                                zona,
                            )

                            fin = inicio + timedelta(
                                minutes=60
                            )

                            ocupado = False

                            for cita in citas:

                                ocupado_inicio = (
                                    timezone.make_aware(
                                        datetime.combine(
                                            cita.fecha,
                                            cita.hora,
                                        ),
                                        zona,
                                    )
                                )

                                if (
                                    inicio
                                    < ocupado_inicio
                                    + timedelta(minutes=60)
                                    and ocupado_inicio < fin
                                ):
                                    ocupado = True
                                    break

                            horarios.append(
                                {
                                    "hora": clave,
                                    "disponible": (
                                        inicio > ahora
                                        and not ocupado
                                    ),
                                }
                            )

                        cursor += timedelta(
                            minutes=60
                        )

                horarios.sort(
                    key=lambda item: item["hora"]
                )

    return render(
        request,
        "citas/horarios_disponibles.html",
        {
            "fisioterapeutas": fisioterapeutas,
            "fisioterapeuta": fisioterapeuta,
            "fisioterapeuta_id": fisio_id,
            "fecha": fecha_str,
            "horarios": horarios,
            "hay_disponibles": any(
                horario["disponible"]
                for horario in horarios
            ),
            "error": error,
        },
    )
