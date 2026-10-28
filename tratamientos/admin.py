from django.contrib import admin

from .models import Tratamiento


@admin.register(Tratamiento)
class TratamientoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "consulta",
        "fecha_inicio",
        "fecha_fin",
        "activo",
    )

    list_filter = (
        "activo",
    )

    search_fields = (
        "nombre",
        "descripcion",
        "objetivo",
    )

    ordering = (
        "-fecha_inicio",
    )