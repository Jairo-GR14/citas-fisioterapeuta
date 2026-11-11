from django.urls import path

from . import views


app_name = "recetas"


urlpatterns = [

    # ==========================================
    # REGISTRAR RECETA
    # ==========================================

    path(
        "consulta/<int:consulta_id>/nueva/",
        views.registrar_receta,
        name="registrar_receta",
    ),

    # ==========================================
    # LISTAR RECETAS DE UNA CONSULTA
    # ==========================================

    path(
        "consulta/<int:consulta_id>/",
        views.lista_recetas,
        name="lista_recetas",
    ),

    # ==========================================
    # DETALLE DE RECETA
    # ==========================================

    path(
        "<int:receta_id>/",
        views.detalle_receta,
        name="detalle_receta",
    ),

    # ==========================================
    # EDITAR RECETA
    # ==========================================

    path(
        "<int:receta_id>/editar/",
        views.editar_receta,
        name="editar_receta",
    ),

    # ==========================================
    # VER INDICACIONES COMO PACIENTE
    # ==========================================

    path(
        "paciente/<int:receta_id>/",
        views.receta_paciente,
        name="receta_paciente",
    ),

]