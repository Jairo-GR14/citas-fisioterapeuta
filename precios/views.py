
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from usuarios.decorators import rol_requerido

from .forms import ServicioForm
from .models import Servicio


def es_administrador(usuario):

    if usuario.is_superuser:
        return True

    perfil = getattr(usuario, "perfil", None)

    return bool(
        perfil
        and perfil.activo
        and perfil.rol == "ADMINISTRADOR"
    )


# LISTAR SERVICIOS Y PRECIOS

@login_required
def lista_precios(request):

    puede_gestionar = es_administrador(
        request.user
    )

    servicios = Servicio.objects.all()

    # Los usuarios normales solo ven servicios activos.
    if not puede_gestionar:
        servicios = servicios.filter(activo=True)

    buscar = request.GET.get(
        "buscar",
        ""
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
            "servicios": servicios.order_by("nombre"),
            "buscar": buscar,
            "puede_gestionar": puede_gestionar,
        },
    )


# REGISTRAR SERVICIO

@rol_requerido(["ADMINISTRADOR"])
def registrar_precio(request):

    if request.method == "POST":
        formulario = ServicioForm(request.POST)

        if formulario.is_valid():

            formulario.save()

            messages.success(
                request,
                "El servicio se registró correctamente."
            )

            return redirect(
                "precios:lista_precios"
            )

    else:
        formulario = ServicioForm(
            initial={"activo": True}
        )

    return render(
        request,
        "precios/registrar_precio.html",
        {
            "form": formulario,
        },
    )


# EDITAR SERVICIO

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
                "El servicio se actualizó correctamente."
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
