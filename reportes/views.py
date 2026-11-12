"""Reportes administrativos basados en los registros del sistema."""
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Max, Q, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils.dateparse import parse_date

from citas.models import Cita
from fisioterapeutas.models import Fisioterapeuta
from pacientes.models import Paciente
from precios.models import Servicio
from usuarios.decorators import rol_requerido


CERO = Decimal("0.00")


def _fecha_valida(valor):
    try:
        return parse_date(valor) if valor else None
    except ValueError:
        return None


def _filtrar_fechas(queryset, request):
    inicio = _fecha_valida(request.GET.get("fecha_inicio", ""))
    fin = _fecha_valida(request.GET.get("fecha_fin", ""))
    if inicio:
        queryset = queryset.filter(fecha__gte=inicio)
    if fin:
        queryset = queryset.filter(fecha__lte=fin)
    return queryset


@login_required
@rol_requerido(["ADMINISTRADOR"])
def reportes(request):
    """Portada de reportes: importes finales, no pagos comprobados."""
    citas_finalizadas = Cita.objects.filter(
        estado=Cita.Estado.FINALIZADA,
        costo_final__isnull=False,
    )
    total_ingresos = (
        citas_finalizadas.aggregate(total=Sum("costo_final"))["total"]
        or CERO
    )
    return render(request, "reportes/reportes.html", {
        "total_citas": Cita.objects.count(),
        "total_pacientes": Paciente.objects.count(),
        "total_fisioterapeutas": Fisioterapeuta.objects.count(),
        "total_ingresos": total_ingresos,
    })


@login_required
@rol_requerido(["ADMINISTRADOR"])
def reporte_citas(request):
    citas = Cita.objects.select_related(
        "paciente__usuario__usuario",
        "fisioterapeuta__usuario__usuario",
        "motivo", "servicio",
    )
    citas = _filtrar_fechas(citas, request)

    buscar = request.GET.get("buscar", "").strip()
    if buscar:
        citas = citas.filter(
            Q(paciente__usuario__usuario__first_name__icontains=buscar)
            | Q(paciente__usuario__usuario__last_name__icontains=buscar)
            | Q(paciente__usuario__usuario__username__icontains=buscar)
            | Q(fisioterapeuta__usuario__usuario__first_name__icontains=buscar)
            | Q(fisioterapeuta__usuario__usuario__last_name__icontains=buscar)
            | Q(fisioterapeuta__usuario__usuario__username__icontains=buscar)
        )

    estado = request.GET.get("estado", "").strip().upper()
    estados_validos = {valor for valor, _ in Cita.Estado.choices}
    if estado in estados_validos:
        citas = citas.filter(estado=estado)

    resumen = citas.aggregate(
        total=Count("id"),
        programadas=Count("id", filter=Q(estado=Cita.Estado.PROGRAMADA)),
        confirmadas=Count("id", filter=Q(estado=Cita.Estado.CONFIRMADA)),
        en_proceso=Count("id", filter=Q(estado=Cita.Estado.EN_PROCESO)),
        finalizadas=Count("id", filter=Q(estado=Cita.Estado.FINALIZADA)),
        canceladas=Count("id", filter=Q(estado=Cita.Estado.CANCELADA)),
    )
    citas_por_mes = (
        citas.order_by()
        .annotate(mes=TruncMonth("fecha"))
        .values("mes")
        .annotate(cantidad=Count("id"))
        .order_by("-mes")
    )
    return render(request, "reportes/reporte_citas.html", {
        "citas": citas.order_by("-fecha", "-hora"),
        "total_citas": resumen["total"],
        "citas_programadas": resumen["programadas"],
        "citas_confirmadas": resumen["confirmadas"],
        "citas_en_proceso": resumen["en_proceso"],
        "citas_finalizadas": resumen["finalizadas"],
        "citas_canceladas": resumen["canceladas"],
        "citas_por_mes": citas_por_mes,
        "estados": Cita.Estado.choices,
        "estado_elegido": estado,
    })


