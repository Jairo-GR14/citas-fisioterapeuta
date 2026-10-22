from django.db import models


class Receta(models.Model):
    consulta = models.ForeignKey(
        "consultas.Consulta",
        on_delete=models.CASCADE,
        related_name="recetas",
    )

    indicaciones = models.TextField()

    ejercicios = models.TextField(
        blank=True,
    )

    repeticiones = models.CharField(
        max_length=100,
        blank=True,
    )

    frecuencia = models.CharField(
        max_length=100,
        blank=True,
    )

    duracion = models.CharField(
        max_length=100,
        blank=True,
    )

    recomendaciones = models.TextField(
        blank=True,
    )

    restricciones = models.TextField(
        blank=True,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"Receta - {self.consulta}"