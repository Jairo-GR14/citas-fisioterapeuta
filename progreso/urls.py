from django.urls import path

from . import views


app_name = "progreso"


urlpatterns = [

    # REGISTRAR PROGRESO
    path(
        "consulta/<int:consulta_id>/registrar/",
        views.registrar_progreso,
        name="registrar_progreso",
    ),

    # EDITAR PROGRESO
    path(
        "consulta/<int:consulta_id>/editar/",
        views.editar_progreso,
        name="editar_progreso",
    ),

    # DETALLE DEL PROGRESO
    path(
        "consulta/<int:consulta_id>/",
        views.detalle_progreso,
        name="detalle_progreso",
    ),

    # PROGRESO VISIBLE PARA EL PACIENTE
    path(
        "paciente/<int:consulta_id>/",
        views.progreso_paciente,
        name="progreso_paciente",
    ),

]