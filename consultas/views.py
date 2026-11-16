
from datetime import datetime

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from citas.models import Cita
from usuarios.decorators import rol_requerido
from usuarios.models import PerfilUsuario

from .forms import ConsultaForm, FinalizarConsultaForm
from .models import Consulta


# =========================================================
# VERIFICAR ACCESO
# =========================================================

def verificar_acceso(request, cita):

    if request.user.is_superuser:
        return

    perfil = getattr(
        request.user,
        "perfil",
        None,
    )

    if (
        perfil is None
        or not perfil.activo
        or not request.user.is_active
    ):
        raise PermissionDenied(
            "Tu cuenta no tiene un perfil activo."
        )

    if perfil.rol == PerfilUsuario.Rol.ADMINISTRADOR:
        return

    if (
        perfil.rol == PerfilUsuario.Rol.FISIOTERAPEUTA
        and cita.fisioterapeuta.usuario_id == perfil.pk
    ):
        return

    raise PermissionDenied(
        "No tienes permiso para acceder a esta consulta."
    )


# =========================================================
# OBTENER CONSULTA
# =========================================================

def obtener_consulta(request, consulta_id):

    consulta = get_object_or_404(
        Consulta.objects.select_related(
            "cita",
            "cita__paciente",
            "cita__fisioterapeuta",
            "cita__motivo",
            "cita__servicio",
        ),
        pk=consulta_id,
    )

    verificar_acceso(
        request,
        consulta.cita,
    )

    return consulta


# =========================================================
# COMPROBAR HORARIO PARA INICIAR
# =========================================================

def puede_iniciar_ahora(cita):

    if cita.estado != Cita.Estado.CONFIRMADA:
        return (
            False,
            "Solo puedes iniciar una cita confirmada.",
        )

    momento_cita = timezone.make_aware(
        datetime.combine(
            cita.fecha,
            cita.hora,
        ),
        timezone.get_current_timezone(),
    )

    if timezone.now() < momento_cita:
        return (
            False,
            "Todavía no puedes iniciar esta consulta. "
            "Debes esperar a la fecha y hora programadas.",
        )

    return True, ""


# =========================================================
# COMPROBAR DATOS CLÍNICOS OBLIGATORIOS
# =========================================================

def valoracion_completa(consulta):

    valoracion = (
        consulta.valoracion_inicial or ""
    ).strip()

    diagnostico = (
        consulta.diagnostico or ""
    ).strip()

    return bool(
        valoracion and diagnostico
    )


# =========================================================
# INICIAR CONSULTA
# =========================================================

@rol_requerido(["ADMINISTRADOR", "FISIOTERAPEUTA"])
def iniciar_consulta(request, cita_id):

    cita = get_object_or_404(
        Cita.objects.select_related(
            "paciente",
            "fisioterapeuta",
            "motivo",
            "servicio",
        ),
        pk=cita_id,
    )

    verificar_acceso(
        request,
        cita,
    )

    # Evitar crear dos consultas para la misma cita.
    consulta_existente = Consulta.objects.filter(
        cita=cita
    ).first()

    if consulta_existente:
        return redirect(
            "consultas:detalle_consulta",
            consulta_id=consulta_existente.pk,
        )

    permitido, mensaje = puede_iniciar_ahora(cita)

    if not permitido:
        messages.warning(
            request,
            mensaje,
        )

        return redirect(
            "citas:detalle_cita",
            cita_id=cita.pk,
        )

    if request.method == "POST":

        with transaction.atomic():

            cita = get_object_or_404(
                Cita.objects.select_for_update(),
                pk=cita.pk,
            )

            verificar_acceso(
                request,
                cita,
            )

            consulta_existente = Consulta.objects.filter(
                cita=cita
            ).first()

            if consulta_existente:
                return redirect(
                    "consultas:detalle_consulta",
                    consulta_id=consulta_existente.pk,
                )

            # Validar nuevamente antes de guardar.
            permitido, mensaje = puede_iniciar_ahora(cita)

            if not permitido:
                messages.warning(
                    request,
                    mensaje,
                )

                return redirect(
                    "citas:detalle_cita",
                    cita_id=cita.pk,
                )

            consulta, creada = Consulta.objects.get_or_create(
                cita=cita,
                defaults={
                    "fecha_inicio": timezone.now(),
                },
            )

            if not creada:
                return redirect(
                    "consultas:detalle_consulta",
                    consulta_id=consulta.pk,
                )

            cita.estado = Cita.Estado.EN_PROCESO

            cita.save(
                update_fields=[
                    "estado",
                    "fecha_actualizacion",
                ]
            )

        messages.success(
            request,
            "Consulta iniciada correctamente.",
        )

        return redirect(
            "consultas:registrar_valoracion",
            consulta_id=consulta.pk,
        )

    return render(
        request,
        "consultas/iniciar_consulta.html",
        {
            "cita": cita,
        },
    )