@login_required
@rol_requerido(["ADMINISTRADOR"])
def reporte_pacientes(request):
    pacientes = Paciente.objects.select_related("usuario__usuario").annotate(
        total_citas=Count("citas", distinct=True),
        ultima_cita=Max("citas__fecha"),
        total_tratamientos=Count(
            "citas__consulta__tratamientos", distinct=True,
        ),
        tratamientos_activos=Count(
            "citas__consulta__tratamientos",
            filter=Q(citas__consulta__tratamientos__activo=True),
            distinct=True,
        ),
    )
    buscar = request.GET.get("buscar", "").strip()
    if buscar:
        pacientes = pacientes.filter(
            Q(usuario__usuario__first_name__icontains=buscar)
            | Q(usuario__usuario__last_name__icontains=buscar)
            | Q(usuario__usuario__username__icontains=buscar)
            | Q(usuario__usuario__email__icontains=buscar)
        )
    pacientes = list(pacientes.order_by(
        "usuario__usuario__first_name", "usuario__usuario__last_name",
    ))
    return render(request, "reportes/reporte_pacientes.html", {
        "pacientes": pacientes,
        "total_pacientes": len(pacientes),
        "pacientes_con_citas": sum(bool(p.total_citas) for p in pacientes),
        "pacientes_en_tratamiento": sum(
            bool(p.tratamientos_activos) for p in pacientes
        ),
    })


@login_required
@rol_requerido(["ADMINISTRADOR"])
def reporte_fisioterapeutas(request):
    fisioterapeutas = Fisioterapeuta.objects.select_related(
        "usuario__usuario"
    ).annotate(
        total_citas=Count("citas", distinct=True),
        citas_finalizadas=Count(
            "citas", filter=Q(citas__estado=Cita.Estado.FINALIZADA),
            distinct=True,
        ),
        citas_en_proceso=Count(
            "citas", filter=Q(citas__estado=Cita.Estado.EN_PROCESO),
            distinct=True,
        ),
    )
    buscar = request.GET.get("buscar", "").strip()
    if buscar:
        fisioterapeutas = fisioterapeutas.filter(
            Q(usuario__usuario__first_name__icontains=buscar)
            | Q(usuario__usuario__last_name__icontains=buscar)
            | Q(usuario__usuario__username__icontains=buscar)
            | Q(usuario__usuario__email__icontains=buscar)
        )
    fisioterapeutas = list(fisioterapeutas.order_by(
        "usuario__usuario__first_name", "usuario__usuario__last_name",
    ))
    return render(request, "reportes/reporte_fisioterapeutas.html", {
        "fisioterapeutas": fisioterapeutas,
        "total_fisioterapeutas": len(fisioterapeutas),
        "total_citas_asignadas": sum(f.total_citas for f in fisioterapeutas),
        "total_citas_finalizadas": sum(
            f.citas_finalizadas for f in fisioterapeutas
        ),
    })


@login_required
@rol_requerido(["ADMINISTRADOR"])
def reporte_ingresos(request):
    # Un costo_final registrado no prueba que se haya recibido el pago.
    citas = Cita.objects.filter(
        estado=Cita.Estado.FINALIZADA,
        costo_final__isnull=False,
    )
    citas = _filtrar_fechas(citas, request)

    tipo_servicio = request.GET.get("tipo_servicio", "").strip()
    if tipo_servicio.isdecimal():
        citas = citas.filter(servicio_id=int(tipo_servicio))

    resumen = citas.aggregate(
        total=Sum("costo_final"),
        cantidad=Count("id"),
        promedio=Avg("costo_final"),
    )
    ingresos = (
        citas.order_by()
        .values("servicio_id", "servicio__nombre")
        .annotate(
            cantidad=Count("id"),
            precio=Avg("costo_final"),
            total=Sum("costo_final"),
        )
        .order_by("servicio__nombre")
    )
    for ingreso in ingresos:
        ingreso["nombre_servicio"] = ingreso["servicio__nombre"]

    ingresos_por_mes = (
        citas.order_by()
        .annotate(mes=TruncMonth("fecha"))
        .values("mes")
        .annotate(cantidad=Count("id"), total=Sum("costo_final"))
        .order_by("-mes")
    )
    return render(request, "reportes/reporte_ingresos.html", {
        "ingresos": ingresos,
        "total_ingresos": resumen["total"] or CERO,
        "total_servicios": resumen["cantidad"],
        "ingreso_promedio": resumen["promedio"] or CERO,
        "servicios": Servicio.objects.all().order_by("nombre"),
        "tipo_servicio_elegido": tipo_servicio,
        "ingresos_por_mes": ingresos_por_mes,
    })
