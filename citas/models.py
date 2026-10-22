from django.db import models
from django.db.models import Q


class MotivoConsulta(models.Model):
    nombre = models.CharField(
        max_length=150,
        unique=True,
    )

    descripcion = models.TextField(
        blank=True,
    )

    activo = models.BooleanField(
        default=True,
    )

    def __str__(self):
        return self.nombre


class Cita(models.Model):

    class Estado(models.TextChoices):
        PROGRAMADA = "PROGRAMADA", "Programada"
        CONFIRMADA = "CONFIRMADA", "Confirmada"
        EN_PROCESO = "EN_PROCESO", "En proceso"
        FINALIZADA = "FINALIZADA", "Finalizada"
        CANCELADA = "CANCELADA", "Cancelada"

    paciente = models.ForeignKey(
        "pacientes.Paciente",
        on_delete=models.PROTECT,
        related_name="citas",
    )

    fisioterapeuta = models.ForeignKey(
        "fisioterapeutas.Fisioterapeuta",
        on_delete=models.PROTECT,
        related_name="citas",
    )

    servicio = models.ForeignKey(
        "precios.Servicio",
        on_delete=models.PROTECT,
        related_name="citas",
    )

    motivo = models.ForeignKey(
        MotivoConsulta,
        on_delete=models.PROTECT,
        related_name="citas",
    )

    fecha = models.DateField()

    hora = models.TimeField()

    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PROGRAMADA,
    )

    costo_estimado = models.DecimalField(
        max_digits=8,
        decimal_places=2,
    )

    costo_final = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )

    observaciones = models.TextField(
        blank=True,
    )

    motivo_cancelacion = models.TextField(
        blank=True,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["fecha", "hora"]

        constraints = [
            models.UniqueConstraint(
                fields=["fisioterapeuta", "fecha", "hora"],
                condition=~Q(estado="CANCELADA"),
                name="cita_unica_fisioterapeuta_horario",
            )
        ]

    def __str__(self):
        return f"{self.paciente} - {self.fecha} {self.hora}"