from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from citas.models import Cita
from consultas.views import obtener_consulta
from usuarios.decorators import rol_requerido

from .forms import ProgresoForm
from .models import Progreso


# =========================================================
# REGISTRAR PROGRESO
# =========================================================

@rol_requerido(["ADMINISTRADOR", "FISIOTERAPEUTA"])
def registrar_progreso(request, consulta_id):

    consulta = obtener_consulta(
        request,
        consulta_id,
    )

    # Comprobar que la consulta esté en proceso
    if consulta.cita.estado != Cita.Estado.EN_PROCESO:

        messages.error(
            request,
            "Solo puedes registrar progreso en "
            "consultas que estén en proceso.",
        )

        return redirect(
            "consultas:detalle_consulta",
            consulta_id=consulta.id,
        )

    # Evitar crear dos registros para la misma consulta
    if Progreso.objects.filter(consulta=consulta).exists():

        messages.info(
            request,
            "Esta consulta ya tiene un registro de progreso.",
        )

        return redirect(
            "progreso:editar_progreso",
            consulta_id=consulta.id,
        )

    if request.method == "POST":

        formulario = ProgresoForm(request.POST)

        if formulario.is_valid():

            progreso = formulario.save(commit=False)

            progreso.consulta = consulta

            progreso.save()

            messages.success(
                request,
                "Progreso registrado correctamente.",
            )

            return redirect(
                "progreso:detalle_progreso",
                consulta_id=consulta.id,
            )

    else:

        formulario = ProgresoForm()

    return render(
        request,
        "progreso/registrar_progreso.html",
        {
            "formulario": formulario,
            "consulta": consulta,
            "cita": consulta.cita,
            "es_edicion": False,
        },
    )


# =========================================================
# EDITAR PROGRESO
# =========================================================

@rol_requerido(["ADMINISTRADOR", "FISIOTERAPEUTA"])
def editar_progreso(request, consulta_id):

    consulta = obtener_consulta(
        request,
        consulta_id,
    )

    progreso = get_object_or_404(
        Progreso,
        consulta=consulta,
    )

    # No permitir cambios en consultas finalizadas
    if consulta.cita.estado != Cita.Estado.EN_PROCESO:

        messages.error(
            request,
            "No puedes modificar el progreso de "
            "una consulta que ya no está en proceso.",
        )

        return redirect(
            "progreso:detalle_progreso",
            consulta_id=consulta.id,
        )

    if request.method == "POST":

        formulario = ProgresoForm(
            request.POST,
            instance=progreso,
        )

        if formulario.is_valid():

            formulario.save()

            messages.success(
                request,
                "Progreso actualizado correctamente.",
            )

            return redirect(
                "progreso:detalle_progreso",
                consulta_id=consulta.id,
            )

    else:

        formulario = ProgresoForm(
            instance=progreso,
        )

    return render(
        request,
        "progreso/registrar_progreso.html",
        {
            "formulario": formulario,
            "progreso": progreso,
            "consulta": consulta,
            "cita": consulta.cita,
            "es_edicion": True,
        },
    )


# =========================================================
# DETALLE DEL PROGRESO
# =========================================================

@rol_requerido(["ADMINISTRADOR", "FISIOTERAPEUTA"])
def detalle_progreso(request, consulta_id):

    consulta = obtener_consulta(
        request,
        consulta_id,
    )

    progreso = get_object_or_404(
        Progreso,
        consulta=consulta,
    )

    return render(
        request,
        "progreso/detalle_progreso.html",
        {
            "progreso": progreso,
            "consulta": consulta,
            "cita": consulta.cita,
        },
    )


# =========================================================
# PROGRESO VISIBLE PARA EL PACIENTE
# =========================================================

@rol_requerido(["PACIENTE"])
def progreso_paciente(request, consulta_id):

    # El paciente únicamente puede consultar su propio progreso
    progreso = get_object_or_404(
        Progreso.objects.select_related(
            "consulta",
            "consulta__cita",
            "consulta__cita__paciente",
            "consulta__cita__fisioterapeuta",
        ),
        consulta_id=consulta_id,
        consulta__cita__paciente__usuario__usuario=request.user,
    )

    consulta = progreso.consulta

    return render(
        request,
        "progreso/progreso_paciente.html",
        {
            "progreso": progreso,
            "consulta": consulta,
            "cita": consulta.cita,
        },
    )