from django.urls import path

from . import views


app_name = "consultas"


urlpatterns = [

    path(
        "iniciar/<int:cita_id>/",
        views.iniciar_consulta,
        name="iniciar_consulta",
    ),

    path(
        "<int:consulta_id>/valoracion/",
        views.registrar_valoracion,
        name="registrar_valoracion",
    ),

    path(
        "<int:consulta_id>/",
        views.detalle_consulta,
        name="detalle_consulta",
    ),

    path(
        "<int:consulta_id>/finalizar/",
        views.finalizar_consulta,
        name="finalizar_consulta",
    ),

]