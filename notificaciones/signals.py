
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from citas.models import Cita

from .servicios import notificar_evento_cita


# DETECTAR CAMBIOS EN UNA CITA

@receiver(pre_save, sender=Cita)
def detectar_cambio_de_cita(sender, instance, **kwargs):

    instance._evento_para_notificar = None
    instance._fisio_anterior_para_notificar = None

    if kwargs.get("raw") or not instance.pk:
        return

    anterior = sender.objects.filter(
        pk=instance.pk
    ).values(
        "estado",
        "fecha",
        "hora",
        "fisioterapeuta_id",
        "servicio_id",
    ).first()

    if anterior is None:
        return

    instance._fisio_anterior_para_notificar = (
        anterior["fisioterapeuta_id"]
    )

    # CAMBIO DE ESTADO
    if anterior["estado"] != instance.estado:

        instance._evento_para_notificar = {
            Cita.Estado.CONFIRMADA: "CONFIRMADA",
            Cita.Estado.CANCELADA: "CANCELADA",
            Cita.Estado.EN_PROCESO: "EN_PROCESO",
            Cita.Estado.FINALIZADA: "FINALIZADA",
        }.get(
            instance.estado,
            "REPROGRAMADA",
        )

    # CAMBIO DE HORARIO, PROFESIONAL O SERVICIO
    elif any((
        anterior["fecha"] != instance.fecha,
        anterior["hora"] != instance.hora,
        anterior["fisioterapeuta_id"]
        != instance.fisioterapeuta_id,
        anterior["servicio_id"]
        != instance.servicio_id,
    )):

        instance._evento_para_notificar = (
            "REPROGRAMADA"
        )


# GENERAR NOTIFICACIONES DESPUÉS DE GUARDAR

@receiver(post_save, sender=Cita)
def crear_notificacion_cita(
    sender,
    instance,
    created,
    **kwargs,
):

    if kwargs.get("raw"):
        return

    if created:
        evento = "PROGRAMADA"

    else:
        evento = getattr(
            instance,
            "_evento_para_notificar",
            None,
        )

    if not evento:
        return

    cita_id = instance.pk

    fisio_anterior_id = getattr(
        instance,
        "_fisio_anterior_para_notificar",
        None,
    )

    # Esperar a que la transacción se confirme.
    transaction.on_commit(
        lambda: notificar_evento_cita(
            cita_id,
            evento,
            fisio_anterior_id,
        ),
        robust=True,
    )
