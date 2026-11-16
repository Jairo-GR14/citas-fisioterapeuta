
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from usuarios.decorators import rol_requerido
from usuarios.models import PerfilUsuario


# =========================================================
# CONFIGURACIÓN DE ROLES
# =========================================================

ROLES_CLINICOS = {
    PerfilUsuario.Rol.PACIENTE,
    PerfilUsuario.Rol.FISIOTERAPEUTA,
}

ROLES_ADMINISTRATIVOS = {
    PerfilUsuario.Rol.ADMINISTRADOR,
    PerfilUsuario.Rol.RECEPCIONISTA,
}


# =========================================================
# LISTA DE USUARIOS
# =========================================================

@login_required
@rol_requerido(["ADMINISTRADOR"])
def lista_usuarios(request):

    usuarios = User.objects.select_related(
        "perfil"
    ).all().order_by("username")

    return render(
        request,
        "administracion/lista_usuarios.html",
        {
            "usuarios": usuarios,
        },
    )


# =========================================================
# DETALLE DE USUARIO
# =========================================================

@login_required
@rol_requerido(["ADMINISTRADOR"])
def detalle_usuario(request, usuario_id):

    usuario = get_object_or_404(
        User.objects.select_related("perfil"),
        id=usuario_id,
    )

    return render(
        request,
        "administracion/detalle_usuario.html",
        {
            "usuario_seleccionado": usuario,
        },
    )


# =========================================================
# EDITAR USUARIO
# =========================================================

@login_required
@rol_requerido(["ADMINISTRADOR"])
def editar_usuario(request, usuario_id):

    usuario = get_object_or_404(
        User,
        id=usuario_id,
    )

    # Las cuentas de superusuario se administran
    # directamente desde Django Admin.
    if usuario.is_superuser:
        messages.error(
            request,
            "No puedes editar una cuenta de superusuario "
            "desde este panel.",
        )

        return redirect(
            "administracion:lista_usuarios"
        )

    # No crear perfiles automáticamente con rol PACIENTE.
    # Esto evita generar pacientes incompletos.
    perfil = PerfilUsuario.objects.filter(
        usuario=usuario
    ).first()

    if request.method == "POST":

        nombre = request.POST.get(
            "nombre", ""
        ).strip()

        apellidos = request.POST.get(
            "apellidos", ""
        ).strip()

        email = request.POST.get(
            "email", ""
        ).strip()

        nuevo_rol = request.POST.get(
            "rol", ""
        ).strip()

        # ---------------------------------------------
        # VALIDAR ROL
        # ---------------------------------------------

        roles_validos = {
            opcion[0]
            for opcion in PerfilUsuario.Rol.choices
        }

        if nuevo_rol not in roles_validos:
            messages.error(
                request,
                "Selecciona un rol válido.",
            )

            return redirect(
                "administracion:editar_usuario",
                usuario_id=usuario.id,
            )

        rol_actual = perfil.rol if perfil else None

        # ---------------------------------------------
        # PROTEGER LOS ROLES CLÍNICOS
        # ---------------------------------------------

        cambio_rol = nuevo_rol != rol_actual

        if cambio_rol and (
            nuevo_rol in ROLES_CLINICOS
            or rol_actual in ROLES_CLINICOS
        ):

            messages.error(
                request,
                "No se permite cambiar directamente "
                "a un usuario hacia o desde un rol clínico. "
                "Utiliza los módulos de Pacientes o "
                "Fisioterapeutas para gestionar esos registros.",
            )

            return redirect(
                "administracion:editar_usuario",
                usuario_id=usuario.id,
            )

        # ---------------------------------------------
        # PROTEGER EL ROL DEL ADMINISTRADOR ACTUAL
        # ---------------------------------------------

        if usuario == request.user and cambio_rol:

            messages.error(
                request,
                "No puedes modificar tu propio rol.",
            )

            return redirect(
                "administracion:editar_usuario",
                usuario_id=usuario.id,
            )

        # ---------------------------------------------
        # VALIDAR CORREO DUPLICADO
        # ---------------------------------------------

        if email and User.objects.filter(
            email__iexact=email
        ).exclude(
            id=usuario.id
        ).exists():

            messages.error(
                request,
                "Ese correo electrónico ya está "
                "registrado por otro usuario.",
            )

            return redirect(
                "administracion:editar_usuario",
                usuario_id=usuario.id,
            )

        # ---------------------------------------------
        # GUARDAR CAMBIOS
        # ---------------------------------------------

        with transaction.atomic():

            usuario.first_name = nombre
            usuario.last_name = apellidos
            usuario.email = email

            usuario.save(
                update_fields=[
                    "first_name",
                    "last_name",
                    "email",
                ]
            )

            if perfil is None:

                # Solo se permite crear un perfil nuevo
                # desde aquí para roles administrativos.
                if nuevo_rol in ROLES_ADMINISTRATIVOS:

                    perfil = PerfilUsuario.objects.create(
                        usuario=usuario,
                        rol=nuevo_rol,
                    )

            elif cambio_rol:

                perfil.rol = nuevo_rol
                perfil.save(
                    update_fields=["rol"]
                )

        messages.success(
            request,
            "Usuario actualizado correctamente.",
        )

        return redirect(
            "administracion:detalle_usuario",
            usuario_id=usuario.id,
        )

    return render(
        request,
        "administracion/editar_usuario.html",
        {
            "usuario_seleccionado": usuario,
            "perfil": perfil,
            "roles": PerfilUsuario.Rol.choices,
        },
    )


# =========================================================
# ACTIVAR / DESACTIVAR USUARIO
# =========================================================

@login_required
@rol_requerido(["ADMINISTRADOR"])
@require_POST
def cambiar_estado_usuario(request, usuario_id):

    usuario = get_object_or_404(
        User,
        id=usuario_id,
    )

    # Impedir que el administrador se desactive.
    if usuario == request.user:

        messages.error(
            request,
            "No puedes desactivar tu propia cuenta.",
        )

        return redirect(
            "administracion:lista_usuarios"
        )

    # Proteger cuentas de superusuario.
    if usuario.is_superuser:

        messages.error(
            request,
            "No puedes cambiar el estado de "
            "una cuenta de superusuario.",
        )

        return redirect(
            "administracion:lista_usuarios"
        )

    # Cambiar el estado de acceso.
    usuario.is_active = not usuario.is_active

    usuario.save(
        update_fields=["is_active"]
    )

    messages.success(
        request,
        "Estado del usuario actualizado.",
    )

    return redirect(
        "administracion:lista_usuarios"
    )
