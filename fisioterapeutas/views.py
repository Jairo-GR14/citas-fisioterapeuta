
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
from django.views.decorators.http import require_POST

from citas.models import Cita
from usuarios.models import PerfilUsuario

from .forms import (
    EditarFisioterapeutaForm,
    RegistrarFisioterapeutaForm,
)
from .models import Fisioterapeuta


GESTION = (
    PerfilUsuario.Rol.ADMINISTRADOR,
    PerfilUsuario.Rol.RECEPCIONISTA,
)


# COMPROBAR ROL

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


# FILTRAR FISIOTERAPEUTAS

def profesionales_visibles(request):
    rol = rol_actual(request)

    profesionales = Fisioterapeuta.objects.select_related(
        "usuario__usuario"
    )

    if rol in GESTION:
        return profesionales

    return profesionales.filter(
        activo=True,
        usuario__activo=True,
        usuario__usuario__is_active=True,
    )


# LISTADO

@login_required
def lista_fisioterapeutas(request):
    rol = rol_actual(request)

    profesionales = profesionales_visibles(request)

    buscar = request.GET.get(
        "buscar",
        "",
    ).strip()

    if buscar:
        profesionales = profesionales.filter(
            Q(
                usuario__usuario__first_name__icontains=buscar
            )
            | Q(
                usuario__usuario__last_name__icontains=buscar
            )
            | Q(
                especialidad__icontains=buscar
            )
            | Q(
                cedula_profesional__icontains=buscar
            )
        )

    return render(
        request,
        "fisioterapeutas/lista_fisioterapeutas.html",
        {
            "fisioterapeutas": profesionales.order_by(
                "usuario__usuario__first_name",
                "pk",
            ),
            "buscar": buscar,
            "puede_gestionar": rol in GESTION,
        },
    )


# REGISTRAR

@login_required
def registrar_fisioterapeuta(request):
    if rol_actual(request) not in GESTION:
        raise PermissionDenied

    formulario = RegistrarFisioterapeutaForm(
        request.POST or None
    )

    if (
        request.method == "POST"
        and formulario.is_valid()
    ):
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
                    rol=PerfilUsuario.Rol.FISIOTERAPEUTA,
                    telefono=datos["telefono"],
                )

                profesional = Fisioterapeuta.objects.create(
                    usuario=perfil,
                    especialidad=datos["especialidad"],
                    cedula_profesional=datos[
                        "cedula_profesional"
                    ],
                    descripcion=datos["descripcion"],
                )

        except IntegrityError:
            formulario.add_error(
                None,
                "No se pudo crear la cuenta. "
                "Verifica usuario y correo.",
            )

        else:
            messages.success(
                request,
                "Fisioterapeuta registrado correctamente.",
            )

            return redirect(
                "fisioterapeutas:detalle_fisioterapeuta",
                fisioterapeuta_id=profesional.pk,
            )

    return render(
        request,
        "fisioterapeutas/registrar_fisioterapeuta.html",
        {
            "form": formulario,
        },
    )


# DETALLE

@login_required
def detalle_fisioterapeuta(request, fisioterapeuta_id):
    rol = rol_actual(request)

    profesional = get_object_or_404(
        profesionales_visibles(request),
        pk=fisioterapeuta_id,
    )

    es_propio = (
        not request.user.is_superuser
        and getattr(request.user, "perfil", None)
        == profesional.usuario
    )

    return render(
        request,
        "fisioterapeutas/detalle_fisioterapeuta.html",
        {
            "fisioterapeuta": profesional,
            "puede_gestionar": rol in GESTION,
            "puede_desactivar": (
                rol == PerfilUsuario.Rol.ADMINISTRADOR
            ),
            "ver_contacto": (
                rol in GESTION or es_propio
            ),
        },
    )


# EDITAR

