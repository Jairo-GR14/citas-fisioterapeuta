from django.contrib import admin

from .models import Receta


@admin.register(Receta)
class RecetaAdmin(admin.ModelAdmin):
    list_display = (
        "consulta",
        "frecuencia",
        "duracion",
        "fecha_creacion",
    )

    search_fields = (
        "indicaciones",
        "ejercicios",
        "recomendaciones",
    )

    ordering = (
        "-fecha_creacion",
    )