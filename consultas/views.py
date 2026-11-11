from django.shortcuts import render

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from citas.models import Cita
from usuarios.decorators import rol_requerido
from usuarios.models import PerfilUsuario

from .forms import ConsultaForm
from .models import Consulta

def verificar_acceso(request, cita):
    if request.user.is_superuser:
        return

    perfil = request.user.perfil

    if perfil.rol == PerfilUsuario.Rol.ADMINISTRADOR:
        return

    if (
        perfil.rol == PerfilUsuario.Rol.FISIOTERAPEUTA
        and cita.fisioterapeuta.usuario_id == perfil.id
    ):
        return

    raise PermissionDenied(
        "No tienes permiso para acceder a esta consulta."
    )

def obtener_consulta(request, consulta_id):
    consulta = get_object_or_404(
        Consulta.objects.select_related(
            "cita",
            "cita__paciente",
            "cita__fisioterapeuta",
            "cita__motivo",
            "cita__servicio",
        ),
        id=consulta_id,
    )

    verificar_acceso(request, consulta.cita)

    return consulta

@rol_requerido(["ADMINISTRADOR", "FISIOTERAPEUTA"])
def iniciar_consulta(request, cita_id):

    cita = get_object_or_404(
        Cita.objects.select_related(
            "paciente",
            "fisioterapeuta",
            "motivo",
            "servicio",
        ),
        id=cita_id,
    )

    verificar_acceso(request, cita)

    if cita.estado == Cita.Estado.CANCELADA:
        messages.error(
            request,
            "No puedes iniciar una cita cancelada.",
        )

        return redirect(
            "usuarios:redireccion_por_rol"
        )

    if cita.estado == Cita.Estado.FINALIZADA:
        messages.error(
            request,
            "Esta cita ya fue finalizada.",
        )

        return redirect(
            "usuarios:redireccion_por_rol"
        )

    consulta_existente = Consulta.objects.filter(
        cita=cita
    ).first()

    if consulta_existente:
        return redirect(
            "consultas:detalle_consulta",
            consulta_id=consulta_existente.id,
        )

    if request.method == "POST":

        with transaction.atomic():

            consulta, creada = Consulta.objects.get_or_create(
                cita=cita,
                defaults={
                    "fecha_inicio": timezone.now(),
                },
            )

            if not creada and consulta.fecha_inicio is None:
                consulta.fecha_inicio = timezone.now()
                consulta.save()

            cita.estado = Cita.Estado.EN_PROCESO
            cita.save()

        messages.success(
            request,
            "Consulta iniciada correctamente.",
        )

        return redirect(
            "consultas:registrar_valoracion",
            consulta_id=consulta.id,
        )

    return render(
        request,
        "consultas/iniciar_consulta.html",
        {
            "cita": cita,
        },
    )

@rol_requerido(["ADMINISTRADOR", "FISIOTERAPEUTA"])
def registrar_valoracion(request, consulta_id):

    consulta = obtener_consulta(
        request,
        consulta_id,
    )

    if consulta.cita.estado != Cita.Estado.EN_PROCESO:
        messages.error(
            request,
            "Solo puedes modificar una consulta en proceso.",
        )

        return redirect(
            "consultas:detalle_consulta",
            consulta_id=consulta.id,
        )

    if request.method == "POST":

        formulario = ConsultaForm(
            request.POST,
            instance=consulta,
        )

        if formulario.is_valid():

            formulario.save()

            messages.success(
                request,
                "Valoración guardada correctamente.",
            )

            return redirect(
                "consultas:detalle_consulta",
                consulta_id=consulta.id,
            )

    else:

        formulario = ConsultaForm(
            instance=consulta
        )

    return render(
        request,
        "consultas/motivo_consulta.html",
        {
            "formulario": formulario,
            "consulta": consulta,
            "cita": consulta.cita,
        },
    )

@rol_requerido(["ADMINISTRADOR", "FISIOTERAPEUTA"])
def detalle_consulta(request, consulta_id):

    consulta = obtener_consulta(
        request,
        consulta_id,
    )

    return render(
        request,
        "consultas/detalle_consulta.html",
        {
            "consulta": consulta,
            "cita": consulta.cita,
        },
    )

@rol_requerido(["ADMINISTRADOR", "FISIOTERAPEUTA"])
def finalizar_consulta(request, consulta_id):

    consulta = obtener_consulta(
        request,
        consulta_id,
    )

    cita = consulta.cita

    if cita.estado == Cita.Estado.FINALIZADA:

        messages.info(
            request,
            "Esta consulta ya está finalizada.",
        )

        return redirect(
            "consultas:detalle_consulta",
            consulta_id=consulta.id,
        )

    if cita.estado != Cita.Estado.EN_PROCESO:

        messages.error(
            request,
            "La consulta debe estar en proceso para finalizarla.",
        )

        return redirect(
            "consultas:detalle_consulta",
            consulta_id=consulta.id,
        )

    if request.method == "POST":

        if (
            not consulta.valoracion_inicial.strip()
            or not consulta.diagnostico.strip()
        ):

            messages.error(
                request,
                "Debes registrar la valoración inicial "
                "y el diagnóstico antes de finalizar.",
            )

            return redirect(
                "consultas:registrar_valoracion",
                consulta_id=consulta.id,
            )

        with transaction.atomic():

            consulta.fecha_finalizacion = timezone.now()
            consulta.save()

            cita.estado = Cita.Estado.FINALIZADA
            cita.save()

        messages.success(
            request,
            "Consulta finalizada correctamente.",
        )

        return redirect(
            "consultas:detalle_consulta",
            consulta_id=consulta.id,
        )

    return render(
        request,
        "consultas/finalizar_consulta.html",
        {
            "consulta": consulta,
            "cita": cita,
        },
    )
