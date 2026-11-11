from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from citas.models import Cita
from consultas.views import obtener_consulta, verificar_acceso
from usuarios.decorators import rol_requerido

from .forms import RecetaForm
from .models import Receta


# =========================================================
# OBTENER RECETA Y COMPROBAR PERMISOS
# =========================================================

def obtener_receta(request, receta_id):

    receta = get_object_or_404(
        Receta.objects.select_related(
            "consulta",
            "consulta__cita",
            "consulta__cita__paciente",
            "consulta__cita__fisioterapeuta",
        ),
        id=receta_id,
    )

    # El administrador o fisioterapeuta debe tener
    # permiso para consultar la cita asociada.
    verificar_acceso(request, receta.consulta.cita)

    return receta


# =========================================================
# REGISTRAR RECETA
# =========================================================

@rol_requerido(["ADMINISTRADOR", "FISIOTERAPEUTA"])
def registrar_receta(request, consulta_id):

    consulta = obtener_consulta(request, consulta_id)
    cita = consulta.cita

    # Solo permitir registros en consultas en proceso.
    if cita.estado != Cita.Estado.EN_PROCESO:

        messages.error(
            request,
            "Solo puedes registrar recetas en consultas "
            "que estén en proceso."
        )

        return redirect(
            "consultas:detalle_consulta",
            consulta_id=consulta.id,
        )

    if request.method == "POST":

        formulario = RecetaForm(request.POST)

        if formulario.is_valid():

            receta = formulario.save(commit=False)

            # Asociar automáticamente la receta
            # con la consulta correspondiente.
            receta.consulta = consulta

            receta.save()

            messages.success(
                request,
                "Receta registrada correctamente."
            )

            return redirect(
                "recetas:detalle_receta",
                receta_id=receta.id,
            )

    else:
        formulario = RecetaForm()

    return render(
        request,
        "recetas/registrar_receta.html",
        {
            "formulario": formulario,
            "consulta": consulta,
            "cita": cita,
        },
    )


# =========================================================
# LISTAR RECETAS DE UNA CONSULTA
# =========================================================

@rol_requerido(["ADMINISTRADOR", "FISIOTERAPEUTA"])
def lista_recetas(request, consulta_id):

    consulta = obtener_consulta(request, consulta_id)
    cita = consulta.cita

    recetas = (
        Receta.objects
        .filter(consulta=consulta)
        .order_by("-id")
    )

    return render(
        request,
        "recetas/lista_recetas.html",
        {
            "recetas": recetas,
            "consulta": consulta,
            "cita": cita,
        },
    )


# =========================================================
# VER DETALLE DE UNA RECETA
# =========================================================

@rol_requerido(["ADMINISTRADOR", "FISIOTERAPEUTA"])
def detalle_receta(request, receta_id):

    receta = obtener_receta(request, receta_id)

    consulta = receta.consulta
    cita = consulta.cita

    return render(
        request,
        "recetas/detalle_receta.html",
        {
            "receta": receta,
            "consulta": consulta,
            "cita": cita,
        },
    )


# =========================================================
# EDITAR RECETA
# =========================================================

@rol_requerido(["ADMINISTRADOR", "FISIOTERAPEUTA"])
def editar_receta(request, receta_id):

    receta = obtener_receta(request, receta_id)

    consulta = receta.consulta
    cita = consulta.cita

    # Evitar modificaciones si la consulta
    # ya fue finalizada o no está en proceso.
    if cita.estado != Cita.Estado.EN_PROCESO:

        messages.error(
            request,
            "No puedes editar una receta si la consulta "
            "ya no está en proceso."
        )

        return redirect(
            "recetas:detalle_receta",
            receta_id=receta.id,
        )

    if request.method == "POST":

        formulario = RecetaForm(
            request.POST,
            instance=receta,
        )

        if formulario.is_valid():

            formulario.save()

            messages.success(
                request,
                "Receta actualizada correctamente."
            )

            return redirect(
                "recetas:detalle_receta",
                receta_id=receta.id,
            )

    else:

        # Cargar los datos existentes de la receta.
        formulario = RecetaForm(instance=receta)

    return render(
        request,
        "recetas/editar_receta.html",
        {
            "formulario": formulario,
            "receta": receta,
            "consulta": consulta,
            "cita": cita,
        },
    )


# =========================================================
# VER RECETA COMO PACIENTE
# =========================================================

@rol_requerido(["PACIENTE"])
def receta_paciente(request, receta_id):

    # Filtrar por el usuario autenticado.
    # Un paciente no puede consultar recetas ajenas.
    receta = get_object_or_404(
        Receta.objects.select_related(
            "consulta",
            "consulta__cita",
            "consulta__cita__paciente",
            "consulta__cita__fisioterapeuta",
            "consulta__cita__servicio",
        ),
        id=receta_id,
        consulta__cita__paciente__usuario__usuario=request.user,
    )

    consulta = receta.consulta
    cita = consulta.cita

    return render(
        request,
        "recetas/receta_paciente.html",
        {
            "receta": receta,
            "consulta": consulta,
            "cita": cita,
        },
    )