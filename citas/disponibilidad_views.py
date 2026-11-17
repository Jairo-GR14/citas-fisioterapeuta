
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_date

from fisioterapeutas.models import (
    Fisioterapeuta,
    HorarioDisponible,
)
from precios.models import Servicio

from .models import Cita
from .views import ROLES_AGENDAR, exigir_rol


def identificador_valido(valor):
    return (
        bool(valor)
        and valor.isascii()
        and valor.isdecimal()
        and len(valor) <= 18
        and int(valor) > 0
    )


def convertir_fecha(valor):
    try:
        return parse_date(valor) if valor else None
    except ValueError:
        return None


def fisioterapeutas_activos():
    return Fisioterapeuta.objects.filter(
        activo=True,
        usuario__activo=True,
        usuario__usuario__is_active=True,
    ).select_related("usuario__usuario")


def construir_horarios_disponibles(
    fisioterapeuta,
    fecha,
    duracion_minutos,
):
    """
    Devuelve los horarios posibles de una fecha.

    Considera:
    - Jornada del fisioterapeuta.
    - Duración del servicio seleccionado.
    - Duración real de las citas existentes.
    - Citas canceladas.
    - Horarios pasados.

    Temporalmente se conservan inicios cada
    60 minutos, compatibles con CitaForm.
    """

    jornadas = HorarioDisponible.objects.filter(
        fisioterapeuta=fisioterapeuta,
        dia_semana=fecha.isoweekday(),
        activo=True,
    ).order_by("hora_inicio")

    citas = list(
        Cita.objects.filter(
            fisioterapeuta=fisioterapeuta,
            fecha=fecha,
        ).exclude(
            estado=Cita.Estado.CANCELADA
        )
    )

    zona = timezone.get_current_timezone()
    ahora = timezone.now()

    ocupados = []

    for cita in citas:
        inicio_ocupado = timezone.make_aware(
            datetime.combine(
                cita.fecha,
                cita.hora,
            ),
            zona,
        )

        fin_ocupado = (
            inicio_ocupado
            + timedelta(
                minutes=cita.duracion_minutos
            )
        )

        ocupados.append(
            (inicio_ocupado, fin_ocupado)
        )

    horarios = []
    vistos = set()

    for jornada in jornadas:

        cursor = datetime.combine(
            fecha,
            jornada.hora_inicio,
        )

        fin_jornada = timezone.make_aware(
            datetime.combine(
                fecha,
                jornada.hora_fin,
            ),
            zona,
        )

        while True:

            inicio = timezone.make_aware(
                cursor,
                zona,
            )

            fin = inicio + timedelta(
                minutes=duracion_minutos
            )

            # La sesión debe caber completa
            # dentro de la jornada.
            if fin > fin_jornada:
                break

            hora_texto = cursor.strftime(
                "%H:%M"
            )

            if hora_texto not in vistos:

                vistos.add(hora_texto)

                ocupado = any(
                    inicio < fin_ocupado
                    and inicio_ocupado < fin
                    for (
                        inicio_ocupado,
                        fin_ocupado,
                    ) in ocupados
                )

                horarios.append(
                    {
                        "hora": hora_texto,
                        "fin": timezone.localtime(
                            fin,
                            zona,
                        ).strftime("%H:%M"),
                        "disponible": (
                            inicio > ahora
                            and not ocupado
                        ),
                    }
                )

            # Mismo intervalo de inicio que
            # acepta actualmente CitaForm.
            cursor += timedelta(hours=1)

    horarios.sort(
        key=lambda item: item["hora"]
    )

    return horarios