@login_required
def editar_fisioterapeuta(request, fisioterapeuta_id):
    if rol_actual(request) not in GESTION:
        raise PermissionDenied

    profesional = get_object_or_404(
        Fisioterapeuta.objects.select_related(
            "usuario__usuario"
        ),
        pk=fisioterapeuta_id,
    )

    usuario = profesional.usuario.usuario

    inicial = {
        "nombre": usuario.first_name,
        "apellidos": usuario.last_name,
        "email": usuario.email,
        "telefono": profesional.usuario.telefono,
        "especialidad": profesional.especialidad,
        "cedula_profesional": profesional.cedula_profesional,
        "descripcion": profesional.descripcion,
    }

    formulario = EditarFisioterapeutaForm(
        request.POST if request.method == "POST" else None,
        initial=inicial,
        usuario_actual=usuario,
        fisioterapeuta_actual=profesional,
    )

    if (
        request.method == "POST"
        and formulario.is_valid()
    ):
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

            profesional.usuario.telefono = datos["telefono"]

            profesional.usuario.save(
                update_fields=[
                    "telefono",
                    "fecha_actualizacion",
                ]
            )

            profesional.especialidad = datos["especialidad"]

            profesional.cedula_profesional = datos[
                "cedula_profesional"
            ]

            profesional.descripcion = datos["descripcion"]

            profesional.save(
                update_fields=[
                    "especialidad",
                    "cedula_profesional",
                    "descripcion",
                    "fecha_actualizacion",
                ]
            )

        messages.success(
            request,
            "Fisioterapeuta actualizado correctamente.",
        )

        return redirect(
            "fisioterapeutas:detalle_fisioterapeuta",
            fisioterapeuta_id=profesional.pk,
        )

    return render(
        request,
        "fisioterapeutas/editar_fisioterapeuta.html",
        {
            "form": formulario,
            "fisioterapeuta": profesional,
        },
    )


# CONSULTAR HORARIOS

@login_required
def horario_fisioterapeuta(request, fisioterapeuta_id):
    profesional = get_object_or_404(
        profesionales_visibles(request),
        pk=fisioterapeuta_id,
    )

    horarios = profesional.horarios.order_by(
        "dia_semana",
        "hora_inicio",
    )

    if rol_actual(request) not in GESTION:
        horarios = horarios.filter(activo=True)

    return render(
        request,
        "fisioterapeutas/horario_fisioterapeuta.html",
        {
            "fisioterapeuta": profesional,
            "horarios": horarios,
        },
    )


# DESACTIVAR O REACTIVAR

@login_required
@require_POST
def cambiar_estado_fisioterapeuta(
    request,
    fisioterapeuta_id,
):
    if rol_actual(request) != (
        PerfilUsuario.Rol.ADMINISTRADOR
    ):
        raise PermissionDenied

    with transaction.atomic():

        profesional = get_object_or_404(
            Fisioterapeuta.objects.select_related(
                "usuario__usuario"
            ).select_for_update(),
            pk=fisioterapeuta_id,
        )

        activar = not profesional.activo

        if not activar:
            tiene_pendientes = profesional.citas.filter(
                Q(
                    estado=Cita.Estado.EN_PROCESO
                )
                | Q(
                    estado__in=[
                        Cita.Estado.PROGRAMADA,
                        Cita.Estado.CONFIRMADA,
                    ],
                    fecha__gte=timezone.localdate(),
                )
            ).exists()

            if tiene_pendientes:
                messages.error(
                    request,
                    "No se puede desactivar: "
                    "tiene citas activas o futuras.",
                )

                return redirect(
                    "fisioterapeutas:detalle_fisioterapeuta",
                    fisioterapeuta_id=profesional.pk,
                )

        profesional.activo = activar

        profesional.save(
            update_fields=[
                "activo",
                "fecha_actualizacion",
            ]
        )

        perfil = profesional.usuario
        perfil.activo = activar

        perfil.save(
            update_fields=[
                "activo",
                "fecha_actualizacion",
            ]
        )

        usuario = perfil.usuario
        usuario.is_active = activar

        usuario.save(
            update_fields=["is_active"]
        )

    messages.success(
        request,
        (
            "Fisioterapeuta activado."
            if activar
            else "Fisioterapeuta desactivado "
                 "sin borrar su historial."
        ),
    )

    return redirect(
        "fisioterapeutas:detalle_fisioterapeuta",
        fisioterapeuta_id=profesional.pk,
    )
