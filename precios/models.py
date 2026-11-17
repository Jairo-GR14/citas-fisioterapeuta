
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models


class Servicio(models.Model):

    nombre = models.CharField(
        max_length=100,
        unique=True,
    )

    descripcion = models.TextField(
        blank=True,
    )

    precio_base = models.DecimalField(
        max_digits=8,
        decimal_places=2,
    )

    # Duración estimada de cada sesión del servicio.
    # Los servicios actuales conservarán 60 minutos
    # como valor inicial al ejecutar la migración.
    duracion_minutos = models.PositiveSmallIntegerField(
        default=60,
        validators=[
            MinValueValidator(15),
            MaxValueValidator(480),
        ],
        help_text=(
            "Duración estimada de una sesión, "
            "en minutos."
        ),
    )

    activo = models.BooleanField(
        default=True,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} - ${self.precio_base}"
