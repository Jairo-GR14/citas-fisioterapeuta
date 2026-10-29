from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from usuarios.decorators import rol_requerido
from usuarios.models import PerfilUsuario


@rol_requerido(["ADMINISTRADOR"])
def lista_usuarios(request):
    usuarios = User.objects.select_related("perfil").all().order_by("username")

    return render(
        request,
        "administracion/lista_usuarios.html",
        {
            "usuarios": usuarios,
        },
    )


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


@rol_requerido(["ADMINISTRADOR"])
def editar_usuario(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)

    perfil, _ = PerfilUsuario.objects.get_or_create(
        usuario=usuario,
        defaults={
            "rol": PerfilUsuario.Rol.PACIENTE,
        },
    )

    if request.method == "POST":
        usuario.first_name = request.POST.get("nombre", "").strip()
        usuario.last_name = request.POST.get("apellidos", "").strip()
        usuario.email = request.POST.get("email", "").strip()

        rol = request.POST.get("rol")

        roles_validos = {
            opcion[0]
            for opcion in PerfilUsuario.Rol.choices
        }

        if rol in roles_validos:
            perfil.rol = rol

        usuario.save()
        perfil.save()

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


@rol_requerido(["ADMINISTRADOR"])
def cambiar_estado_usuario(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)

    if usuario == request.user:
        messages.error(
            request,
            "No puedes desactivar tu propia cuenta.",
        )

        return redirect(
            "administracion:lista_usuarios",
        )

    usuario.is_active = not usuario.is_active
    usuario.save()

    messages.success(
        request,
        "Estado del usuario actualizado.",
    )

    return redirect(
        "administracion:lista_usuarios",
    )