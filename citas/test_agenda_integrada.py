
from datetime import time

from django.urls import reverse

from .tests import DatosCitas


class AgendaIntegradaTests(DatosCitas):

    def setUp(self):
        self.client.force_login(self.admin)

    def parametros(self, **cambios):

        datos = {
            "servicio": str(self.servicio.pk),
            "fisioterapeuta": str(self.fisio.pk),
            "fecha": self.fecha_futura.isoformat(),
        }

        datos.update(cambios)

        return datos

    def test_pantalla_muestra_horarios_integrados(self):

        respuesta = self.client.get(
            reverse("citas:agendar_cita")
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertContains(
            respuesta,
            "Horarios disponibles",
        )

        self.assertNotContains(
            respuesta,
            "¿No sabes qué horario elegir?",
        )

    def test_api_respeta_duracion_de_90_minutos(self):

        self.servicio.duracion_minutos = 90

        self.servicio.save(
            update_fields=["duracion_minutos"]
        )

        respuesta = self.client.get(
            reverse(
                "citas:horarios_disponibles_json"
            ),
            self.parametros(),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        datos = respuesta.json()

        self.assertTrue(datos["ok"])

        self.assertEqual(
            datos["duracion_minutos"],
            90,
        )

        horarios = {
            item["hora"]: item
            for item in datos["horarios"]
        }

        self.assertEqual(
            horarios["10:00"]["hora_fin"],
            "11:30",
        )

        # La jornada termina a las 13:00.
        self.assertNotIn(
            "12:00",
            horarios,
        )

    def test_api_bloquea_citas_traslapadas(self):

        self.crear_cita(
            hora=time(10, 0),
            duracion_minutos=90,
        )

        respuesta = self.client.get(
            reverse(
                "citas:horarios_disponibles_json"
            ),
            self.parametros(
                servicio=str(
                    self.otro_servicio.pk
                )
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        horarios = {
            item["hora"]: item
            for item in respuesta.json()["horarios"]
        }

        self.assertFalse(
            horarios["11:00"]["disponible"]
        )

        self.assertTrue(
            horarios["12:00"]["disponible"]
        )

    def test_api_rechaza_identificador_invalido(self):

        respuesta = self.client.get(
            reverse(
                "citas:horarios_disponibles_json"
            ),
            self.parametros(
                fisioterapeuta="incorrecto"
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            400,
        )

        self.assertFalse(
            respuesta.json()["ok"]
        )

    def test_fisioterapeuta_no_puede_consultar_api(self):

        self.client.force_login(
            self.usuario_fisio
        )

        respuesta = self.client.get(
            reverse(
                "citas:horarios_disponibles_json"
            ),
            self.parametros(),
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )
