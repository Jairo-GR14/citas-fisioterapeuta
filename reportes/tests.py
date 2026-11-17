
from datetime import date, time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from citas.models import Cita, MotivoConsulta
from consultas.models import Consulta
from fisioterapeutas.models import Fisioterapeuta
from pacientes.models import Paciente
from precios.models import Servicio
from tratamientos.models import Tratamiento
from usuarios.models import PerfilUsuario


class ReportesTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        Usuario = get_user_model()

        # Administrador
        cls.admin = Usuario.objects.create_user(
            username="admin_reportes",
            password="Prueba12345!",
        )

        cls.perfil_admin = PerfilUsuario.objects.create(
            usuario=cls.admin,
            rol=PerfilUsuario.Rol.ADMINISTRADOR,
        )

        # Paciente 1
        cls.usuario_ana = Usuario.objects.create_user(
            username="paciente_ana",
            password="Prueba12345!",
            first_name="Ana",
            last_name="López",
        )

        perfil_ana = PerfilUsuario.objects.create(
            usuario=cls.usuario_ana,
            rol=PerfilUsuario.Rol.PACIENTE,
        )

        cls.paciente_ana = Paciente.objects.create(
            usuario=perfil_ana,
        )

        # Paciente 2
        usuario_mario = Usuario.objects.create_user(
            username="paciente_mario",
            password="Prueba12345!",
            first_name="Mario",
            last_name="García",
        )

        perfil_mario = PerfilUsuario.objects.create(
            usuario=usuario_mario,
            rol=PerfilUsuario.Rol.PACIENTE,
        )

        cls.paciente_mario = Paciente.objects.create(
            usuario=perfil_mario,
        )

        # Fisioterapeuta
        cls.usuario_fisio = Usuario.objects.create_user(
            username="fisio_luis",
            password="Prueba12345!",
            first_name="Luis",
        )

        perfil_fisio = PerfilUsuario.objects.create(
            usuario=cls.usuario_fisio,
            rol=PerfilUsuario.Rol.FISIOTERAPEUTA,
        )

        cls.fisio = Fisioterapeuta.objects.create(
            usuario=perfil_fisio,
        )

        # Servicios
        cls.servicio_1 = Servicio.objects.create(
            nombre="Valoración inicial",
            precio_base=Decimal("400.00"),
        )

        cls.servicio_2 = Servicio.objects.create(
            nombre="Terapia de rehabilitación",
            precio_base=Decimal("250.00"),
        )

        cls.motivo = MotivoConsulta.objects.create(
            nombre="Consulta de prueba para reportes",
        )

        # Función auxiliar para crear citas
        def crear_cita(
            paciente,
            servicio,
            fecha,
            estado,
            costo_final=None,
        ):
            return Cita.objects.create(
                paciente=paciente,
                fisioterapeuta=cls.fisio,
                servicio=servicio,
                motivo=cls.motivo,
                fecha=fecha,
                hora=time(10, 0),
                estado=estado,
                costo_estimado=servicio.precio_base,
                costo_final=costo_final,
            )

        # Dos citas finalizadas con costo:
        # 450 + 250 = 700 MXN
        cls.cita_octubre = crear_cita(
            cls.paciente_ana,
            cls.servicio_1,
            date(2026, 10, 12),
            Cita.Estado.FINALIZADA,
            Decimal("450.00"),
        )

        cls.cita_noviembre = crear_cita(
            cls.paciente_mario,
            cls.servicio_2,
            date(2026, 11, 13),
            Cita.Estado.FINALIZADA,
            Decimal("250.00"),
        )

        # Finalizada sin costo: no debe sumarse
        cls.cita_sin_costo = crear_cita(
            cls.paciente_ana,
            cls.servicio_1,
            date(2026, 11, 14),
            Cita.Estado.FINALIZADA,
        )

        # Confirmada con un importe:
        # tampoco debe sumarse.
        cls.cita_confirmada = crear_cita(
            cls.paciente_ana,
            cls.servicio_1,
            date(2026, 11, 15),
            Cita.Estado.CONFIRMADA,
            Decimal("999.00"),
        )

        cls.cita_en_proceso = crear_cita(
            cls.paciente_ana,
            cls.servicio_2,
            date(2026, 11, 16),
            Cita.Estado.EN_PROCESO,
        )

        # Consulta y tratamientos
        consulta = Consulta.objects.create(
            cita=cls.cita_octubre,
            fecha_inicio=timezone.now(),
            valoracion_inicial="Valoración de prueba",
            diagnostico="Diagnóstico de prueba",
        )

        Tratamiento.objects.create(
            consulta=consulta,
            nombre="Fortalecimiento",
            activo=True,
        )

        Tratamiento.objects.create(
            consulta=consulta,
            nombre="Ejercicios completados",
            activo=False,
        )

    def setUp(self):
        self.client.force_login(self.admin)

    # =====================================================
    # ACCESO A REPORTES
    # =====================================================

    def test_administrador_accede_a_todos_los_reportes(self):

        nombres = [
            "inicio",
            "reporte_citas",
            "reporte_pacientes",
            "reporte_fisioterapeutas",
            "reporte_ingresos",
        ]

        for nombre in nombres:
            with self.subTest(reporte=nombre):
                respuesta = self.client.get(
                    reverse(f"reportes:{nombre}")
                )

                self.assertEqual(
                    respuesta.status_code,
                    200,
                )

    def test_usuario_sin_sesion_no_accede(self):

        self.client.logout()

        respuesta = self.client.get(
            reverse("reportes:inicio")
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

    def test_paciente_no_accede_a_reportes(self):

        self.client.force_login(self.usuario_ana)

        respuesta = self.client.get(
            reverse("reportes:reporte_ingresos")
        )

        self.assertNotEqual(
            respuesta.status_code,
            200,
        )

    def test_fisioterapeuta_no_accede_a_reportes(self):

        self.client.force_login(self.usuario_fisio)

        respuesta = self.client.get(
            reverse("reportes:reporte_pacientes")
        )

        self.assertNotEqual(
            respuesta.status_code,
            200,
        )

    # =====================================================
    # RESUMEN ADMINISTRATIVO
    # =====================================================

    def test_portada_muestra_totales_correctos(self):

        respuesta = self.client.get(
            reverse("reportes:inicio")
        )

        self.assertEqual(
            respuesta.context["total_citas"],
            5,
        )

        self.assertEqual(
            respuesta.context["total_pacientes"],
            2,
        )

        self.assertEqual(
            respuesta.context["total_fisioterapeutas"],
            1,
        )

        self.assertEqual(
            respuesta.context["total_ingresos"],
            Decimal("700.00"),
        )

    # =====================================================
    # REPORTE DE INGRESOS
    # =====================================================

    def test_ingresos_excluyen_citas_sin_costo_o_no_finalizadas(self):

        respuesta = self.client.get(
            reverse("reportes:reporte_ingresos")
        )

        self.assertEqual(
            respuesta.context["total_ingresos"],
            Decimal("700.00"),
        )

        self.assertEqual(
            respuesta.context["total_servicios"],
            2,
        )

        self.assertEqual(
            respuesta.context["ingreso_promedio"],
            Decimal("350.00"),
        )

    def test_ingresos_filtran_por_servicio(self):

        respuesta = self.client.get(
            reverse("reportes:reporte_ingresos"),
            {
                "tipo_servicio": str(self.servicio_1.pk),
            },
        )

        self.assertEqual(
            respuesta.context["total_ingresos"],
            Decimal("450.00"),
        )

        self.assertEqual(
            respuesta.context["total_servicios"],
            1,
        )

    def test_ingresos_filtran_por_fechas(self):

        respuesta = self.client.get(
            reverse("reportes:reporte_ingresos"),
            {
                "fecha_inicio": "2026-11-01",
                "fecha_fin": "2026-11-30",
            },
        )

        self.assertEqual(
            respuesta.context["total_ingresos"],
            Decimal("250.00"),
        )

    def test_ingresos_agrupados_por_mes(self):

        respuesta = self.client.get(
            reverse("reportes:reporte_ingresos")
        )

        registros = list(
            respuesta.context["ingresos_por_mes"]
        )

        self.assertEqual(len(registros), 2)

        totales = {
            registro["mes"].month: registro["total"]
            for registro in registros
        }

        self.assertEqual(
            totales[10],
            Decimal("450.00"),
        )

        self.assertEqual(
            totales[11],
            Decimal("250.00"),
        )

    def test_costo_cero_no_aumenta_importe(self):

        Cita.objects.create(
            paciente=self.paciente_ana,
            fisioterapeuta=self.fisio,
            servicio=self.servicio_1,
            motivo=self.motivo,
            fecha=date(2026, 11, 20),
            hora=time(12, 0),
            estado=Cita.Estado.FINALIZADA,
            costo_estimado=Decimal("400.00"),
            costo_final=Decimal("0.00"),
        )

        respuesta = self.client.get(
            reverse("reportes:reporte_ingresos")
        )

        self.assertEqual(
            respuesta.context["total_ingresos"],
            Decimal("700.00"),
        )

        # Un servicio gratuito también se cuenta.
        self.assertEqual(
            respuesta.context["total_servicios"],
            3,
        )

    # =====================================================
    # REPORTE DE CITAS
    # =====================================================

    def test_resumen_citas_por_estado(self):

        respuesta = self.client.get(
            reverse("reportes:reporte_citas")
        )

        self.assertEqual(
            respuesta.context["total_citas"],
            5,
        )

        self.assertEqual(
            respuesta.context["citas_finalizadas"],
            3,
        )

        self.assertEqual(
            respuesta.context["citas_confirmadas"],
            1,
        )

        self.assertEqual(
            respuesta.context["citas_en_proceso"],
            1,
        )

    def test_citas_filtran_por_estado(self):

        respuesta = self.client.get(
            reverse("reportes:reporte_citas"),
            {
                "estado": Cita.Estado.FINALIZADA,
            },
        )

        self.assertEqual(
            respuesta.context["total_citas"],
            3,
        )

    def test_citas_filtran_por_paciente(self):

        respuesta = self.client.get(
            reverse("reportes:reporte_citas"),
            {
                "buscar": "paciente_ana",
            },
        )

        self.assertEqual(
            respuesta.context["total_citas"],
            4,
        )

    def test_citas_filtran_por_periodo(self):

        respuesta = self.client.get(
            reverse("reportes:reporte_citas"),
            {
                "fecha_inicio": "2026-11-01",
                "fecha_fin": "2026-11-30",
            },
        )

        self.assertEqual(
            respuesta.context["total_citas"],
            4,
        )

    def test_fecha_invalida_no_provoca_error(self):

        respuesta = self.client.get(
            reverse("reportes:reporte_citas"),
            {
                "fecha_inicio": "2026-02-31",
            },
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertEqual(
            respuesta.context["total_citas"],
            5,
        )

    # =====================================================
    # REPORTE DE PACIENTES
    # =====================================================

    def test_reporte_pacientes_cuenta_tratamientos(self):

        respuesta = self.client.get(
            reverse("reportes:reporte_pacientes")
        )

        pacientes = list(
            respuesta.context["pacientes"]
        )

        ana = next(
            paciente
            for paciente in pacientes
            if paciente.pk == self.paciente_ana.pk
        )

        self.assertEqual(ana.total_citas, 4)

        self.assertEqual(
            ana.total_tratamientos,
            2,
        )

        self.assertEqual(
            ana.tratamientos_activos,
            1,
        )

        self.assertEqual(
            respuesta.context["pacientes_en_tratamiento"],
            1,
        )

    # =====================================================
    # REPORTE DE FISIOTERAPEUTAS
    # =====================================================

    def test_reporte_fisioterapeutas_cuenta_citas(self):

        respuesta = self.client.get(
            reverse("reportes:reporte_fisioterapeutas")
        )

        self.assertEqual(
            respuesta.context["total_fisioterapeutas"],
            1,
        )

        self.assertEqual(
            respuesta.context["total_citas_asignadas"],
            5,
        )

        self.assertEqual(
            respuesta.context["total_citas_finalizadas"],
            3,
        )

    # =====================================================
    # SEGURIDAD: ADMINISTRADOR DESACTIVADO
    # =====================================================

    def test_admin_con_perfil_inactivo_no_accede(self):

        self.perfil_admin.activo = False

        self.perfil_admin.save(
            update_fields=["activo"]
        )

        respuesta = self.client.get(
            reverse("reportes:inicio")
        )

        self.assertNotEqual(
            respuesta.status_code,
            200,
        )
