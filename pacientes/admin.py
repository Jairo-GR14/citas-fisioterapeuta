from django.contrib import admin

from .models import Paciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "fecha_nacimiento",
        "activo",
        "fecha_registro",
    )

    list_filter = (
        "activo",
    )

    search_fields = (
        "usuario__usuario__username",
        "usuario__usuario__first_name",
        "usuario__usuario__last_name",
        "usuario__usuario__email",
    )

    ordering = (
        "-fecha_registro",
    )