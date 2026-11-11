from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time

from fisioterapeutas.models import Fisioterapeuta, HorarioDisponible

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