from django.urls import path

from . import views

app_name = "administracion"

urlpatterns = [
    path(
        "usuarios/",
        views.lista_usuarios,
        name="lista_usuarios",
    ),
    path(
        "usuarios/<int:usuario_id>/",
        views.detalle_usuario,
        name="detalle_usuario",
    ),
    path(
        "usuarios/<int:usuario_id>/editar/",
        views.editar_usuario,
        name="editar_usuario",
    ),
    path(
        "usuarios/<int:usuario_id>/estado/",
        views.cambiar_estado_usuario,
        name="cambiar_estado_usuario",
    ),
]