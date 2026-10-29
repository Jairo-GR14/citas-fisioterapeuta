from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def rol_requerido(roles_permitidos):
    def decorador(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("usuarios:login")

            if request.user.is_superuser:
                return view_func(
                    request,
                    *args,
                    **kwargs
                )

            try:
                rol = request.user.perfil.rol

            except AttributeError:
                messages.error(
                    request,
                    "Tu usuario no tiene un perfil asignado.",
                )

                return redirect(
                    "usuarios:login"
                )

            if rol not in roles_permitidos:
                messages.error(
                    request,
                    "No tienes permiso para acceder a esta sección.",
                )

                return redirect(
                    "usuarios:redireccion_por_rol"
                )

            return view_func(
                request,
                *args,
                **kwargs
            )

        return wrapper

    return decorador