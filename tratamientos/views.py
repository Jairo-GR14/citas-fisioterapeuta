from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from citas.models import Cita
from consultas.views import obtener_consulta, verificar_acceso
from usuarios.decorators import rol_requerido

from .forms import TratamientoForm
from .models import Tratamiento


# =========================================================
# OBTENER TRATAMIENTO Y VERIFICAR PERMISOS
# =========================================================

def obtener_tratamiento(request, tratamiento_id):

    tratamiento = get_object_or_404(
        Tratamiento.objects.select_related(
            "consulta",
            "consulta__cita",
            "consulta__cita__paciente",
            "consulta__cita__fisioterapeuta",
        ),
        id=tratamiento_id,
    )

    verificar_acceso(
        request,
        tratamiento.consulta.cita,
    )

    return tratamiento


# =========================================================
# REGISTRAR TRATAMIENTO
# =========================================================

@rol_requerido(["ADMINISTRADOR", "FISIOTERAPEUTA"])
def registrar_tratamiento(request, consulta_id):

    consulta = obtener_consulta(
        request,
        consulta_id,
    )

    if consulta.cita.estado != Cita.Estado.EN_PROCESO:

        messages.error(
            request,
            "Solo puedes registrar tratamientos "
            "en consultas que estén en proceso.",
        )

        return redirect(
            "consultas:detalle_consulta",
            consulta_id=consulta.id,
        )

    if request.method == "POST":

        formulario = TratamientoForm(
            request.POST
        )

        if formulario.is_valid():

            tratamiento = formulario.save(
                commit=False
            )

            tratamiento.consulta = consulta

            tratamiento.save()

            messages.success(
                request,
                "Tratamiento registrado correctamente.",
            )

            return redirect(
                "tratamientos:detalle_tratamiento",
                tratamiento_id=tratamiento.id,
            )

    else:

        formulario = TratamientoForm()

    return render(
        request,
        "tratamientos/registrar_tratamiento.html",
        {
            "formulario": formulario,
            "consulta": consulta,
            "cita": consulta.cita,
        },
    )


# =========================================================
# DETALLE DEL TRATAMIENTO
# =========================================================

@rol_requerido(["ADMINISTRADOR", "FISIOTERAPEUTA"])
def detalle_tratamiento(request, tratamiento_id):

    tratamiento = obtener_tratamiento(
        request,
        tratamiento_id,
    )

    consulta = tratamiento.consulta

    return render(
        request,
        "tratamientos/detalle_tratamiento.html",
        {
            "tratamiento": tratamiento,
            "consulta": consulta,
            "cita": consulta.cita,
        },
    )


# =========================================================
# EDITAR TRATAMIENTO
# =========================================================

@rol_requerido(["ADMINISTRADOR", "FISIOTERAPEUTA"])
def editar_tratamiento(request, tratamiento_id):

    tratamiento = obtener_tratamiento(
        request,
        tratamiento_id,
    )

    consulta = tratamiento.consulta

    if consulta.cita.estado != Cita.Estado.EN_PROCESO:

        messages.error(
            request,
            "No puedes modificar tratamientos "
            "de una consulta que ya no está en proceso.",
        )

        return redirect(
            "tratamientos:detalle_tratamiento",
            tratamiento_id=tratamiento.id,
        )

    if request.method == "POST":

        formulario = TratamientoForm(
            request.POST,
            instance=tratamiento,
        )

        if formulario.is_valid():

            formulario.save()

            messages.success(
                request,
                "Tratamiento actualizado correctamente.",
            )

            return redirect(
                "tratamientos:detalle_tratamiento",
                tratamiento_id=tratamiento.id,
            )

    else:

        formulario = TratamientoForm(
            instance=tratamiento
        )

    return render(
        request,
        "tratamientos/editar_tratamiento.html",
        {
            "formulario": formulario,
            "tratamiento": tratamiento,
            "consulta": consulta,
            "cita": consulta.cita,
        },
    )


# =========================================================
# HISTORIAL DE TRATAMIENTOS
# =========================================================

@rol_requerido(["ADMINISTRADOR", "FISIOTERAPEUTA"])
def historial_tratamientos(request, consulta_id):

    consulta = obtener_consulta(
        request,
        consulta_id,
    )

    tratamientos = (
        Tratamiento.objects.filter(
            consulta=consulta
        )
        .order_by(
            "-fecha_creacion",
            "-id",
        )
    )

    return render(
        request,
        "tratamientos/historial_tratamientos.html",
        {
            "tratamientos": tratamientos,
            "consulta": consulta,
            "cita": consulta.cita,
        },
    )