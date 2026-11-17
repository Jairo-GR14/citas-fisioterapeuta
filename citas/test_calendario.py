
from datetime import time, timedelta

from django.urls import reverse

from .tests import DatosCitas


class CalendarioTests(DatosCitas):

    def setUp(self):
        self.client.force_login(self.admin)

    def parametros(self):

        return {
            "start": (
                self.fecha_futura
                - timedelta(days=1)
            ).isoformat(),

            "end": (
                self.fecha_futura
                + timedelta(days=1)
            ).isoformat(),
        }

    def test_agenda_muestra_calendario(self):

        respuesta = self.client.get(
            reverse("citas:agenda")
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertContains(
            respuesta,
            'id="calendario"',
        )

        self.assertContains(
            respuesta,
            reverse("citas:eventos_calendario"),
        )

    def test_cita_de_90_minutos_tiene_fin_correcto(self):

        cita = self.crear_cita(
            duracion_minutos=90
        )

        respuesta = self.client.get(
            reverse("citas:eventos_calendario"),
            self.parametros(),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        eventos = respuesta.json()

        self.assertEqual(
            len(eventos),
            1,
        )

        self.assertEqual(
            eventos[0]["id"],
            str(cita.pk),
        )

        self.assertEqual(
            eventos[0]["start"],
            f"{self.fecha_futura.isoformat()}T10:00",
        )

        self.assertEqual(
            eventos[0]["end"],
            f"{self.fecha_futura.isoformat()}T11:30",
        )

    def test_paciente_solo_ve_sus_citas(self):

        propia = self.crear_cita()

        ajena = self.crear_cita(
            paciente=self.otro_paciente,
            hora=time(11, 0),
        )

        self.client.force_login(
            self.usuario_paciente
        )

        respuesta = self.client.get(
            reverse("citas:eventos_calendario"),
            self.parametros(),
        )

        ids = {
            evento["id"]
            for evento in respuesta.json()
        }

        self.assertIn(
            str(propia.pk),
            ids,
        )

        self.assertNotIn(
            str(ajena.pk),
            ids,
        )

    def test_fisioterapeuta_solo_ve_sus_citas(self):

        propia = self.crear_cita()

        ajena = self.crear_cita(
            fisioterapeuta=self.otro_fisio
        )

        self.client.force_login(
            self.usuario_fisio
        )

        respuesta = self.client.get(
            reverse("citas:eventos_calendario"),
            self.parametros(),
        )

        ids = {
            evento["id"]
            for evento in respuesta.json()
        }

        self.assertIn(
            str(propia.pk),
            ids,
        )

        self.assertNotIn(
            str(ajena.pk),
            ids,
        )

    def test_usuario_sin_sesion_no_consulta_eventos(self):

        self.client.logout()

        respuesta = self.client.get(
            reverse("citas:eventos_calendario"),
            self.parametros(),
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

    def test_intervalo_invalido_no_devuelve_eventos(self):

        respuesta = self.client.get(
            reverse("citas:eventos_calendario"),
            {
                "start": "fecha-no-valida",
                "end": "tampoco",
            },
        )

        self.assertEqual(
            respuesta.status_code,
            400,
        )
