from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views


app_name = "usuarios"


urlpatterns = [

    # =====================================================
    # AUTENTICACIÓN
    # =====================================================

    path(
        "login/",
        views.iniciar_sesion,
        name="login",
    ),

    path(
        "logout/",
        views.cerrar_sesion,
        name="logout",
    ),

    path(
        "redirigir/",
        views.redireccion_por_rol,
        name="redireccion_por_rol",
    ),


    # =====================================================
    # REGISTRO
    # =====================================================

    path(
        "registro/",
        views.registro,
        name="registro",
    ),


    # =====================================================
    # PERFIL
    # =====================================================

    path(
        "perfil/",
        views.perfil,
        name="perfil",
    ),

    path(
        "perfil/editar/",
        views.editar_perfil,
        name="editar_perfil",
    ),

    path(
        "cambiar-contrasena/",
        views.cambiar_contrasena,
        name="cambiar_contrasena",
    ),


    # =====================================================
    # RECUPERACIÓN DE CONTRASEÑA
    # =====================================================

    path(
        "recuperar-contrasena/",
        auth_views.PasswordResetView.as_view(
            template_name="usuarios/recuperar_contrasena.html",
            email_template_name="usuarios/correo_recuperacion.txt",
            subject_template_name="usuarios/asunto_recuperacion.txt",
            success_url=reverse_lazy(
                "usuarios:recuperar_contrasena_enviado"
            ),
        ),
        name="recuperar_contrasena",
    ),

    path(
        "recuperar-contrasena/enviado/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="usuarios/recuperar_contrasena_enviado.html",
        ),
        name="recuperar_contrasena_enviado",
    ),

    path(
        "restablecer-contrasena/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="usuarios/restablecer_contrasena.html",
            success_url=reverse_lazy(
                "usuarios:restablecer_contrasena_completo"
            ),
        ),
        name="restablecer_contrasena",
    ),

    path(
        "restablecer-contrasena/completo/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="usuarios/restablecer_contrasena_completo.html",
        ),
        name="restablecer_contrasena_completo",
    ),


    # =====================================================
    # DASHBOARDS
    # =====================================================

    path(
        "dashboard/administrador/",
        views.dashboard_administrador,
        name="dashboard_administrador",
    ),

    path(
        "dashboard/recepcionista/",
        views.dashboard_recepcionista,
        name="dashboard_recepcionista",
    ),

    path(
        "dashboard/fisioterapeuta/",
        views.dashboard_fisioterapeuta,
        name="dashboard_fisioterapeuta",
    ),

    path(
        "dashboard/paciente/",
        views.dashboard_paciente,
        name="dashboard_paciente",
    ),
]