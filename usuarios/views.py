from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import redirect, render

from pacientes.models import Paciente

from .decorators import rol_requerido
from .models import PerfilUsuario


# =========================================================
# INICIO DE SESIÓN
# =========================================================

def iniciar_sesion(request):
    if request.user.is_authenticated:
        return redirect("usuarios:redireccion_por_rol")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        usuario = authenticate(
            request,
            username=username,
            password=password,
        )

        if usuario is not None:
            login(request, usuario)

            return redirect(
                "usuarios:redireccion_por_rol"
            )

        messages.error(
            request,
            "Usuario o contraseña incorrectos.",
        )

    return render(
        request,
        "usuarios/login.html",
    )


# =========================================================
# CERRAR SESIÓN
# =========================================================

def cerrar_sesion(request):
    logout(request)

    return redirect(
        "usuarios:login"
    )


# =========================================================
# REDIRECCIÓN SEGÚN ROL
# =========================================================

@login_required
def redireccion_por_rol(request):
    if request.user.is_superuser:
        return redirect(
            "usuarios:dashboard_administrador"
        )

    try:
        rol = request.user.perfil.rol

    except AttributeError:
        messages.error(
            request,
            "Tu usuario no tiene un perfil asignado.",
        )

        logout(request)

        return redirect(
            "usuarios:login"
        )

    if rol == PerfilUsuario.Rol.ADMINISTRADOR:
        return redirect(
            "usuarios:dashboard_administrador"
        )

    if rol == PerfilUsuario.Rol.RECEPCIONISTA:
        return redirect(
            "usuarios:dashboard_recepcionista"
        )

    if rol == PerfilUsuario.Rol.FISIOTERAPEUTA:
        return redirect(
            "usuarios:dashboard_fisioterapeuta"
        )

    if rol == PerfilUsuario.Rol.PACIENTE:
        return redirect(
            "usuarios:dashboard_paciente"
        )

    messages.error(
        request,
        "Tu usuario no tiene un rol válido.",
    )

    return redirect(
        "usuarios:login"
    )


# =========================================================
# REGISTRO DE PACIENTE
# =========================================================

def registro(request):
    if request.user.is_authenticated:
        return redirect(
            "usuarios:redireccion_por_rol"
        )

    if request.method == "POST":
        nombre = request.POST.get(
            "nombre",
            "",
        ).strip()

        apellidos = request.POST.get(
            "apellidos",
            "",
        ).strip()

        fecha_nacimiento = (
            request.POST.get("fecha_nacimiento")
            or None
        )

        telefono = request.POST.get(
            "telefono",
            "",
        ).strip()

        correo = request.POST.get(
            "correo",
            "",
        ).strip()

        username = request.POST.get(
            "usuario",
            "",
        ).strip()

        password = request.POST.get(
            "password",
            "",
        )

        password2 = request.POST.get(
            "password2",
            "",
        )

        # Validar campos obligatorios
        if not all([
            nombre,
            apellidos,
            telefono,
            correo,
            username,
            password,
            password2,
        ]):
            messages.error(
                request,
                "Completa todos los campos obligatorios.",
            )

            return render(
                request,
                "usuarios/registro.html",
            )

        # Validar contraseñas
        if password != password2:
            messages.error(
                request,
                "Las contraseñas no coinciden.",
            )

            return render(
                request,
                "usuarios/registro.html",
            )

        # Validar usuario repetido
        if User.objects.filter(
            username=username
        ).exists():
            messages.error(
                request,
                "Ese nombre de usuario ya está registrado.",
            )

            return render(
                request,
                "usuarios/registro.html",
            )

        # Validar correo repetido
        if User.objects.filter(
            email__iexact=correo
        ).exists():
            messages.error(
                request,
                "Ese correo electrónico ya está registrado.",
            )

            return render(
                request,
                "usuarios/registro.html",
            )

        # Validar seguridad de contraseña
        try:
            validate_password(password)

        except ValidationError as errores:
            for error in errores.messages:
                messages.error(
                    request,
                    error,
                )

            return render(
                request,
                "usuarios/registro.html",
            )

        # Crear usuario, perfil y paciente
        try:
            with transaction.atomic():

                usuario = User.objects.create_user(
                    username=username,
                    email=correo,
                    password=password,
                    first_name=nombre,
                    last_name=apellidos,
                )

                perfil_usuario = (
                    PerfilUsuario.objects.create(
                        usuario=usuario,
                        rol=PerfilUsuario.Rol.PACIENTE,
                        telefono=telefono,
                    )
                )

                Paciente.objects.create(
                    usuario=perfil_usuario,
                    fecha_nacimiento=fecha_nacimiento,
                )

        except Exception:
            messages.error(
                request,
                "No fue posible crear la cuenta.",
            )

            return render(
                request,
                "usuarios/registro.html",
            )

        messages.success(
            request,
            "Cuenta creada correctamente. "
            "Ya puedes iniciar sesión.",
        )

        return redirect(
            "usuarios:login"
        )

    return render(
        request,
        "usuarios/registro.html",
    )


