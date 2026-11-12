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


from decimal import Decimal

from django.db.models import Q, Sum
from django.utils import timezone

from citas.models import Cita
from fisioterapeutas.models import Fisioterapeuta



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
# FUNCIÓN AUXILIAR: CITAS FUTURAS
# =========================================================

def obtener_citas_futuras(citas):
    """
    Devuelve citas programadas o confirmadas
    que todavía no han comenzado.
    """
    ahora = timezone.localtime()

    return citas.filter(
        estado__in=[
            Cita.Estado.PROGRAMADA,
            Cita.Estado.CONFIRMADA,
        ]
    ).filter(
        Q(fecha__gt=ahora.date())
        | Q(
            fecha=ahora.date(),
            hora__gte=ahora.time(),
        )
    )


# =========================================================
# DASHBOARD ADMINISTRADOR
# =========================================================

@login_required
@rol_requerido(["ADMINISTRADOR"])
def dashboard_administrador(request):

    hoy = timezone.localdate()

    total_pacientes = Paciente.objects.count()

    total_fisioterapeutas = (
        Fisioterapeuta.objects.count()
    )

    citas_hoy = Cita.objects.filter(
        fecha=hoy
    ).exclude(
        estado=Cita.Estado.CANCELADA
    ).count()

    # Proyección de ingresos por citas pendientes.
    # No representa pagos recibidos.
    ingreso_estimado = obtener_citas_futuras(
        Cita.objects.all()
    ).aggregate(
        total=Sum("costo_estimado")
    )["total"] or Decimal("0.00")

    citas = Cita.objects.select_related(
        "paciente__usuario__usuario",
        "fisioterapeuta__usuario__usuario",
        "servicio",
        "motivo",
    ).order_by(
        "-fecha_creacion",
        "-pk",
    )[:10]

    contexto = {
        "total_pacientes": total_pacientes,
        "total_fisioterapeutas": total_fisioterapeutas,
        "citas_hoy": citas_hoy,
        "ingreso_estimado": ingreso_estimado,
        "citas": citas,
    }

    return render(
        request,
        "dashboard/dashboard_admin.html",
        contexto,
    )


# =========================================================
# DASHBOARD RECEPCIONISTA
# =========================================================

@login_required
@rol_requerido(["RECEPCIONISTA"])
def dashboard_recepcionista(request):

    hoy = timezone.localdate()

    citas_hoy = Cita.objects.filter(
        fecha=hoy
    ).exclude(
        estado=Cita.Estado.CANCELADA
    ).count()

    total_pacientes = Paciente.objects.count()

    citas_pendientes = obtener_citas_futuras(
        Cita.objects.all()
    ).count()

    citas = Cita.objects.filter(
        fecha=hoy
    ).exclude(
        estado=Cita.Estado.CANCELADA
    ).select_related(
        "paciente__usuario__usuario",
        "fisioterapeuta__usuario__usuario",
        "servicio",
        "motivo",
    ).order_by(
        "hora"
    )

    contexto = {
        "citas_hoy": citas_hoy,
        "total_pacientes": total_pacientes,
        "citas_pendientes": citas_pendientes,
        "citas": citas,
    }

    return render(
        request,
        "dashboard/dashboard_recepcionista.html",
        contexto,
    )


# =========================================================
# DASHBOARD FISIOTERAPEUTA
# =========================================================

@login_required
@rol_requerido(["FISIOTERAPEUTA"])
def dashboard_fisioterapeuta(request):

    hoy = timezone.localdate()

    # Solo las citas asignadas al usuario actual.
    citas_propias = Cita.objects.filter(
        fisioterapeuta__usuario__usuario=request.user
    )

    citas_hoy = citas_propias.filter(
        fecha=hoy
    ).exclude(
        estado=Cita.Estado.CANCELADA
    ).count()

    # Pacientes distintos con citas finalizadas.
    pacientes_atendidos = citas_propias.filter(
        estado=Cita.Estado.FINALIZADA
    ).values(
        "paciente_id"
    ).distinct().count()

    citas_pendientes = obtener_citas_futuras(
        citas_propias
    ).count()

    proxima_cita = obtener_citas_futuras(
        citas_propias
    ).select_related(
        "paciente__usuario__usuario",
        "motivo",
        "servicio",
    ).order_by(
        "fecha",
        "hora",
    ).first()

    citas = citas_propias.filter(
        fecha=hoy
    ).exclude(
        estado=Cita.Estado.CANCELADA
    ).select_related(
        "paciente__usuario__usuario",
        "motivo",
        "servicio",
    ).order_by(
        "hora"
    )

    contexto = {
        "citas_hoy": citas_hoy,
        "pacientes_atendidos": pacientes_atendidos,
        "citas_pendientes": citas_pendientes,
        "proxima_cita": proxima_cita,
        "citas": citas,
    }

    return render(
        request,
        "dashboard/dashboard_fisioterapeuta.html",
        contexto,
    )


# =========================================================
# DASHBOARD PACIENTE
# =========================================================

@login_required
@rol_requerido(["PACIENTE"])
def dashboard_paciente(request):

    # Solo las citas del paciente autenticado.
    citas_propias = Cita.objects.filter(
        paciente__usuario__usuario=request.user
    )

    citas_futuras = obtener_citas_futuras(
        citas_propias
    )

    citas_pendientes = citas_futuras.count()

    citas_completadas = citas_propias.filter(
        estado=Cita.Estado.FINALIZADA
    ).count()

    citas = citas_futuras.select_related(
        "fisioterapeuta__usuario__usuario",
        "servicio",
        "motivo",
    ).order_by(
        "fecha",
        "hora",
    )

    proxima_cita = citas.first()

    contexto = {
        "proxima_cita": proxima_cita,
        "citas_pendientes": citas_pendientes,
        "citas_completadas": citas_completadas,
        "citas": citas,
    }

    return render(
        request,
        "dashboard/dashboard_paciente.html",
        contexto,
    )
