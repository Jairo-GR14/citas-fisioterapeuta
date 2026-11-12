from django.urls import path
from . import views

app_name = "reportes"

urlpatterns = [
    path("", views.reportes, name="inicio"),
    path("citas/", views.reporte_citas, name="reporte_citas"),
    path("pacientes/", views.reporte_pacientes, name="reporte_pacientes"),
    path("fisioterapeutas/", views.reporte_fisioterapeutas, name="reporte_fisioterapeutas"),
    path("ingresos/", views.reporte_ingresos, name="reporte_ingresos"),
]
