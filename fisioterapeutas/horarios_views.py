
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from citas.models import Cita

from .horarios_forms import HorarioDisponibleForm
from .models import Fisioterapeuta, HorarioDisponible
from .views import GESTION, profesionales_visibles, rol_actual


# VALIDAR QUE UN HORARIO CUBRA UNA CITA

def cubre_cita(horario, cita):

    if (
        not horario.activo
        or horario.dia_semana != cita.fecha.isoweekday()
    ):
        return False

    dia = cita.fecha

    inicio_jornada = datetime.combine(
        dia,
        horario.hora_inicio,
    )

    fin_jornada = datetime.combine(
        dia,
        horario.hora_fin,
    )

    inicio_cita = datetime.combine(
        dia,
        cita.hora,
    )

    diferencia = (
        inicio_cita - inicio_jornada
    ).total_seconds()

    return (
        diferencia >= 0
        and diferencia % 3600 == 0
        and inicio_cita + timedelta(hours=1) <= fin_jornada
    )


# PROTEGER CITAS FUTURAS

def validar_citas_futuras(
    fisioterapeuta,
    horario_propuesto,
    horario_id=None,
):

    jornadas_antes = list(
        HorarioDisponible.objects.filter(
            fisioterapeuta=fisioterapeuta,
            activo=True,
        )
    )

    jornadas_despues = [
        jornada
        for jornada in jornadas_antes
        if jornada.pk != horario_id
    ]

    if horario_propuesto.activo:
        jornadas_despues.append(
            horario_propuesto
        )

    citas = Cita.objects.filter(
        fisioterapeuta=fisioterapeuta,
        fecha__gte=timezone.localdate(),
        estado__in=(
            Cita.Estado.PROGRAMADA,
            Cita.Estado.CONFIRMADA,
            Cita.Estado.EN_PROCESO,
        ),
    )

    for cita in citas:

        cubierta_antes = any(
            cubre_cita(jornada, cita)
            for jornada in jornadas_antes
        )

        cubierta_despues = any(
            cubre_cita(jornada, cita)
            for jornada in jornadas_despues
        )

        if cubierta_antes and not cubierta_despues:
            raise ValidationError(
                f"El cambio dejaría sin horario válido "
                f"la cita #{cita.pk} del "
                f"{cita.fecha:%d/%m/%Y} "
                f"a las {cita.hora:%H:%M}. "
                "Reprograma esa cita antes de cambiar la jornada."
            )


# EVITAR HORARIOS TRASLAPADOS

def validar_solapamiento(
    fisioterapeuta,
    horario,
    horario_id=None,
):

    if not horario.activo:
        return

    otros = HorarioDisponible.objects.filter(
        fisioterapeuta=fisioterapeuta,
        dia_semana=horario.dia_semana,
        hora_inicio__lt=horario.hora_fin,
        hora_fin__gt=horario.hora_inicio,
        activo=True,
    ).exclude(
        pk=horario_id
    )

    if otros.exists():
        raise ValidationError(
            "La jornada se traslapa con otro horario activo."
        )


# MOSTRAR HORARIOS

@login_required
def horario_fisioterapeuta(request, fisioterapeuta_id):

    rol = rol_actual(request)

    profesional = get_object_or_404(
        profesionales_visibles(request),
        pk=fisioterapeuta_id,
    )

    horarios = profesional.horarios.order_by(
        "dia_semana",
        "hora_inicio",
    )

    if rol not in GESTION:
        horarios = horarios.filter(
            activo=True
        )

    return render(
        request,
        "fisioterapeutas/horario_fisioterapeuta.html",
        {
            "fisioterapeuta": profesional,
            "horarios": horarios,
            "puede_gestionar": rol in GESTION,
        },
    )


# REGISTRAR HORARIO

