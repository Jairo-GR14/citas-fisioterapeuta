
from django.test import TestCase
from django.urls import reverse


class NavegacionPublicaTests(TestCase):

    def test_login_tiene_enlace_a_registro(self):
        respuesta = self.client.get(
            reverse("usuarios:login")
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertContains(
            respuesta,
            reverse("usuarios:registro"),
        )

    def test_login_tiene_recuperacion_de_contrasena(self):
        respuesta = self.client.get(
            reverse("usuarios:login")
        )

        self.assertContains(
            respuesta,
            reverse("usuarios:recuperar_contrasena"),
        )

        self.assertNotContains(
            respuesta,
            'href="#"',
        )

    def test_registro_tiene_enlaces_funcionales(self):
        respuesta = self.client.get(
            reverse("usuarios:registro")
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertContains(
            respuesta,
            reverse("usuarios:login"),
        )

        self.assertNotContains(
            respuesta,
            'href="#"',
        )

    def test_recuperacion_de_contrasena_abre(self):
        respuesta = self.client.get(
            reverse("usuarios:recuperar_contrasena")
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

    def test_registro_muestra_errores_de_validacion(self):
        respuesta = self.client.post(
            reverse("usuarios:registro"),
            data={
                "nombre": "",
                "apellidos": "",
                "telefono": "",
                "correo": "",
                "usuario": "",
                "password": "",
                "password2": "",
            },
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertContains(
            respuesta,
            "Completa todos los campos obligatorios.",
        )
