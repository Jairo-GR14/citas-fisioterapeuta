from django.contrib import admin

from .models import RegistroActividad


@admin.register(RegistroActividad)
class RegistroActividadAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "accion",
        "modulo",
        "fecha",
    )

    list_filter = (
        "modulo",
        "fecha",
    )

    search_fields = (
        "accion",
        "descripcion",
        "usuario__usuario__username",
    )

    ordering = (
        "-fecha",
    )