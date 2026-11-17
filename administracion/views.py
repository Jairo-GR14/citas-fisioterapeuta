
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from citas.models import Cita
from fisioterapeutas.models import Fisioterapeuta
from pacientes.models import Paciente
from usuarios.decorators import rol_requerido
from usuarios.models import PerfilUsuario

from .models import RegistroActividad


User = get_user_model()


# =========================================================
# REGISTRAR ACTIVIDAD ADMINISTRATIVA
# =========================================================

def registrar_actividad(request, accion, descripcion):

    perfil = getattr(
        request.user,
        "perfil",
        None,
    )

    return RegistroActividad.objects.create(
        usuario=perfil,
        accion=accion,
        descripcion=descripcion,
        modulo="administracion",
    )


# =========================================================
# MOSTRAR FORMULARIO DE EDICIÓN
# =========================================================

def mostrar_edicion(request, usuario, perfil):

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
# ASEGURAR REGISTRO SEGÚN EL ROL
# =========================================================

def asegurar_registro_rol(perfil):

    if perfil.rol == PerfilUsuario.Rol.PACIENTE:

        Paciente.objects.get_or_create(
            usuario=perfil,
            defaults={
                "activo": perfil.activo,
            },
        )

    elif perfil.rol == PerfilUsuario.Rol.FISIOTERAPEUTA:

        Fisioterapeuta.objects.get_or_create(
            usuario=perfil,
            defaults={
                "activo": perfil.activo,
            },
        )


# =========================================================
# COMPROBAR CITAS PENDIENTES
# =========================================================

def tiene_citas_pendientes(perfil):

    citas = Cita.objects.filter(
        Q(paciente__usuario=perfil)
        | Q(fisioterapeuta__usuario=perfil)
    )

    return citas.filter(
        Q(estado=Cita.Estado.EN_PROCESO)
        | Q(
            estado__in=[
                Cita.Estado.PROGRAMADA,
                Cita.Estado.CONFIRMADA,
            ],
            fecha__gte=timezone.localdate(),
        )
    ).exists()


# =========================================================
# SINCRONIZAR ESTADO DE CUENTA Y PERFILES
# =========================================================

def sincronizar_estado(usuario, activar):

    usuario.is_active = activar

    usuario.save(
        update_fields=["is_active"]
    )

    perfil = getattr(
        usuario,
        "perfil",
        None,
    )

    if perfil is None:
        return

    perfil.activo = activar

    perfil.save(
        update_fields=[
            "activo",
            "fecha_actualizacion",
        ]
    )

    paciente = getattr(
        perfil,
        "paciente",
        None,
    )

    if paciente is not None:

        paciente.activo = activar

        paciente.save(
            update_fields=[
                "activo",
                "fecha_actualizacion",
            ]
        )

    fisioterapeuta = getattr(
        perfil,
        "fisioterapeuta",
        None,
    )

    if fisioterapeuta is not None:

        fisioterapeuta.activo = activar

        fisioterapeuta.save(
            update_fields=[
                "activo",
                "fecha_actualizacion",
            ]
        )


# =========================================================
# LISTA DE USUARIOS
# =========================================================

@rol_requerido(["ADMINISTRADOR"])
def lista_usuarios(request):

    usuarios = (
        User.objects
        .select_related("perfil")
        .all()
        .order_by("username")
    )

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

