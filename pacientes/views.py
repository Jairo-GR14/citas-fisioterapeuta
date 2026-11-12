
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone

from citas.models import Cita
from usuarios.models import PerfilUsuario

from .forms import EditarPacienteForm, RegistrarPacienteForm
from .models import Paciente


GESTION = (
    PerfilUsuario.Rol.ADMINISTRADOR,
    PerfilUsuario.Rol.RECEPCIONISTA,
)


# OBTENER ROL

def rol_actual(request):

    usuario = request.user

    if not usuario.is_active:
        raise PermissionDenied(
            "Tu cuenta está desactivada."
        )

    if usuario.is_superuser:
        return PerfilUsuario.Rol.ADMINISTRADOR

    perfil = getattr(usuario, "perfil", None)

    if perfil is None or not perfil.activo:
        raise PermissionDenied(
            "No tienes un perfil activo."
        )

    return perfil.rol


# FILTRAR PACIENTES SEGÚN PERMISOS

def pacientes_visibles(request, incluir_propio=False):

    rol = rol_actual(request)

    consulta = Paciente.objects.select_related(
        "usuario__usuario"
    )

    if rol in GESTION:
        return consulta

    if rol == PerfilUsuario.Rol.FISIOTERAPEUTA:
        return consulta.filter(
            citas__fisioterapeuta__usuario=request.user.perfil
        ).distinct()

    if incluir_propio and rol == PerfilUsuario.Rol.PACIENTE:
        return consulta.filter(
            usuario=request.user.perfil
        )

    raise PermissionDenied(
        "No tienes permiso para consultar esta sección."
    )


# LISTAR PACIENTES

@login_required
def lista_pacientes(request):

    rol = rol_actual(request)

    pacientes = pacientes_visibles(request)

    buscar = request.GET.get(
        "buscar", ""
    ).strip()

    if buscar:
        pacientes = pacientes.filter(
            Q(usuario__usuario__first_name__icontains=buscar)
            | Q(usuario__usuario__last_name__icontains=buscar)
            | Q(usuario__usuario__username__icontains=buscar)
            | Q(usuario__usuario__email__icontains=buscar)
            | Q(usuario__telefono__icontains=buscar)
        )

    return render(
        request,
        "pacientes/lista_pacientes.html",
        {
            "pacientes": pacientes.order_by(
                "usuario__usuario__first_name",
                "id",
            ),
            "buscar": buscar,
            "puede_gestionar": rol in GESTION,
        },
    )


# REGISTRAR PACIENTE

@login_required
def registrar_paciente(request):

    rol = rol_actual(request)

    if rol not in GESTION:
        raise PermissionDenied

    formulario = RegistrarPacienteForm(
        request.POST if request.method == "POST" else None,
        incluir_antecedentes=(
            rol == PerfilUsuario.Rol.ADMINISTRADOR
        ),
    )

    if request.method == "POST" and formulario.is_valid():

        datos = formulario.cleaned_data

        try:
            with transaction.atomic():

                usuario = User.objects.create_user(
                    username=datos["username"],
                    password=datos["password1"],
                    first_name=datos["nombre"],
                    last_name=datos["apellidos"],
                    email=datos["email"],
                )

                perfil = PerfilUsuario.objects.create(
                    usuario=usuario,
                    rol=PerfilUsuario.Rol.PACIENTE,
                    telefono=datos["telefono"],
                )

                paciente = Paciente.objects.create(
                    usuario=perfil,
                    fecha_nacimiento=datos["fecha_nacimiento"],
                    direccion=datos["direccion"],
                    contacto_emergencia=datos["contacto_emergencia"],
                    telefono_emergencia=datos["telefono_emergencia"],
                    antecedentes_medicos=datos.get(
                        "antecedentes_medicos", ""
                    ),
                )

        except IntegrityError:
            formulario.add_error(
                None,
                "No fue posible crear la cuenta. "
                "El usuario puede estar duplicado.",
            )

        else:
            messages.success(
                request,
                "Paciente registrado correctamente.",
            )

            return redirect(
                "pacientes:detalle_paciente",
                paciente_id=paciente.pk,
            )

    return render(
        request,
        "pacientes/registrar_paciente.html",
        {
            "form": formulario,
        },
    )


# DETALLE DEL PACIENTE

@login_required
def detalle_paciente(request, paciente_id):

    rol = rol_actual(request)

    paciente = get_object_or_404(
        pacientes_visibles(
            request,
            incluir_propio=True,
        ),
        pk=paciente_id,
    )

    puede_gestionar = rol in GESTION

    puede_historial = rol in (
        PerfilUsuario.Rol.ADMINISTRADOR,
        PerfilUsuario.Rol.PACIENTE,
        PerfilUsuario.Rol.FISIOTERAPEUTA,
    )

    return render(
        request,
        "pacientes/detalle_paciente.html",
        {
            "paciente": paciente,
            "puede_gestionar": puede_gestionar,
            "puede_historial": puede_historial,
            "puede_desactivar": (
                rol == PerfilUsuario.Rol.ADMINISTRADOR
            ),
            "puede_ver_antecedentes": (
                rol != PerfilUsuario.Rol.RECEPCIONISTA
            ),
            "puede_ver_lista": (
                rol in GESTION
                or rol == PerfilUsuario.Rol.FISIOTERAPEUTA
            ),
        },
    )


# EDITAR PACIENTE