@login_required
def horarios_disponibles(request):
    """
    Conserva la pantalla independiente de
    consultar horarios y su compatibilidad
    con las pruebas existentes.
    """

    exigir_rol(
        request.user,
        ROLES_AGENDAR,
    )

    fisioterapeutas = fisioterapeutas_activos()

    servicios = Servicio.objects.filter(
        activo=True
    ).order_by("nombre")

    fisioterapeuta_id = request.GET.get(
        "fisioterapeuta", ""
    ).strip()

    servicio_id = request.GET.get(
        "servicio", ""
    ).strip()

    fecha_str = request.GET.get(
        "fecha", ""
    ).strip()

    fecha = convertir_fecha(fecha_str)

    fisioterapeuta = None
    servicio = None
    horarios = []
    error = ""

    # Compatibilidad con pruebas y consultas
    # anteriores que no seleccionan servicio.
    duracion = 60

    if servicio_id:

        if identificador_valido(servicio_id):
            servicio = servicios.filter(
                pk=servicio_id
            ).first()

        if servicio is None:
            error = (
                "Selecciona un servicio activo "
                "y válido."
            )
        else:
            duracion = servicio.duracion_minutos

    if fisioterapeuta_id or fecha_str:

        if (
            not identificador_valido(
                fisioterapeuta_id
            )
            or fecha is None
        ):
            error = error or (
                "Selecciona un fisioterapeuta "
                "y una fecha válida."
            )

        else:

            fisioterapeuta = (
                fisioterapeutas.filter(
                    pk=fisioterapeuta_id
                ).first()
            )

            if fisioterapeuta is None:
                error = error or (
                    "El fisioterapeuta seleccionado "
                    "no está disponible."
                )

            elif fecha < timezone.localdate():
                error = error or (
                    "No puedes consultar fechas pasadas."
                )

            elif not error:

                horarios = construir_horarios_disponibles(
                    fisioterapeuta=fisioterapeuta,
                    fecha=fecha,
                    duracion_minutos=duracion,
                )

    return render(
        request,
        "citas/horarios_disponibles.html",
        {
            "fisioterapeutas": fisioterapeutas,
            "fisioterapeuta": fisioterapeuta,
            "fisioterapeuta_id": fisioterapeuta_id,
            "servicios": servicios,
            "servicio": servicio,
            "servicio_id": servicio_id,
            "duracion_minutos": duracion,
            "fecha": fecha_str,
            "horarios": horarios,
            "hay_disponibles": any(
                item["disponible"]
                for item in horarios
            ),
            "error": error,
        },
    )


@login_required
def horarios_disponibles_json(request):
    """
    API utilizada por la pantalla Agendar cita.

    Devuelve los horarios disponibles como JSON
    sin recargar la página.
    """

    exigir_rol(
        request.user,
        ROLES_AGENDAR,
    )

    servicio_id = request.GET.get(
        "servicio", ""
    ).strip()

    fisioterapeuta_id = request.GET.get(
        "fisioterapeuta", ""
    ).strip()

    fecha_str = request.GET.get(
        "fecha", ""
    ).strip()

    if not (
        identificador_valido(servicio_id)
        and identificador_valido(fisioterapeuta_id)
        and fecha_str
    ):
        return JsonResponse(
            {
                "ok": False,
                "error": (
                    "Selecciona un servicio, "
                    "fisioterapeuta y fecha válidos."
                ),
            },
            status=400,
        )

    fecha = convertir_fecha(fecha_str)

    if fecha is None:
        return JsonResponse(
            {
                "ok": False,
                "error": "La fecha no es válida.",
            },
            status=400,
        )

    if fecha < timezone.localdate():
        return JsonResponse(
            {
                "ok": False,
                "error": (
                    "No puedes reservar citas "
                    "en fechas pasadas."
                ),
            },
            status=400,
        )

    servicio = Servicio.objects.filter(
        pk=servicio_id,
        activo=True,
    ).first()

    if servicio is None:
        return JsonResponse(
            {
                "ok": False,
                "error": (
                    "El servicio seleccionado "
                    "no está disponible."
                ),
            },
            status=404,
        )

    fisioterapeuta = (
        fisioterapeutas_activos().filter(
            pk=fisioterapeuta_id
        ).first()
    )

    if fisioterapeuta is None:
        return JsonResponse(
            {
                "ok": False,
                "error": (
                    "El fisioterapeuta seleccionado "
                    "no está disponible."
                ),
            },
            status=404,
        )

    duracion = servicio.duracion_minutos

    horarios = construir_horarios_disponibles(
        fisioterapeuta=fisioterapeuta,
        fecha=fecha,
        duracion_minutos=duracion,
    )

    nombre_fisioterapeuta = (
        fisioterapeuta.usuario.usuario.get_full_name()
        or fisioterapeuta.usuario.usuario.username
    )

    return JsonResponse(
        {
            "ok": True,
            "servicio": servicio.nombre,
            "fisioterapeuta": nombre_fisioterapeuta,
            "fecha": fecha.isoformat(),
            "duracion_minutos": duracion,
            "horarios": [
                {
                    "hora": item["hora"],
                    "hora_fin": item["fin"],
                    "disponible": item["disponible"],
                }
                for item in horarios
            ],
            "hay_disponibles": any(
                item["disponible"]
                for item in horarios
            ),
        }
    )
