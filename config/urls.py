
from django.contrib import admin
from django.urls import include, path


urlpatterns = [

    # PANEL DE ADMINISTRACIÓN DE DJANGO
    path(
        "admin/",
        admin.site.urls,
    ),

    # USUARIOS Y AUTENTICACIÓN - JAIRO
    path(
        "usuarios/",
        include("usuarios.urls"),
    ),

    # ADMINISTRACIÓN - JAIRO
    path(
        "administracion/",
        include("administracion.urls"),
    ),

    # PACIENTES - JUAN
    path(
        "pacientes/",
        include("pacientes.urls"),
    ),

    # FISIOTERAPEUTAS Y HORARIOS - JUAN
    path(
        "fisioterapeutas/",
        include("fisioterapeutas.urls"),
    ),

    # SERVICIOS Y PRECIOS - JUAN
    path(
        "precios/",
        include("precios.urls"),
    ),

    # CITAS - KEVIN
    path(
        "citas/",
        include("citas.urls"),
    ),

    # NOTIFICACIONES - KEVIN
    path(
        "notificaciones/",
        include("notificaciones.urls"),
    ),

    # CONSULTAS - SALAZAR
    path(
        "consultas/",
        include("consultas.urls"),
    ),

    # TRATAMIENTOS - SALAZAR
    path(
        "tratamientos/",
        include("tratamientos.urls"),
    ),

    # PROGRESO - SALAZAR
    path(
        "progreso/",
        include("progreso.urls"),
    ),

    # RECETAS - SALAZAR
    path(
        "recetas/",
        include("recetas.urls"),
    ),

    # CALIFICACIONES - SALAZAR
    path(
        "calificaciones/",
        include("calificaciones.urls"),
    ),


    path("reportes/", include("reportes.urls")),

]
