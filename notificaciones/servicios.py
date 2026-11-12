
from citas.models import Cita
from fisioterapeutas.models import Fisioterapeuta

from .models import Notificacion


TITULOS = {
    "PROGRAMADA": "Nueva cita programada",
    "CONFIRMADA": "Cita confirmada",
    "REPROGRAMADA": "Cita modificada",
    "CANCELADA": "Cita cancelada",
    "EN_PROCESO": "Consulta iniciada",
    "FINALIZADA": "Consulta finalizada",
}


def notificar_evento_cita(
    cita_id,
    evento,
    fisio_anterior_id=None,
):
    """
    Crea notificaciones internas para el paciente
    y el fisioterapeuta de una cita.
    """

    cita = Cita.objects.select_related(
        "paciente__usuario",
        "fisioterapeuta__usuario",
        "servicio",
    ).filter(
        pk=cita_id
    ).first()

    if cita is None or evento not in TITULOS:
        return

    # Eliminar recordatorios pendientes que
    # ya no sean válidos.
    if evento in ("REPROGRAMADA", "CANCELADA"):

        Notificacion.objects.filter(
            tipo=Notificacion.Tipo.RECORDATORIO,
            titulo=f"Recordatorio de la cita #{cita.pk}",
            leida=False,
        ).delete()

    fecha = cita.fecha.strftime("%d/%m/%Y")
    hora = cita.hora.strftime("%H:%M")

    mensaje = (
        f"La cita #{cita.pk} "
        f"({cita.servicio.nombre}) "
        f"para el {fecha} a las {hora} "
        f"tiene el estado: {cita.get_estado_display()}."
    )

    # Notificar al paciente y al fisioterapeuta.
    destinatarios = {
        cita.paciente.usuario_id,
        cita.fisioterapeuta.usuario_id,
    }

    for perfil_id in destinatarios:

        Notificacion.objects.create(
            usuario_id=perfil_id,
            tipo=Notificacion.Tipo.CITA,
            titulo=TITULOS[evento],
            mensaje=mensaje,
        )

    # Si hubo cambio de fisioterapeuta,
    # avisar también al profesional anterior.
    if (
        fisio_anterior_id
        and fisio_anterior_id != cita.fisioterapeuta_id
    ):

        anterior_perfil_id = (
            Fisioterapeuta.objects.filter(
                pk=fisio_anterior_id
            ).values_list(
                "usuario_id",
                flat=True,
            ).first()
        )

        if (
            anterior_perfil_id
            and anterior_perfil_id not in destinatarios
        ):

            Notificacion.objects.create(
                usuario_id=anterior_perfil_id,
                tipo=Notificacion.Tipo.CITA,
                titulo="Cita reasignada",
                mensaje=(
                    f"La cita #{cita.pk} ya no está "
                    "asignada a tu agenda."
                ),
            )
