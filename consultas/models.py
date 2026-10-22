from django.db import models


class Consulta(models.Model):
    cita = models.OneToOneField(
        "citas.Cita",
        on_delete=models.PROTECT,
        related_name="consulta",
    )

    valoracion_inicial = models.TextField(
        blank=True,
    )

    diagnostico = models.TextField(
        blank=True,
    )

    informacion_atencion = models.TextField(
        blank=True,
    )

    observaciones = models.TextField(
        blank=True,
    )

    fecha_inicio = models.DateTimeField(
        null=True,
        blank=True,
    )

    fecha_finalizacion = models.DateTimeField(
        null=True,
        blank=True,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"Consulta - {self.cita}"