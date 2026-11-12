
from django.urls import path

from . import views


app_name = "precios"


urlpatterns = [
    path(
        "",
        views.lista_precios,
        name="lista_precios",
    ),

    path(
        "registrar/",
        views.registrar_precio,
        name="registrar_precio",
    ),

    path(
        "<int:servicio_id>/editar/",
        views.editar_precio,
        name="editar_precio",
    ),
]
