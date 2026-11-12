
from django.urls import path
from . import views


app_name = "notificaciones"


urlpatterns = [
    path(
        "",
        views.lista_notificaciones,
        name="lista",
    ),

    path(
        "<int:notificacion_id>/",
        views.detalle_notificacion,
        name="detalle",
    ),

    path(
        "<int:notificacion_id>/leer/",
        views.marcar_leida,
        name="marcar_leida",
    ),

    path(
        "leer-todas/",
        views.marcar_todas_leidas,
        name="marcar_todas",
    ),
]
