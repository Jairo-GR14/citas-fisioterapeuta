
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CitaForm, EditarCitaForm
from .models import Cita


# PERMISOS

def obtener_rol(usuario):
    if usuario.is_superuser:
        return "ADMINISTRADOR"

    perfil = getattr(usuario, "perfil", None)

    if perfil is None or not perfil.activo:
        raise PermissionDenied(
            "No tienes un perfil activo."
        )

    return perfil.rol


def obtener_citas_permitidas(usuario):
    """
    Devuelve las citas que el usuario puede consultar.
    """
    citas = Cita.objects.select_related(
        "paciente__usuario__usuario",
        "fisioterapeuta__usuario__usuario",
        "servicio",
        "motivo",
    )

    rol = obtener_rol(usuario)

    if rol in ("ADMINISTRADOR", "RECEPCIONISTA"):
        return citas

    perfil = usuario.perfil

    if rol == "FISIOTERAPEUTA":
        return citas.filter(
            fisioterapeuta__usuario=perfil
        )

    if rol == "PACIENTE":
        return citas.filter(
            paciente__usuario=perfil
        )

    raise PermissionDenied(
        "No tienes permiso para consultar citas."
    )


# AGENDA

@login_required
def agenda(request):
    citas = obtener_citas_permitidas(
        request.user
    ).order_by("fecha", "hora")

    return render(
        request,
        "citas/agenda.html",
        {"citas": citas},
    )


# AGENDAR CITA

@login_required
def agendar_cita(request):
    rol = obtener_rol(request.user)

    if rol not in (
        "ADMINISTRADOR",
        "RECEPCIONISTA",
        "PACIENTE",
    ):
        raise PermissionDenied(
            "No tienes permiso para agendar citas."
        )

    form = CitaForm(
        request.POST if request.method == "POST" else None
    )

    # PACIENTE
    if rol == "PACIENTE":
        perfil = request.user.perfil

        paciente = getattr(
            perfil,
            "paciente",
            None,
        )

        if paciente is None or not paciente.activo:
            raise PermissionDenied(
                "No tienes un registro de paciente activo."
            )

        form.fields["paciente"].queryset = (
            form.fields["paciente"].queryset.filter(
                pk=paciente.pk
            )
        )

        form.fields["paciente"].widget = (
            forms.HiddenInput()
        )

        if request.method == "POST":
            datos = request.POST.copy()
            datos["paciente"] = str(paciente.pk)

            form = CitaForm(datos)

            form.fields["paciente"].queryset = (
                form.fields["paciente"].queryset.filter(
                    pk=paciente.pk
                )
            )

            form.fields["paciente"].widget = (
                forms.HiddenInput()
            )

        else:
            form.initial["paciente"] = paciente.pk

    if request.method == "POST" and form.is_valid():
        cita = form.save(commit=False)

        cita.costo_estimado = (
            cita.servicio.precio_base
        )

        cita.estado = Cita.Estado.PROGRAMADA

        try:
            with transaction.atomic():
                cita.save()

        except IntegrityError:
            form.add_error(
                None,
                "El horario seleccionado ya está ocupado. "
                "Elige otra fecha u hora."
            )

        else:
            messages.success(
                request,
                "La cita se registró correctamente."
            )

            return redirect(
                "citas:detalle_cita",
                cita_id=cita.pk,
            )

    return render(
        request,
        "citas/agendar_cita.html",
        {"form": form},
    )


# MIS CITAS

@login_required
def mis_citas(request):
    citas = obtener_citas_permitidas(
        request.user
    ).order_by("fecha", "hora")

    return render(
        request,
        "citas/mis_citas.html",
        {"citas": citas},
    )


# HORARIOS DISPONIBLES

@login_required
def horarios_disponibles(request):
    # PENDIENTE
    return render(
        request,
        "citas/horarios_disponibles.html",
    )


# CONFIRMAR CITA

@login_required
def confirmar_cita(request):
    rol = obtener_rol(request.user)

    if rol not in (
        "ADMINISTRADOR",
        "RECEPCIONISTA",
    ):
        raise PermissionDenied(
            "No tienes permiso para confirmar citas."
        )

    if request.method == "POST":
        cita_id = request.POST.get("cita_id")

        if not cita_id:
            messages.error(
                request,
                "No se seleccionó ninguna cita."
            )
            return redirect("citas:confirmar_cita")

        with transaction.atomic():
            cita = get_object_or_404(
                Cita.objects.select_for_update(),
                pk=cita_id,
                estado=Cita.Estado.PROGRAMADA,
            )

            cita.estado = Cita.Estado.CONFIRMADA

            cita.save(
                update_fields=[
                    "estado",
                    "fecha_actualizacion",
                ]
            )

        messages.success(
            request,
            "La cita se confirmó correctamente."
        )

        return redirect("citas:confirmar_cita")

    citas = Cita.objects.filter(
        estado=Cita.Estado.PROGRAMADA
    ).select_related(
        "paciente__usuario__usuario",
        "fisioterapeuta__usuario__usuario",
        "servicio",
        "motivo",
    ).order_by("fecha", "hora")

    return render(
        request,
        "citas/confirmar_cita.html",
        {"citas": citas},
    )


# CITA DE EMERGENCIA

@login_required
def cita_emergencia(request):
    # PENDIENTE
    return render(
        request,
        "citas/cita_emergencia.html",
    )


# DETALLE DE CITA

@login_required
def detalle_cita(request, cita_id):
    cita = get_object_or_404(
        obtener_citas_permitidas(request.user),
        pk=cita_id,
    )

    return render(
        request,
        "citas/detalle_cita.html",
        {"cita": cita},
    )


# EDITAR CITA

@login_required
def editar_cita(request, cita_id):
    rol = obtener_rol(request.user)

    if rol not in (
        "ADMINISTRADOR",
        "RECEPCIONISTA",
        "PACIENTE",
    ):
        raise PermissionDenied(
            "No tienes permiso para editar citas."
        )

    cita = get_object_or_404(
        obtener_citas_permitidas(request.user),
        pk=cita_id,
    )

    if cita.estado not in (
        Cita.Estado.PROGRAMADA,
        Cita.Estado.CONFIRMADA,
    ):
        raise PermissionDenied(
            "Esta cita ya no se puede modificar."
        )

    if request.method == "POST":
        form = EditarCitaForm(
            request.POST,
            instance=cita,
        )

        if form.is_valid():
            cita_editada = form.save(commit=False)

            cita_editada.costo_estimado = (
                cita_editada.servicio.precio_base
            )

            cita_editada.estado = (
                Cita.Estado.PROGRAMADA
            )

            try:
                with transaction.atomic():
                    cita_editada.save()

            except IntegrityError:
                form.add_error(
                    None,
                    "El horario seleccionado ya está "
                    "ocupado. Selecciona otro."
                )

            else:
                messages.success(
                    request,
                    "La cita se actualizó correctamente."
                )

                return redirect(
                    "citas:detalle_cita",
                    cita_id=cita.pk,
                )

    else:
        form = EditarCitaForm(instance=cita)

    return render(
        request,
        "citas/editar_cita.html",
        {
            "form": form,
            "cita": cita,
        },
    )


# CANCELAR CITA

@login_required
def cancelar_cita(request, cita_id):
    cita = get_object_or_404(
        obtener_citas_permitidas(request.user),
        pk=cita_id,
    )

    # PENDIENTE
    return render(
        request,
        "citas/cancelar_cita.html",
        {"cita": cita},
    )
