
from functools import wraps

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


# =========================================================
# DECORADOR PARA CONTROLAR ACCESO POR ROLES
# =========================================================

def rol_requerido(roles_permitidos):

    def decorador(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            usuario = request.user

            # 1. Verificar que haya iniciado sesión.
            if not usuario.is_authenticated:

                return redirect(
                    "usuarios:login"
                )

            # 2. Bloquear cuentas de usuario inactivas.
            if not usuario.is_active:

                raise PermissionDenied(
                    "Tu cuenta de usuario está desactivada."
                )

            # 3. Obtener el perfil del usuario.
            perfil = getattr(
                usuario,
                "perfil",
                None,
            )

            # 4. Bloquear perfiles desactivados.
            # Esta comprobación también aplica a
            # superusuarios que tengan un perfil.
            if perfil is not None and not perfil.activo:

                raise PermissionDenied(
                    "Tu perfil está desactivado. "
                    "No puedes acceder a esta sección."
                )

            # 5. Permitir a superusuarios activos.
            # No se exige perfil a un superusuario
            # que no tenga uno asignado.
            if usuario.is_superuser:

                return view_func(
                    request,
                    *args,
                    **kwargs
                )

            # 6. Verificar que el usuario tenga perfil.
            if perfil is None:

                messages.error(
                    request,
                    "Tu usuario no tiene un perfil asignado."
                )

                return redirect(
                    "usuarios:login"
                )

            # 7. Verificar que el rol esté autorizado.
            if perfil.rol not in roles_permitidos:

                messages.error(
                    request,
                    "No tienes permiso para acceder "
                    "a esta sección."
                )

                return redirect(
                    "usuarios:redireccion_por_rol"
                )

            # 8. Permitir el acceso.
            return view_func(
                request,
                *args,
                **kwargs
            )

        return wrapper

    return decorador
