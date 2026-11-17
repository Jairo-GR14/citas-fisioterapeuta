
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from usuarios.decorators import rol_requerido
from usuarios.models import PerfilUsuario

from .forms import ServicioForm
from .models import Servicio


# =========================================================
# VERIFICAR ADMINISTRADOR Y CUENTA ACTIVA
# =========================================================

def es_administrador(usuario):
    """
    Comprueba los permisos del usuario.

    - Bloquea cuentas desactivadas.
    - Bloquea perfiles desactivados, incluidos superusuarios.
    - Permite superusuarios activos sin perfil.
    - Los usuarios normales necesitan un perfil activo.
    """

    if not usuario.is_authenticated or not usuario.is_active:
        raise PermissionDenied(
            "Tu cuenta no está activa."
        )

    perfil = getattr(
        usuario,
        "perfil",
        None,
    )

    # Bloquear perfiles desactivados,
    # incluso cuando el usuario es superusuario.
    if perfil is not None and not perfil.activo:
        raise PermissionDenied(
            "Tu perfil está desactivado."
        )

    # Permitir superusuarios activos.
    if usuario.is_superuser:
        return True

    # Los usuarios normales necesitan un perfil.
    if perfil is None:
        raise PermissionDenied(
            "Tu usuario no tiene un perfil asignado."
        )

    return (
        perfil.rol == PerfilUsuario.Rol.ADMINISTRADOR
    )


# =========================================================
# LISTAR SERVICIOS Y PRECIOS
# =========================================================

@login_required
def lista_precios(request):

    puede_gestionar = es_administrador(
        request.user
    )

    servicios = Servicio.objects.all()

    # Los usuarios que no son administradores
    # solamente pueden consultar servicios activos.
    if not puede_gestionar:
        servicios = servicios.filter(
            activo=True
        )

    buscar = request.GET.get(
        "buscar",
        "",
    ).strip()

    if buscar:

        servicios = servicios.filter(
            Q(nombre__icontains=buscar)
            | Q(descripcion__icontains=buscar)
        )

    return render(
        request,
        "precios/lista_precios.html",
        {
            "servicios": servicios.order_by(
                "nombre"
            ),
            "buscar": buscar,
            "puede_gestionar": puede_gestionar,
        },
    )


# =========================================================
# REGISTRAR SERVICIO
# =========================================================

@rol_requerido(["ADMINISTRADOR"])
def registrar_precio(request):

    if request.method == "POST":

        formulario = ServicioForm(
            request.POST
        )

        if formulario.is_valid():

            formulario.save()

            messages.success(
                request,
                "El servicio se registró correctamente.",
            )

            return redirect(
                "precios:lista_precios"
            )

    else:

        formulario = ServicioForm(
            initial={
                "activo": True,
            }
        )

    return render(
        request,
        "precios/registrar_precio.html",
        {
            "form": formulario,
        },
    )


# =========================================================
# EDITAR SERVICIO Y PRECIO
# =========================================================

@rol_requerido(["ADMINISTRADOR"])
def editar_precio(request, servicio_id):

    servicio = get_object_or_404(
        Servicio,
        pk=servicio_id,
    )

    if request.method == "POST":

        formulario = ServicioForm(
            request.POST,
            instance=servicio,
        )

        if formulario.is_valid():

            formulario.save()

            messages.success(
                request,
                "El servicio se actualizó correctamente.",
            )

            return redirect(
                "precios:lista_precios"
            )

    else:

        formulario = ServicioForm(
            instance=servicio
        )

    return render(
        request,
        "precios/editar_precio.html",
        {
            "form": formulario,
            "servicio": servicio,
        },
    )
