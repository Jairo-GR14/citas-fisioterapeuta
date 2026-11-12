
from django.urls import path

from . import views, horarios_views


app_name = "fisioterapeutas"


urlpatterns = [
    path(
        "",
        views.lista_fisioterapeutas,
        name="lista_fisioterapeutas",
    ),

    path(
        "registrar/",
        views.registrar_fisioterapeuta,
        name="registrar_fisioterapeuta",
    ),

    path(
        "<int:fisioterapeuta_id>/",
        views.detalle_fisioterapeuta,
        name="detalle_fisioterapeuta",
    ),

    path(
        "<int:fisioterapeuta_id>/editar/",
        views.editar_fisioterapeuta,
        name="editar_fisioterapeuta",
    ),

    path(
        "<int:fisioterapeuta_id>/horario/",
        horarios_views.horario_fisioterapeuta,
        name="horario_fisioterapeuta",
    ),

    path(
        "<int:fisioterapeuta_id>/horario/nuevo/",
        horarios_views.registrar_horario,
        name="registrar_horario",
    ),

    path(
        "horarios/<int:horario_id>/editar/",
        horarios_views.editar_horario,
        name="editar_horario",
    ),

    path(
        "horarios/<int:horario_id>/estado/",
        horarios_views.cambiar_estado_horario,
        name="cambiar_estado_horario",
    ),

    path(
        "<int:fisioterapeuta_id>/estado/",
        views.cambiar_estado_fisioterapeuta,
        name="cambiar_estado_fisioterapeuta",
    ),
]
