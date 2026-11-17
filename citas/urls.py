
from django.urls import path

from . import (
    calendario_views,
    disponibilidad_views,
    views,
)


app_name = "citas"


urlpatterns = [
    path(
        "",
        views.agenda,
        name="agenda",
    ),

    path(
        "agendar/",
        views.agendar_cita,
        name="agendar_cita",
    ),

    path(
        "mis-citas/",
        views.mis_citas,
        name="mis_citas",
    ),

    path(
        "calendario/eventos/",
        calendario_views.eventos_calendario,
        name="eventos_calendario",
    ),

    path(
        "horarios/",
        disponibilidad_views.horarios_disponibles,
        name="horarios_disponibles",
    ),

    path(
        "horarios/api/",
        disponibilidad_views.horarios_disponibles_json,
        name="horarios_disponibles_json",
    ),

    path(
        "confirmar/",
        views.confirmar_cita,
        name="confirmar_cita",
    ),

    path(
        "emergencia/",
        views.cita_emergencia,
        name="cita_emergencia",
    ),

    path(
        "<int:cita_id>/",
        views.detalle_cita,
        name="detalle_cita",
    ),

    path(
        "<int:cita_id>/editar/",
        views.editar_cita,
        name="editar_cita",
    ),

    path(
        "<int:cita_id>/cancelar/",
        views.cancelar_cita,
        name="cancelar_cita",
    ),
]
