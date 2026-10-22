from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Calificacion(models.Model):
    cita = models.OneToOneField(
        "citas.Cita",
        on_delete=models.CASCADE,
        related_name="calificacion",
    )

    puntuacion = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
    )

    comentario = models.TextField(
        blank=True,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.puntuacion}/5 - {self.cita}"