
from datetime import time

from django.urls import reverse

from .forms import CitaForm, EditarCitaForm
from .tests import DatosCitas


class DuracionVariableTests(DatosCitas):

    def setUp(self):
        self.client.force_login(self.admin)

    def test_consulta_de_90_minutos_respeta_fin_de_jornada(self):

        self.servicio.duracion_minutos = 90
        self.servicio.save(
            update_fields=["duracion_minutos"]
        )

        respuesta = self.client.get(
            reverse("citas:horarios_disponibles"),
            {
                "fisioterapeuta": str(self.fisio.pk),
                "servicio": str(self.servicio.pk),
                "fecha": self.fecha_futura.isoformat(),
            },
        )

        self.assertEqual(respuesta.status_code, 200)

        horarios = {
            item["hora"]: item
            for item in respuesta.context["horarios"]
        }

        self.assertEqual(
            set(horarios),
            {"09:00", "10:00", "11:00"},
        )

        self.assertEqual(
            horarios["10:00"]["fin"],
            "11:30",
        )

        self.assertTrue(
            all(
                item["disponible"]
                for item in horarios.values()
            )
        )

    def test_consulta_de_45_minutos_muestra_fin_correcto(self):

        self.servicio.duracion_minutos = 45
        self.servicio.save(
            update_fields=["duracion_minutos"]
        )

        respuesta = self.client.get(
            reverse("citas:horarios_disponibles"),
            {
                "fisioterapeuta": str(self.fisio.pk),
                "servicio": str(self.servicio.pk),
                "fecha": self.fecha_futura.isoformat(),
            },
        )

        horarios = {
            item["hora"]: item
            for item in respuesta.context["horarios"]
        }

        self.assertEqual(
            horarios["10:00"]["fin"],
            "10:45",
        )

        self.assertTrue(
            horarios["12:00"]["disponible"]
        )

    def test_cita_ocupada_90_minutos_bloquea_inicio_11(self):

        self.crear_cita(
            hora=time(10, 0),
            duracion_minutos=90,
        )

        respuesta = self.client.get(
            reverse("citas:horarios_disponibles"),
            {
                "fisioterapeuta": str(self.fisio.pk),
                "servicio": str(self.otro_servicio.pk),
                "fecha": self.fecha_futura.isoformat(),
            },
        )

        horarios = {
            item["hora"]: item["disponible"]
            for item in respuesta.context["horarios"]
        }

        self.assertFalse(horarios["11:00"])
        self.assertTrue(horarios["12:00"])

    def test_formulario_copia_duracion_del_servicio(self):

        self.servicio.duracion_minutos = 90
        self.servicio.save(
            update_fields=["duracion_minutos"]
        )

        formulario = CitaForm(
            data=self.datos_cita()
        )

        self.assertTrue(
            formulario.is_valid(),
            formulario.errors,
        )

        cita = formulario.save(commit=False)

        self.assertEqual(
            cita.duracion_minutos,
            90,
        )

    def test_formulario_impide_solapamiento_por_duracion_real(self):

        self.crear_cita(
            hora=time(10, 0),
            duracion_minutos=90,
        )

        formulario = CitaForm(
            data=self.datos_cita(
                hora="11:00"
            )
        )

        self.assertFalse(
            formulario.is_valid()
        )

        self.assertTrue(
            formulario.non_field_errors()
        )

    def test_edicion_conserva_duracion_si_servicio_no_cambia(self):

        cita = self.crear_cita(
            duracion_minutos=45
        )

        self.servicio.duracion_minutos = 90
        self.servicio.save(
            update_fields=["duracion_minutos"]
        )

        formulario = EditarCitaForm(
            data=self.datos_cita(),
            instance=cita,
        )

        self.assertTrue(
            formulario.is_valid(),
            formulario.errors,
        )

        self.assertEqual(
            formulario.save(
                commit=False
            ).duracion_minutos,
            45,
        )

    def test_edicion_cambia_duracion_al_cambiar_servicio(self):

        cita = self.crear_cita(
            duracion_minutos=45
        )

        self.otro_servicio.duracion_minutos = 90
        self.otro_servicio.save(
            update_fields=["duracion_minutos"]
        )

        formulario = EditarCitaForm(
            data=self.datos_cita(
                servicio=str(
                    self.otro_servicio.pk
                )
            ),
            instance=cita,
        )

        self.assertTrue(
            formulario.is_valid(),
            formulario.errors,
        )

        self.assertEqual(
            formulario.save(
                commit=False
            ).duracion_minutos,
            90,
        )
