from django.urls import path

from . import views


app_name = "calificaciones"


urlpatterns = [

    # ==========================================
    # REGISTRAR CALIFICACIÓN
    # ==========================================
    path(
        "cita/<int:cita_id>/calificar/",
        views.registrar_calificacion,
        name="registrar_calificacion",
    ),

    # ==========================================
    # DETALLE DE CALIFICACIÓN
    # ==========================================
    path(
        "<int:calificacion_id>/",
        views.detalle_calificacion,
        name="detalle_calificacion",
    ),

    # ==========================================
    # MIS CALIFICACIONES - PACIENTE
    # ==========================================
    path(
        "mis-calificaciones/",
        views.mis_calificaciones,
        name="mis_calificaciones",
    ),

    # ==========================================
    # TODAS LAS CALIFICACIONES - ADMINISTRADOR
    # ==========================================
    path(
        "administracion/",
        views.lista_calificaciones,
        name="lista_calificaciones",
    ),

]