@login_required
def editar_paciente(request, paciente_id):

    rol = rol_actual(request)

    if rol not in GESTION:
        raise PermissionDenied

    paciente = get_object_or_404(
        Paciente.objects.select_related(
            "usuario__usuario"
        ),
        pk=paciente_id,
    )

    usuario = paciente.usuario.usuario

    if request.method == "POST":

        formulario = EditarPacienteForm(
            request.POST,
            usuario_actual=usuario,
            incluir_antecedentes=(
                rol == PerfilUsuario.Rol.ADMINISTRADOR
            ),
        )

    else:

        formulario = EditarPacienteForm(
            usuario_actual=usuario,
            incluir_antecedentes=(
                rol == PerfilUsuario.Rol.ADMINISTRADOR
            ),
            initial={
                "nombre": usuario.first_name,
                "apellidos": usuario.last_name,
                "email": usuario.email,
                "telefono": paciente.usuario.telefono,
                "fecha_nacimiento": paciente.fecha_nacimiento,
                "direccion": paciente.direccion,
                "contacto_emergencia": paciente.contacto_emergencia,
                "telefono_emergencia": paciente.telefono_emergencia,
                "antecedentes_medicos": paciente.antecedentes_medicos,
            },
        )

    if request.method == "POST" and formulario.is_valid():

        datos = formulario.cleaned_data

        with transaction.atomic():

            usuario.first_name = datos["nombre"]
            usuario.last_name = datos["apellidos"]
            usuario.email = datos["email"]

            usuario.save(
                update_fields=[
                    "first_name",
                    "last_name",
                    "email",
                ]
            )

            paciente.usuario.telefono = datos["telefono"]

            paciente.usuario.save(
                update_fields=[
                    "telefono",
                    "fecha_actualizacion",
                ]
            )

            paciente.fecha_nacimiento = datos["fecha_nacimiento"]
            paciente.direccion = datos["direccion"]
            paciente.contacto_emergencia = datos["contacto_emergencia"]
            paciente.telefono_emergencia = datos["telefono_emergencia"]

            if rol == PerfilUsuario.Rol.ADMINISTRADOR:
                paciente.antecedentes_medicos = datos[
                    "antecedentes_medicos"
                ]

            paciente.save()

        messages.success(
            request,
            "Datos del paciente actualizados.",
        )

        return redirect(
            "pacientes:detalle_paciente",
            paciente_id=paciente.pk,
        )

    return render(
        request,
        "pacientes/editar_paciente.html",
        {
            "form": formulario,
            "paciente": paciente,
        },
    )


# HISTORIAL DEL PACIENTE

@login_required
def historial_paciente(request, paciente_id):

    rol = rol_actual(request)

    # Recepción no tiene acceso a diagnósticos.
    if rol == PerfilUsuario.Rol.RECEPCIONISTA:
        raise PermissionDenied(
            "El historial clínico es privado."
        )

    paciente = get_object_or_404(
        pacientes_visibles(
            request,
            incluir_propio=True,
        ),
        pk=paciente_id,
    )

    citas = Cita.objects.filter(
        paciente=paciente
    ).select_related(
        "servicio",
        "motivo",
        "fisioterapeuta__usuario__usuario",
        "consulta",
    )

    # El fisioterapeuta solo ve las consultas
    # que le fueron asignadas.
    if rol == PerfilUsuario.Rol.FISIOTERAPEUTA:

        citas = citas.filter(
            fisioterapeuta__usuario=request.user.perfil
        )

    return render(
        request,
        "pacientes/historial_paciente.html",
        {
            "paciente": paciente,
            "citas": citas.order_by(
                "-fecha", "-hora"
            ),
        },
    )


# DESACTIVAR PACIENTE SIN BORRAR SU HISTORIAL

@login_required
def eliminar_paciente(request, paciente_id):

    if rol_actual(request) != PerfilUsuario.Rol.ADMINISTRADOR:
        raise PermissionDenied

    paciente = get_object_or_404(
        Paciente.objects.select_related(
            "usuario__usuario"
        ),
        pk=paciente_id,
    )

    if request.method == "POST":

        pendientes = paciente.citas.filter(
            Q(estado=Cita.Estado.EN_PROCESO)
            | Q(
                estado__in=[
                    Cita.Estado.PROGRAMADA,
                    Cita.Estado.CONFIRMADA,
                ],
                fecha__gte=timezone.localdate(),
            )
        ).exists()

        if pendientes:
            messages.error(
                request,
                "No se puede desactivar: "
                "tiene citas activas o futuras.",
            )

            return redirect(
                "pacientes:detalle_paciente",
                paciente_id=paciente.pk,
            )

        with transaction.atomic():

            paciente.activo = False
            paciente.save(
                update_fields=[
                    "activo",
                    "fecha_actualizacion",
                ]
            )

            perfil = paciente.usuario
            perfil.activo = False

            perfil.save(
                update_fields=[
                    "activo",
                    "fecha_actualizacion",
                ]
            )

            usuario = perfil.usuario
            usuario.is_active = False

            usuario.save(
                update_fields=["is_active"]
            )

        messages.success(
            request,
            "Paciente desactivado sin borrar su historial.",
        )

        return redirect(
            "pacientes:lista_pacientes"
        )

    return render(
        request,
        "pacientes/eliminar_paciente.html",
        {
            "paciente": paciente,
        },
    )
