
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.utils.dateparse import parse_date

from .views import obtener_citas_permitidas


COLORES_ESTADO = {
    "PROGRAMADA": "#2563eb",
    "CONFIRMADA": "#059669",
    "EN_PROCESO": "#d97706",
    "FINALIZADA": "#64748b",
    "CANCELADA": "#dc2626",
}


@login_required
def eventos_calendario(request):
    """
    Devuelve las citas visibles para el usuario
    dentro del intervalo solicitado por FullCalendar.
    """

    inicio_texto = request.GET.get("start", "")
    fin_texto = request.GET.get("end", "")

    # FullCalendar envía fechas ISO 8601.
    try:
        inicio = parse_date(inicio_texto[:10])
        fin = parse_date(fin_texto[:10])

    except (ValueError, TypeError):
        inicio = None
        fin = None

    if (
        inicio is None
        or fin is None
        or fin <= inicio
        or (fin - inicio).days > 62
    ):
        return JsonResponse(
            {
                "error": (
                    "El intervalo solicitado no es válido."
                )
            },
            status=400,
        )

    # Conserva la seguridad por roles:
    # Administrador y Recepcionista: todas.
    # Fisioterapeuta: solamente las suyas.
    # Paciente: solamente las suyas.
    citas = (
        obtener_citas_permitidas(request.user)
        .filter(
            fecha__gte=inicio,
            fecha__lt=fin,
        )
        .order_by("fecha", "hora", "pk")
    )

    eventos = []

    for cita in citas:

        inicio_cita = datetime.combine(
            cita.fecha,
            cita.hora,
        )

        duracion = cita.duracion_minutos or 60

        fin_cita = inicio_cita + timedelta(
            minutes=duracion
        )

        usuario_paciente = (
            cita.paciente.usuario.usuario
        )

        usuario_fisioterapeuta = (
            cita.fisioterapeuta.usuario.usuario
        )

        nombre_paciente = (
            usuario_paciente.get_full_name().strip()
            or usuario_paciente.username
        )

        nombre_fisioterapeuta = (
            usuario_fisioterapeuta.get_full_name().strip()
            or usuario_fisioterapeuta.username
        )

        color = COLORES_ESTADO.get(
            cita.estado,
            "#475569",
        )

        eventos.append(
            {
                "id": str(cita.pk),

                "title": (
                    f"{nombre_paciente} · "
                    f"{cita.servicio.nombre}"
                ),

                # Horario local de la clínica.
                "start": inicio_cita.isoformat(
                    timespec="minutes"
                ),

                "end": fin_cita.isoformat(
                    timespec="minutes"
                ),

                "url": reverse(
                    "citas:detalle_cita",
                    args=[cita.pk],
                ),

                "backgroundColor": color,
                "borderColor": color,
                "textColor": "#ffffff",

                "extendedProps": {
                    "estado": cita.get_estado_display(),
                    "paciente": nombre_paciente,
                    "fisioterapeuta": nombre_fisioterapeuta,
                    "servicio": cita.servicio.nombre,
                    "duracion_minutos": duracion,
                },
            }
        )

    return JsonResponse(
        eventos,
        safe=False,
    )
