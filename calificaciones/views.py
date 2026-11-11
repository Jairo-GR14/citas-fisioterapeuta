from django.contrib import messages
from django.db.models import Avg
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from citas.models import Cita
from usuarios.decorators import rol_requerido
from usuarios.models import PerfilUsuario

from .forms import CalificacionForm
from .models import Calificacion


# =========================================================
# REGISTRAR CALIFICACIÓN
# =========================================================

@rol_requerido(["PACIENTE"])
def registrar_calificacion(request, cita_id):

    # Buscar únicamente una cita del paciente autenticado.
    cita = get_object_or_404(
        Cita.objects.select_related(
            "paciente",
            "fisioterapeuta",
            "fisioterapeuta__usuario",
            "fisioterapeuta__usuario__usuario",
            "servicio",
        ),
        id=cita_id,
        paciente__usuario__usuario=request.user,
    )

    # Solo se permite calificar citas finalizadas.
    if cita.estado != Cita.Estado.FINALIZADA:

        messages.error(
            request,
            "Solo puedes calificar citas que hayan finalizado.",
        )

        return redirect(
            "usuarios:redireccion_por_rol"
        )

    # Comprobar si ya existe una calificación para esta cita.
    calificacion_existente = Calificacion.objects.filter(
        cita=cita
    ).first()

    if calificacion_existente:

        messages.info(
            request,
            "Ya registraste una calificación para esta cita.",
        )

        return redirect(
            "calificaciones:detalle_calificacion",
            calificacion_id=calificacion_existente.id,
        )

    # Procesar el formulario.
    if request.method == "POST":

        formulario = CalificacionForm(request.POST)

        if formulario.is_valid():

            # La cita se asigna automáticamente.
            # No se permite seleccionar una cita diferente.
            calificacion, creada = Calificacion.objects.get_or_create(
                cita=cita,
                defaults={
                    "puntuacion": formulario.cleaned_data["puntuacion"],
                    "comentario": formulario.cleaned_data["comentario"],
                },
            )

            if creada:

                messages.success(
                    request,
                    "Tu calificación se registró correctamente.",
                )

            else:

                messages.info(
                    request,
                    "Esta cita ya tiene una calificación.",
                )

            return redirect(
                "calificaciones:detalle_calificacion",
                calificacion_id=calificacion.id,
            )

    else:

        formulario = CalificacionForm()

    # Utilizamos el HTML que ya existe en el proyecto.
    return render(
        request,
        "calificaciones/calificar_cita.html",
        {
            "formulario": formulario,
            "cita": cita,
        },
    )


# =========================================================
# DETALLE DE UNA CALIFICACIÓN
# =========================================================

@rol_requerido(["PACIENTE", "ADMINISTRADOR"])
def detalle_calificacion(request, calificacion_id):

    calificacion = get_object_or_404(
        Calificacion.objects.select_related(
            "cita",
            "cita__paciente",
            "cita__paciente__usuario",
            "cita__paciente__usuario__usuario",
            "cita__fisioterapeuta",
            "cita__fisioterapeuta__usuario",
            "cita__fisioterapeuta__usuario__usuario",
            "cita__servicio",
        ),
        id=calificacion_id,
    )

    cita = calificacion.cita

    # Comprobar si el usuario es administrador.
    es_administrador = (
        request.user.is_superuser
        or request.user.perfil.rol
        == PerfilUsuario.Rol.ADMINISTRADOR
    )

    # El paciente solo puede ver sus propias calificaciones.
    if not es_administrador:

        if cita.paciente.usuario.usuario_id != request.user.id:

            raise Http404(
                "Calificación no encontrada."
            )

    return render(
        request,
        "calificaciones/detalle_calificacion.html",
        {
            "calificacion": calificacion,
            "cita": cita,
        },
    )


# =========================================================
# MIS CALIFICACIONES - PACIENTE
# =========================================================

@rol_requerido(["PACIENTE"])
def mis_calificaciones(request):

    # Mostrar únicamente las calificaciones del paciente.
    calificaciones = (
        Calificacion.objects
        .filter(
            cita__paciente__usuario__usuario=request.user
        )
        .select_related(
            "cita",
            "cita__fisioterapeuta",
            "cita__fisioterapeuta__usuario",
            "cita__fisioterapeuta__usuario__usuario",
            "cita__servicio",
        )
        .order_by("-id")
    )

    return render(
        request,
        "calificaciones/mis_calificaciones.html",
        {
            "calificaciones": calificaciones,
        },
    )


# =========================================================
# LISTA DE CALIFICACIONES - ADMINISTRADOR
# =========================================================

@rol_requerido(["ADMINISTRADOR"])
def lista_calificaciones(request):

    # El administrador puede consultar todas las calificaciones.
    calificaciones = (
        Calificacion.objects
        .select_related(
            "cita",
            "cita__paciente",
            "cita__paciente__usuario",
            "cita__paciente__usuario__usuario",
            "cita__fisioterapeuta",
            "cita__fisioterapeuta__usuario",
            "cita__fisioterapeuta__usuario__usuario",
            "cita__servicio",
        )
        .order_by("-id")
    )

    # Total de calificaciones registradas.
    total_calificaciones = calificaciones.count()

    # Calcular el promedio general.
    promedio_calificaciones = calificaciones.aggregate(
        promedio=Avg("puntuacion")
    )["promedio"]

    return render(
        request,
        "calificaciones/lista_calificaciones.html",
        {
            "calificaciones": calificaciones,
            "total_calificaciones": total_calificaciones,
            "promedio_calificaciones": promedio_calificaciones,
        },
    )