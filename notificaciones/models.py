from django.db import models


class Notificacion(models.Model):

    class Tipo(models.TextChoices):
        CITA = "CITA", "Cita"
        RECORDATORIO = "RECORDATORIO", "Recordatorio"
        SISTEMA = "SISTEMA", "Sistema"

    usuario = models.ForeignKey(
        "usuarios.PerfilUsuario",
        on_delete=models.CASCADE,
        related_name="notificaciones",
    )

    tipo = models.CharField(
        max_length=20,
        choices=Tipo.choices,
        default=Tipo.SISTEMA,
    )

    titulo = models.CharField(
        max_length=150,
    )

    mensaje = models.TextField()

    leida = models.BooleanField(
        default=False,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_lectura = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.titulo} - {self.usuario}"