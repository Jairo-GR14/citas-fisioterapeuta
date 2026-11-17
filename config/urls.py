
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView


urlpatterns = [

    # =====================================================
    # PÁGINA PRINCIPAL
    # =====================================================
    # Redirige al login si no hay sesión activa.
    # Si el usuario ya inició sesión, lo dirige
    # a su dashboard correspondiente.
    path(
        "",
        RedirectView.as_view(
            pattern_name="usuarios:redireccion_por_rol",
            permanent=False,
        ),
        name="inicio",
    ),

    # =====================================================
    # PANEL DE ADMINISTRACIÓN DE DJANGO
    # =====================================================
    path(
        "admin/",
        admin.site.urls,
    ),

    # =====================================================
    # USUARIOS Y AUTENTICACIÓN - JAIRO
    # =====================================================
    path(
        "usuarios/",
        include("usuarios.urls"),
    ),

    # =====================================================
    # ADMINISTRACIÓN - JAIRO
    # =====================================================
    path(
        "administracion/",
        include("administracion.urls"),
    ),

    # =====================================================
    # PACIENTES - JUAN
    # =====================================================
    path(
        "pacientes/",
        include("pacientes.urls"),
    ),

    # =====================================================
    # FISIOTERAPEUTAS Y HORARIOS - JUAN
    # =====================================================
    path(
        "fisioterapeutas/",
        include("fisioterapeutas.urls"),
    ),

    # =====================================================
    # SERVICIOS Y PRECIOS - JUAN
    # =====================================================
    path(
        "precios/",
        include("precios.urls"),
    ),

    # =====================================================
    # CITAS - KEVIN
    # =====================================================
    path(
        "citas/",
        include("citas.urls"),
    ),

    # =====================================================
    # NOTIFICACIONES - KEVIN
    # =====================================================
    path(
        "notificaciones/",
        include("notificaciones.urls"),
    ),

    # =====================================================
    # CONSULTAS - SALAZAR
    # =====================================================
    path(
        "consultas/",
        include("consultas.urls"),
    ),

    # =====================================================
    # TRATAMIENTOS - SALAZAR
    # =====================================================
    path(
        "tratamientos/",
        include("tratamientos.urls"),
    ),

    # =====================================================
    # PROGRESO - SALAZAR
    # =====================================================
    path(
        "progreso/",
        include("progreso.urls"),
    ),

    # =====================================================
    # RECETAS - SALAZAR
    # =====================================================
    path(
        "recetas/",
        include("recetas.urls"),
    ),

    # =====================================================
    # CALIFICACIONES - SALAZAR
    # =====================================================
    path(
        "calificaciones/",
        include("calificaciones.urls"),
    ),

    # =====================================================
    # REPORTES - JAIRO
    # =====================================================
    path(
        "reportes/",
        include("reportes.urls"),
    ),

]
