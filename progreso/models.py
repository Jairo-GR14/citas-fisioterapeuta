from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Progreso(models.Model):
    consulta = models.OneToOneField(
        "consultas.Consulta",
        on_delete=models.CASCADE,
        related_name="progreso",
    )

    movilidad = models.TextField(
        blank=True,
    )

    nivel_dolor = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(10),
        ],
    )

    ejercicios_realizados = models.TextField(
        blank=True,
    )

    avances = models.TextField(
        blank=True,
    )

    observaciones = models.TextField(
        blank=True,
    )

    recomendaciones = models.TextField(
        blank=True,
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"Progreso - {self.consulta}"