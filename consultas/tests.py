
from datetime import timedelta, time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from citas.models import Cita, MotivoConsulta
from fisioterapeutas.models import Fisioterapeuta
from pacientes.models import Paciente
from precios.models import Servicio
from usuarios.models import PerfilUsuario

from .models import Consulta


class ConsultaIntegracionTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        Usuario = get_user_model()

        # ADMINISTRADOR
        cls.admin = Usuario.objects.create_user(
            username="admin_integracion",
            password="Prueba12345!",
        )

        PerfilUsuario.objects.create(
            usuario=cls.admin,
            rol=PerfilUsuario.Rol.ADMINISTRADOR,
        )

        # PACIENTE
        usuario_paciente = Usuario.objects.create_user(
            username="paciente_integracion",
            password="Prueba12345!",
        )

        perfil_paciente = PerfilUsuario.objects.create(
            usuario=usuario_paciente,
            rol=PerfilUsuario.Rol.PACIENTE,
        )

        paciente = Paciente.objects.create(
            usuario=perfil_paciente,
        )

        # FISIOTERAPEUTA
        usuario_fisio = Usuario.objects.create_user(
            username="fisio_integracion",
            password="Prueba12345!",
        )

        perfil_fisio = PerfilUsuario.objects.create(
            usuario=usuario_fisio,
            rol=PerfilUsuario.Rol.FISIOTERAPEUTA,
        )

        fisioterapeuta = Fisioterapeuta.objects.create(
            usuario=perfil_fisio,
        )

        # SERVICIO
        servicio = Servicio.objects.create(
            nombre="Servicio de prueba de integración",
            precio_base=Decimal("400.00"),
        )

        # MOTIVO
        motivo = MotivoConsulta.objects.create(
            nombre="Motivo de prueba de integración",
        )

        # CITA DE PRUEBA FUTURA
        cls.cita = Cita.objects.create(
            paciente=paciente,
            fisioterapeuta=fisioterapeuta,
            servicio=servicio,
            motivo=motivo,
            fecha=timezone.localdate() + timedelta(days=3),
            hora=time(10, 0),
            estado=Cita.Estado.CONFIRMADA,
            costo_estimado=Decimal("400.00"),
        )

    def setUp(self):
        self.client.force_login(self.admin)

    # =====================================================
    # FUNCIONES AUXILIARES
    # =====================================================

    def url_inicio(self):
        return reverse(
            "consultas:iniciar_consulta",
            args=[self.cita.pk],
        )

    def preparar_cita_pasada(
        self,
        estado=Cita.Estado.CONFIRMADA,
    ):

        self.cita.fecha = (
            timezone.localdate() - timedelta(days=3)
        )

        self.cita.estado = estado

        self.cita.save(
            update_fields=["fecha", "estado"]
        )

    def preparar_consulta_en_proceso(self):

        self.preparar_cita_pasada(
            Cita.Estado.EN_PROCESO
        )

        return Consulta.objects.create(
            cita=self.cita,
            fecha_inicio=timezone.now(),
            valoracion_inicial="Valoración de prueba",
            diagnostico="Diagnóstico de prueba",
        )

    # =====================================================
    # NO PERMITIR INICIAR CITA FUTURA MEDIANTE GET
    # =====================================================

    def test_get_futuro_no_permite_iniciar(self):

        respuesta = self.client.get(
            self.url_inicio()
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.assertFalse(
            Consulta.objects.filter(
                cita=self.cita
            ).exists()
        )

    # =====================================================
    # NO PERMITIR INICIAR CITA FUTURA MEDIANTE POST
    # =====================================================

    def test_post_futuro_no_permite_iniciar(self):

        respuesta = self.client.post(
            self.url_inicio()
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.assertFalse(
            Consulta.objects.filter(
                cita=self.cita
            ).exists()
        )

        self.cita.refresh_from_db()

        self.assertEqual(
            self.cita.estado,
            Cita.Estado.CONFIRMADA,
        )

    # =====================================================
    # NO INICIAR CITAS SIN CONFIRMAR
    # =====================================================

    def test_no_permite_iniciar_cita_no_confirmada(self):

        self.preparar_cita_pasada(
            Cita.Estado.PROGRAMADA
        )

        respuesta = self.client.post(
            self.url_inicio()
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.assertFalse(
            Consulta.objects.filter(
                cita=self.cita
            ).exists()
        )

    # =====================================================
    # INICIAR CITA CONFIRMADA EN FECHA PASADA
    # =====================================================

    def test_permite_iniciar_confirmada_pasada(self):

        self.preparar_cita_pasada()

        respuesta = self.client.post(
            self.url_inicio()
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.assertTrue(
            Consulta.objects.filter(
                cita=self.cita
            ).exists()
        )

        self.cita.refresh_from_db()

        self.assertEqual(
            self.cita.estado,
            Cita.Estado.EN_PROCESO,
        )

    # =====================================================
    # REGISTRAR COSTO REAL Y FECHA DE FINALIZACIÓN
    # =====================================================

    def test_finalizar_registra_costo_real_y_fecha(self):

        consulta = self.preparar_consulta_en_proceso()

        url = reverse(
            "consultas:finalizar_consulta",
            args=[consulta.pk],
        )

        respuesta = self.client.post(
            url,
            {
                "costo_final": "450.50",
            },
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.cita.refresh_from_db()
        consulta.refresh_from_db()

        self.assertEqual(
            self.cita.costo_final,
            Decimal("450.50"),
        )

        self.assertEqual(
            self.cita.estado,
            Cita.Estado.FINALIZADA,
        )

        self.assertIsNotNone(
            consulta.fecha_finalizacion
        )

    # =====================================================
    # RECHAZAR COSTO OMITIDO
    # =====================================================

    def test_finalizar_rechaza_costo_omitido(self):

        consulta = self.preparar_consulta_en_proceso()

        url = reverse(
            "consultas:finalizar_consulta",
            args=[consulta.pk],
        )

        respuesta = self.client.post(
            url,
            {},
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.cita.refresh_from_db()

        self.assertEqual(
            self.cita.estado,
            Cita.Estado.EN_PROCESO,
        )

        self.assertIsNone(
            self.cita.costo_final
        )

    # =====================================================
    # RECHAZAR COSTO NEGATIVO
    # =====================================================

    def test_finalizar_rechaza_costo_negativo(self):

        consulta = self.preparar_consulta_en_proceso()

        url = reverse(
            "consultas:finalizar_consulta",
            args=[consulta.pk],
        )

        respuesta = self.client.post(
            url,
            {
                "costo_final": "-5.00",
            },
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.cita.refresh_from_db()

        self.assertEqual(
            self.cita.estado,
            Cita.Estado.EN_PROCESO,
        )

        self.assertIsNone(
            self.cita.costo_final
        )

    # =====================================================
    # PERMITIR COSTO CERO
    # =====================================================

    def test_finalizar_acepta_costo_cero(self):

        consulta = self.preparar_consulta_en_proceso()

        url = reverse(
            "consultas:finalizar_consulta",
            args=[consulta.pk],
        )

        respuesta = self.client.post(
            url,
            {
                "costo_final": "0.00",
            },
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.cita.refresh_from_db()

        self.assertEqual(
            self.cita.costo_final,
            Decimal("0.00"),
        )

        self.assertEqual(
            self.cita.estado,
            Cita.Estado.FINALIZADA,
        )

    # =====================================================
    # EXIGIR DIAGNÓSTICO
    # =====================================================

    def test_finalizar_exige_diagnostico(self):

        consulta = self.preparar_consulta_en_proceso()

        consulta.diagnostico = ""

        consulta.save(
            update_fields=["diagnostico"]
        )

        url = reverse(
            "consultas:finalizar_consulta",
            args=[consulta.pk],
        )

        respuesta = self.client.post(
            url,
            {
                "costo_final": "400.00",
            },
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.cita.refresh_from_db()

        self.assertEqual(
            self.cita.estado,
            Cita.Estado.EN_PROCESO,
        )

        self.assertIsNone(
            self.cita.costo_final
        )

    # =====================================================
    # NO FINALIZAR DOS VECES
    # =====================================================

    def test_no_finaliza_dos_veces(self):

        consulta = self.preparar_consulta_en_proceso()

        url = reverse(
            "consultas:finalizar_consulta",
            args=[consulta.pk],
        )

        self.client.post(
            url,
            {
                "costo_final": "400.00",
            },
        )

        respuesta = self.client.post(
            url,
            {
                "costo_final": "900.00",
            },
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.cita.refresh_from_db()

        self.assertEqual(
            self.cita.costo_final,
            Decimal("400.00"),
        )