@login_required
def registrar_horario(request, fisioterapeuta_id):

    if rol_actual(request) not in GESTION:
        raise PermissionDenied

    profesional = get_object_or_404(
        Fisioterapeuta,
        pk=fisioterapeuta_id,
    )

    formulario = HorarioDisponibleForm(
        request.POST if request.method == "POST" else None,
        fisioterapeuta=profesional,
        initial={
            "activo": True,
        },
    )

    if (
        request.method == "POST"
        and formulario.is_valid()
    ):

        horario = formulario.save(
            commit=False
        )

        horario.fisioterapeuta = profesional

        try:
            with transaction.atomic():

                Fisioterapeuta.objects.select_for_update().get(
                    pk=profesional.pk
                )

                validar_solapamiento(
                    profesional,
                    horario,
                )

                horario.save()

        except ValidationError as error:
            formulario.add_error(
                None,
                error,
            )

        else:

            messages.success(
                request,
                "Horario registrado correctamente.",
            )

            return redirect(
                "fisioterapeutas:horario_fisioterapeuta",
                fisioterapeuta_id=profesional.pk,
            )

    return render(
        request,
        "fisioterapeutas/form_horario.html",
        {
            "form": formulario,
            "fisioterapeuta": profesional,
            "titulo_pagina": "Registrar horario",
            "accion": "Guardar horario",
        },
    )


# EDITAR HORARIO

@login_required
def editar_horario(request, horario_id):

    if rol_actual(request) not in GESTION:
        raise PermissionDenied

    horario = get_object_or_404(
        HorarioDisponible.objects.select_related(
            "fisioterapeuta"
        ),
        pk=horario_id,
    )

    profesional = horario.fisioterapeuta

    formulario = HorarioDisponibleForm(
        request.POST if request.method == "POST" else None,
        instance=horario,
        fisioterapeuta=profesional,
    )

    if (
        request.method == "POST"
        and formulario.is_valid()
    ):

        propuesta = formulario.save(
            commit=False
        )

        try:
            with transaction.atomic():

                Fisioterapeuta.objects.select_for_update().get(
                    pk=profesional.pk
                )

                validar_solapamiento(
                    profesional,
                    propuesta,
                    horario.pk,
                )

                validar_citas_futuras(
                    profesional,
                    propuesta,
                    horario.pk,
                )

                propuesta.save()

        except ValidationError as error:
            formulario.add_error(
                None,
                error,
            )

        else:

            messages.success(
                request,
                "Horario actualizado correctamente.",
            )

            return redirect(
                "fisioterapeutas:horario_fisioterapeuta",
                fisioterapeuta_id=profesional.pk,
            )

    return render(
        request,
        "fisioterapeutas/form_horario.html",
        {
            "form": formulario,
            "fisioterapeuta": profesional,
            "titulo_pagina": "Editar horario",
            "accion": "Guardar cambios",
        },
    )


# ACTIVAR O DESACTIVAR HORARIO

@login_required
@require_POST
def cambiar_estado_horario(request, horario_id):

    if rol_actual(request) not in GESTION:
        raise PermissionDenied

    with transaction.atomic():

        horario = get_object_or_404(
            HorarioDisponible.objects.select_related(
                "fisioterapeuta"
            ).select_for_update(),
            pk=horario_id,
        )

        profesional = horario.fisioterapeuta

        nuevo_estado = not horario.activo

        horario.activo = nuevo_estado

        try:

            if nuevo_estado and not (
                profesional.activo
                and profesional.usuario.activo
                and profesional.usuario.usuario.is_active
            ):
                raise ValidationError(
                    "No puedes activar horarios "
                    "de un fisioterapeuta inactivo."
                )

            validar_solapamiento(
                profesional,
                horario,
                horario.pk,
            )

            validar_citas_futuras(
                profesional,
                horario,
                horario.pk,
            )

        except ValidationError as error:

            messages.error(
                request,
                "; ".join(error.messages),
            )

        else:

            horario.save(
                update_fields=["activo"]
            )

            messages.success(
                request,
                "Horario activado."
                if nuevo_estado
                else "Horario desactivado.",
            )

    return redirect(
        "fisioterapeutas:horario_fisioterapeuta",
        fisioterapeuta_id=profesional.pk,
    )