@rol_requerido(["ADMINISTRADOR"])
def detalle_usuario(request, usuario_id):

    usuario = get_object_or_404(
        User.objects.select_related("perfil"),
        pk=usuario_id,
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

@rol_requerido(["ADMINISTRADOR"])
def editar_usuario(request, usuario_id):

    usuario = get_object_or_404(
        User,
        pk=usuario_id,
    )

    # Un administrador normal no puede editar
    # cuentas de superusuario.
    if usuario.is_superuser:
        raise PermissionDenied(
            "No puedes editar una cuenta de superusuario "
            "desde este panel."
        )

    perfil = getattr(
        usuario,
        "perfil",
        None,
    )

    # Consultar la página no debe crear un perfil.
    if request.method != "POST":
        return mostrar_edicion(
            request,
            usuario,
            perfil,
        )

    nombre = request.POST.get(
        "nombre", ""
    ).strip()

    apellidos = request.POST.get(
        "apellidos", ""
    ).strip()

    email = request.POST.get(
        "email", ""
    ).strip().lower()

    nuevo_rol = request.POST.get(
        "rol", ""
    ).strip()

    roles_validos = {
        opcion[0]
        for opcion in PerfilUsuario.Rol.choices
    }

    errores = []

    if not nombre:
        errores.append(
            "El nombre es obligatorio."
        )

    elif len(nombre) > 150:
        errores.append(
            "El nombre no puede superar 150 caracteres."
        )

    if not apellidos:
        errores.append(
            "Los apellidos son obligatorios."
        )

    elif len(apellidos) > 150:
        errores.append(
            "Los apellidos no pueden superar 150 caracteres."
        )

    if not email:
        errores.append(
            "El correo electrónico es obligatorio."
        )

    else:

        try:
            validate_email(email)

        except ValidationError:
            errores.append(
                "El correo electrónico no es válido."
            )

        if len(email) > 254:
            errores.append(
                "El correo electrónico es demasiado largo."
            )

        elif User.objects.filter(
            email__iexact=email
        ).exclude(
            pk=usuario.pk
        ).exists():

            errores.append(
                "Este correo electrónico ya está registrado."
            )

    if nuevo_rol not in roles_validos:
        errores.append(
            "Selecciona un rol válido."
        )

    # Evitar que un administrador pierda acceso
    # cambiándose su propio rol.
    roles_clinicos = {
        PerfilUsuario.Rol.PACIENTE,
        PerfilUsuario.Rol.FISIOTERAPEUTA,
    }

    rol_actual = perfil.rol if perfil is not None else None

    if nuevo_rol != rol_actual and (
        nuevo_rol in roles_clinicos
        or rol_actual in roles_clinicos
    ):
        errores.append(
            "No se permite cambiar directamente hacia o desde "
            "Paciente o Fisioterapeuta desde este panel."
        )

    if (
        usuario.pk == request.user.pk
        and perfil is not None
        and nuevo_rol != perfil.rol
    ):
        errores.append(
            "No puedes cambiar tu propio rol."
        )

    if errores:

        for error in errores:
            messages.error(
                request,
                error,
            )

        return mostrar_edicion(
            request,
            usuario,
            perfil,
        )

    rol_anterior = (
        perfil.rol
        if perfil is not None
        else "SIN_PERFIL"
    )

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

            perfil = PerfilUsuario.objects.create(
                usuario=usuario,
                rol=nuevo_rol,
                activo=usuario.is_active,
            )

        else:

            perfil.rol = nuevo_rol

            perfil.save(
                update_fields=[
                    "rol",
                    "fecha_actualizacion",
                ]
            )

        # Garantizar que el rol tenga su registro
        # correspondiente de Paciente o Fisioterapeuta.
        asegurar_registro_rol(perfil)

        registrar_actividad(
            request,
            "EDITAR_USUARIO",
            (
                f"Se editó el usuario {usuario.username}. "
                f"Rol anterior: {rol_anterior}. "
                f"Rol nuevo: {nuevo_rol}."
            ),
        )

    messages.success(
        request,
        "Usuario actualizado correctamente.",
    )

    return redirect(
        "administracion:detalle_usuario",
        usuario_id=usuario.pk,
    )


# =========================================================
# ACTIVAR / DESACTIVAR USUARIO
# =========================================================

@rol_requerido(["ADMINISTRADOR"])
@require_POST
def cambiar_estado_usuario(request, usuario_id):

    with transaction.atomic():

        usuario = get_object_or_404(
            User.objects.select_for_update(),
            pk=usuario_id,
        )

        # No permitir la desactivación propia.
        if usuario.pk == request.user.pk:

            messages.error(
                request,
                "No puedes cambiar el estado de tu propia cuenta.",
            )

            return redirect(
                "administracion:lista_usuarios"
            )

        # No modificar superusuarios desde este panel.
        if usuario.is_superuser:

            messages.error(
                request,
                "No puedes cambiar el estado de una cuenta "
                "de superusuario desde este panel.",
            )

            return redirect(
                "administracion:lista_usuarios"
            )

        activar = not usuario.is_active

        perfil = getattr(
            usuario,
            "perfil",
            None,
        )

        # Evitar que se pierdan citas activas
        # o futuras al desactivar al usuario.
        if (
            not activar
            and perfil is not None
            and tiene_citas_pendientes(perfil)
        ):

            messages.error(
                request,
                "No se puede desactivar al usuario "
                "porque tiene citas activas o futuras.",
            )

            return redirect(
                "administracion:lista_usuarios"
            )

        sincronizar_estado(
            usuario,
            activar,
        )

        accion = (
            "ACTIVAR_USUARIO"
            if activar
            else "DESACTIVAR_USUARIO"
        )

        registrar_actividad(
            request,
            accion,
            (
                f"Se {'activó' if activar else 'desactivó'} "
                f"la cuenta {usuario.username}."
            ),
        )

    messages.success(
        request,
        (
            "Usuario activado correctamente."
            if activar
            else "Usuario desactivado correctamente."
        ),
    )

    return redirect(
        "administracion:lista_usuarios"
    )
