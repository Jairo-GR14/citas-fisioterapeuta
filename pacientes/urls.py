
from django.urls import path
from . import views


app_name = "pacientes"


urlpatterns = [
    path(
        "",
        views.lista_pacientes,
        name="lista_pacientes",
    ),

    path(
        "registrar/",
        views.registrar_paciente,
        name="registrar_paciente",
    ),

    path(
        "<int:paciente_id>/",
        views.detalle_paciente,
        name="detalle_paciente",
    ),

    path(
        "<int:paciente_id>/editar/",
        views.editar_paciente,
        name="editar_paciente",
    ),

    path(
        "<int:paciente_id>/historial/",
        views.historial_paciente,
        name="historial_paciente",
    ),

    path(
        "<int:paciente_id>/eliminar/",
        views.eliminar_paciente,
        name="eliminar_paciente",
    ),
]
