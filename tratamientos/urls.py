from django.urls import path

from . import views


app_name = "tratamientos"


urlpatterns = [

    # ==========================================
    # REGISTRAR TRATAMIENTO
    # ==========================================

    path(
        "consulta/<int:consulta_id>/nuevo/",
        views.registrar_tratamiento,
        name="registrar_tratamiento",
    ),

    # ==========================================
    # HISTORIAL DE TRATAMIENTOS
    # ==========================================

    path(
        "consulta/<int:consulta_id>/historial/",
        views.historial_tratamientos,
        name="historial_tratamientos",
    ),

    # ==========================================
    # DETALLE DEL TRATAMIENTO
    # ==========================================

    path(
        "<int:tratamiento_id>/",
        views.detalle_tratamiento,
        name="detalle_tratamiento",
    ),

    # ==========================================
    # EDITAR TRATAMIENTO
    # ==========================================

    path(
        "<int:tratamiento_id>/editar/",
        views.editar_tratamiento,
        name="editar_tratamiento",
    ),

]