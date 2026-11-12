
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Notificacion


# VALIDAR PERFIL

def perfil_activo(request):

    perfil = getattr(request.user, "perfil", None)

    if (
        not request.user.is_active
        or perfil is None
        or not perfil.activo
    ):
        raise PermissionDenied(
            "Necesitas un perfil activo para consultar "
            "tus notificaciones."
        )

    return perfil


# MOSTRAR NOTIFICACIONES

@login_required
def lista_notificaciones(request):

    perfil = perfil_activo(request)

    propias = Notificacion.objects.filter(
        usuario=perfil
    )

    return render(
        request,
        "notificaciones/notificaciones.html",
        {
            "notificaciones": propias.order_by(
                "-fecha_creacion"
            )[:100],

            "sin_leer": propias.filter(
                leida=False
            ).count(),
        },
    )


# DETALLE DE NOTIFICACIÓN

@login_required
def detalle_notificacion(request, notificacion_id):

    perfil = perfil_activo(request)

    notificacion = get_object_or_404(
        Notificacion,
        pk=notificacion_id,
        usuario=perfil,
    )

    return render(
        request,
        "notificaciones/detalle_notificacion.html",
        {
            "notificacion": notificacion,
        },
    )


# MARCAR UNA NOTIFICACIÓN COMO LEÍDA

@login_required
@require_POST
def marcar_leida(request, notificacion_id):

    perfil = perfil_activo(request)

    notificacion = get_object_or_404(
        Notificacion,
        pk=notificacion_id,
        usuario=perfil,
    )

    if not notificacion.leida:

        Notificacion.objects.filter(
            pk=notificacion.pk,
            leida=False,
        ).update(
            leida=True,
            fecha_lectura=timezone.now(),
        )

    return redirect(
        "notificaciones:detalle",
        notificacion_id=notificacion.pk,
    )


# MARCAR TODAS COMO LEÍDAS

@login_required
@require_POST
def marcar_todas_leidas(request):

    perfil = perfil_activo(request)

    Notificacion.objects.filter(
        usuario=perfil,
        leida=False,
    ).update(
        leida=True,
        fecha_lectura=timezone.now(),
    )

    return redirect(
        "notificaciones:lista"
    )