# =========================================================
# REGISTRAR VALORACIÓN
# =========================================================

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
            consulta_id=consulta.pk,
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
                consulta_id=consulta.pk,
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


# =========================================================
# DETALLE DE CONSULTA
# =========================================================

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


# =========================================================
# FINALIZAR CONSULTA Y REGISTRAR COSTO FINAL
# =========================================================

@rol_requerido(["ADMINISTRADOR", "FISIOTERAPEUTA"])
def finalizar_consulta(request, consulta_id):

    consulta = obtener_consulta(
        request,
        consulta_id,
    )

    cita = consulta.cita

    # No permitir finalizar dos veces.
    if cita.estado == Cita.Estado.FINALIZADA:

        messages.info(
            request,
            "Esta consulta ya está finalizada.",
        )

        return redirect(
            "consultas:detalle_consulta",
            consulta_id=consulta.pk,
        )

    # La consulta debe estar en proceso.
    if cita.estado != Cita.Estado.EN_PROCESO:

        messages.error(
            request,
            "La consulta debe estar en proceso para finalizarla.",
        )

        return redirect(
            "consultas:detalle_consulta",
            consulta_id=consulta.pk,
        )

    puede_finalizar = valoracion_completa(
        consulta
    )

    # =====================================================
    # PROCESAR FINALIZACIÓN
    # =====================================================

    if request.method == "POST":

        formulario_cierre = FinalizarConsultaForm(
            request.POST
        )

        if not puede_finalizar:

            messages.error(
                request,
                "Debes registrar la valoración inicial "
                "y el diagnóstico antes de finalizar.",
            )

            return redirect(
                "consultas:registrar_valoracion",
                consulta_id=consulta.pk,
            )

        if formulario_cierre.is_valid():

            costo_final = formulario_cierre.cleaned_data[
                "costo_final"
            ]

            with transaction.atomic():

                # Bloquear la cita para evitar cierres simultáneos.
                cita_actual = get_object_or_404(
                    Cita.objects.select_for_update(),
                    pk=cita.pk,
                )

                # Consultar los datos clínicos más recientes.
                consulta_actual = get_object_or_404(
                    Consulta.objects.select_for_update(),
                    pk=consulta.pk,
                    cita=cita_actual,
                )

                verificar_acceso(
                    request,
                    cita_actual,
                )

                # Volver a comprobar el estado dentro
                # de la transacción.
                if cita_actual.estado != Cita.Estado.EN_PROCESO:

                    messages.error(
                        request,
                        "La cita ya no está disponible "
                        "para finalizar.",
                    )

                    return redirect(
                        "consultas:detalle_consulta",
                        consulta_id=consulta_actual.pk,
                    )

                # Evitar finalizar sin valoración
                # o diagnóstico registrados.
                if not valoracion_completa(consulta_actual):

                    messages.error(
                        request,
                        "Faltan la valoración inicial "
                        "o el diagnóstico.",
                    )

                    return redirect(
                        "consultas:registrar_valoracion",
                        consulta_id=consulta_actual.pk,
                    )

                # Guardar fecha de cierre.
                consulta_actual.fecha_finalizacion = (
                    timezone.now()
                )

                consulta_actual.save(
                    update_fields=[
                        "fecha_finalizacion",
                        "fecha_actualizacion",
                    ]
                )

                # Guardar costo final y estado
                # de la cita en una misma operación.
                cita_actual.costo_final = costo_final
                cita_actual.estado = Cita.Estado.FINALIZADA

                cita_actual.save(
                    update_fields=[
                        "costo_final",
                        "estado",
                        "fecha_actualizacion",
                    ]
                )

            messages.success(
                request,
                "Consulta finalizada correctamente. "
                "El costo final quedó registrado.",
            )

            return redirect(
                "consultas:detalle_consulta",
                consulta_id=consulta.pk,
            )

    # =====================================================
    # MOSTRAR FORMULARIO DE FINALIZACIÓN
    # =====================================================

    else:

        # No copiar automáticamente el estimado:
        # el profesional debe registrar el importe real.
        inicial = {}

        if cita.costo_final is not None:
            inicial["costo_final"] = cita.costo_final

        formulario_cierre = FinalizarConsultaForm(
            initial=inicial
        )

    return render(
        request,
        "consultas/finalizar_consulta.html",
        {
            "consulta": consulta,
            "cita": cita,
            "formulario_cierre": formulario_cierre,
            "puede_finalizar": puede_finalizar,
        },
    )
