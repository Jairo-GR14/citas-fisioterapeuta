
from django.urls import path
from ..templates.citas import views

app_name = "citas"

urlpatterns = [
    path("", views.agenda, name="agenda"),
    path("agendar/", views.agendar_cita, name="agendar_cita"),
    path("mis-citas/", views.mis_citas, name="mis_citas"),
    path("horarios/", views.horarios_disponibles, name="horarios_disponibles"),
    path("confirmar/", views.confirmar_cita, name="confirmar_cita"),
    path("emergencia/", views.cita_emergencia, name="cita_emergencia"),

    path("<int:cita_id>/", views.detalle_cita, name="detalle_cita"),
    path("<int:cita_id>/editar/", views.editar_cita, name="editar_cita"),
    path("<int:cita_id>/cancelar/", views.cancelar_cita, name="cancelar_cita"),
]