# =========================================================
# PERFIL
# =========================================================

@login_required
def perfil(request):
    perfil_usuario = getattr(
        request.user,
        "perfil",
        None,
    )

    return render(
        request,
        "usuarios/perfil.html",
        {
            "perfil_usuario": perfil_usuario,
        },
    )


# =========================================================
# EDITAR PERFIL
# =========================================================

@login_required
def editar_perfil(request):
    perfil_usuario = getattr(
        request.user,
        "perfil",
        None,
    )

    if request.method == "POST":
        request.user.first_name = (
            request.POST.get(
                "nombre",
                "",
            ).strip()
        )

        request.user.last_name = (
            request.POST.get(
                "apellidos",
                "",
            ).strip()
        )

        request.user.email = (
            request.POST.get(
                "email",
                "",
            ).strip()
        )

        request.user.save()

        if perfil_usuario:
            perfil_usuario.telefono = (
                request.POST.get(
                    "telefono",
                    "",
                ).strip()
            )

            perfil_usuario.save()

        messages.success(
            request,
            "Perfil actualizado correctamente.",
        )

        return redirect(
            "usuarios:perfil"
        )

    return render(
        request,
        "usuarios/editar_perfil.html",
        {
            "perfil_usuario": perfil_usuario,
        },
    )


# =========================================================
# CAMBIAR CONTRASEÑA
# =========================================================

@login_required
def cambiar_contrasena(request):
    if request.method == "POST":
        formulario = PasswordChangeForm(
            request.user,
            request.POST,
        )

        if formulario.is_valid():
            usuario = formulario.save()

            update_session_auth_hash(
                request,
                usuario,
            )

            messages.success(
                request,
                "Contraseña actualizada correctamente.",
            )

            return redirect(
                "usuarios:perfil"
            )

    else:
        formulario = PasswordChangeForm(
            request.user
        )

    return render(
        request,
        "usuarios/cambiar_contrasena.html",
        {
            "formulario": formulario,
        },
    )


# =========================================================
# DASHBOARD ADMINISTRADOR
# =========================================================

@login_required
@rol_requerido(["ADMINISTRADOR"])
def dashboard_administrador(request):
    return render(
        request,
        "dashboard/dashboard_admin.html",
    )


# =========================================================
# DASHBOARD RECEPCIONISTA
# =========================================================

@login_required
@rol_requerido(["RECEPCIONISTA"])
def dashboard_recepcionista(request):
    return render(
        request,
        "dashboard/dashboard_recepcionista.html",
    )


# =========================================================
# DASHBOARD FISIOTERAPEUTA
# =========================================================

@login_required
@rol_requerido(["FISIOTERAPEUTA"])
def dashboard_fisioterapeuta(request):
    return render(
        request,
        "dashboard/dashboard_fisioterapeuta.html",
    )


# =========================================================
# DASHBOARD PACIENTE
# =========================================================

@login_required
@rol_requerido(["PACIENTE"])
def dashboard_paciente(request):
    return render(
        request,
        "dashboard/dashboard_paciente.html",
    )