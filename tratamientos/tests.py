
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
from usuarios.models import PerfilUsuario

from .forms import TratamientoForm
from .models import Tratamiento


# =========================================================
# PRUEBAS DEL FORMULARIO
# =========================================================

class TratamientoFormTests(TestCase):

    def test_fechas_validas(self):
        formulario = TratamientoForm(data={
            "nombre": "Rehabilitación de rodilla",
            "descripcion": "Ejercicios terapéuticos",
            "objetivo": "Mejorar movilidad",
            "fecha_inicio": "2026-11-13",
            "fecha_fin": "2026-11-20",
            "activo": "on",
        })

        self.assertTrue(
            formulario.is_valid(),
            formulario.errors,
        )

    def test_no_acepta_fecha_fin_anterior(self):
        formulario = TratamientoForm(data={
            "nombre": "Movilidad",
            "fecha_inicio": "2026-11-20",
            "fecha_fin": "2026-11-13",
            "activo": "on",
        })

        self.assertFalse(formulario.is_valid())
        self.assertIn("fecha_fin", formulario.errors)

    def test_nombre_es_obligatorio(self):
        formulario = TratamientoForm(data={
            "nombre": "",
            "fecha_inicio": "2026-11-13",
            "fecha_fin": "2026-11-20",
        })

        self.assertFalse(formulario.is_valid())
        self.assertIn("nombre", formulario.errors)

    def test_fechas_son_opcionales(self):
        formulario = TratamientoForm(data={
            "nombre": "Ejercicios generales",
            "descripcion": "",
            "objetivo": "",
        })

        self.assertTrue(
            formulario.is_valid(),
            formulario.errors,
        )


# =========================================================
# PRUEBAS DE VISTAS, PERMISOS E INTEGRACIÓN
# =========================================================

class TratamientoVistasTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        Usuario = get_user_model()

        # ADMINISTRADOR
        cls.admin = Usuario.objects.create_user(
            username="admin_prueba",
            password="Prueba12345!",
        )

        PerfilUsuario.objects.create(
            usuario=cls.admin,
            rol=PerfilUsuario.Rol.ADMINISTRADOR,
        )

        # FISIOTERAPEUTA PRINCIPAL
        cls.fisio_usuario = Usuario.objects.create_user(
            username="fisio_prueba",
            password="Prueba12345!",
        )

        cls.fisio_perfil = PerfilUsuario.objects.create(
            usuario=cls.fisio_usuario,
            rol=PerfilUsuario.Rol.FISIOTERAPEUTA,
        )

        cls.fisioterapeuta = Fisioterapeuta.objects.create(
            usuario=cls.fisio_perfil,
            especialidad="Fisioterapia",
        )

        # OTRO FISIOTERAPEUTA
        cls.otro_usuario = Usuario.objects.create_user(
            username="otro_fisio",
            password="Prueba12345!",
        )

        cls.otro_perfil = PerfilUsuario.objects.create(
            usuario=cls.otro_usuario,
            rol=PerfilUsuario.Rol.FISIOTERAPEUTA,
        )

        cls.otro_fisioterapeuta = Fisioterapeuta.objects.create(
            usuario=cls.otro_perfil,
        )

        # PACIENTE
        cls.paciente_usuario = Usuario.objects.create_user(
            username="paciente_prueba",
            password="Prueba12345!",
        )

        cls.paciente_perfil = PerfilUsuario.objects.create(
            usuario=cls.paciente_usuario,
            rol=PerfilUsuario.Rol.PACIENTE,
        )

        cls.paciente = Paciente.objects.create(
            usuario=cls.paciente_perfil,
        )

        # RECEPCIONISTA
        cls.recepcionista = Usuario.objects.create_user(
            username="recepcion_prueba",
            password="Prueba12345!",
        )

        PerfilUsuario.objects.create(
            usuario=cls.recepcionista,
            rol=PerfilUsuario.Rol.RECEPCIONISTA,
        )

        # SERVICIO
        cls.servicio = Servicio.objects.create(
            nombre="Valoración de prueba",
            precio_base=Decimal("400.00"),
        )

        # MOTIVO
        cls.motivo = MotivoConsulta.objects.create(
            nombre="Consulta de prueba",
        )

        # CITA EN PROCESO
        cls.cita = Cita.objects.create(
            paciente=cls.paciente,
            fisioterapeuta=cls.fisioterapeuta,
            servicio=cls.servicio,
            motivo=cls.motivo,
            fecha=date(2026, 11, 13),
            hora=time(10, 0),
            estado=Cita.Estado.EN_PROCESO,
            costo_estimado=Decimal("400.00"),
        )

        cls.consulta = Consulta.objects.create(
            cita=cls.cita,
            fecha_inicio=timezone.now(),
        )

        # TRATAMIENTO EXISTENTE
        cls.tratamiento = Tratamiento.objects.create(
            consulta=cls.consulta,
            nombre="Rehabilitación de rodilla",
            descripcion="Ejercicios iniciales",
            objetivo="Mejorar movilidad",
            fecha_inicio=date(2026, 11, 13),
            fecha_fin=date(2026, 11, 20),
            activo=True,
        )

        # CONSULTA DEL OTRO FISIOTERAPEUTA
        cls.cita_ajena = Cita.objects.create(
            paciente=cls.paciente,
            fisioterapeuta=cls.otro_fisioterapeuta,
            servicio=cls.servicio,
            motivo=cls.motivo,
            fecha=date(2026, 11, 13),
            hora=time(11, 0),
            estado=Cita.Estado.EN_PROCESO,
            costo_estimado=Decimal("400.00"),
        )

        cls.consulta_ajena = Consulta.objects.create(
            cita=cls.cita_ajena,
            fecha_inicio=timezone.now(),
        )

    # =====================================================
    # DATOS Y URLS AUXILIARES
    # =====================================================

    def datos_validos(self, **cambios):
        datos = {
            "nombre": "Terapia de fortalecimiento",
            "descripcion": "Ejercicios progresivos",
            "objetivo": "Recuperar fuerza",
            "fecha_inicio": "2026-11-13",
            "fecha_fin": "2026-11-20",
            "activo": "on",
        }

        datos.update(cambios)
        return datos

    def url_registro(self):
        return reverse(
            "tratamientos:registrar_tratamiento",
            args=[self.consulta.pk],
        )

    def url_detalle(self):
        return reverse(
            "tratamientos:detalle_tratamiento",
            args=[self.tratamiento.pk],
        )

    def url_edicion(self):
        return reverse(
            "tratamientos:editar_tratamiento",
            args=[self.tratamiento.pk],
        )

    def url_historial(self):
        return reverse(
            "tratamientos:historial_tratamientos",
            args=[self.consulta.pk],
        )

    # =====================================================
    # PRUEBA: ABRIR FORMULARIO DE REGISTRO
    # =====================================================

    def test_fisioterapeuta_puede_ver_formulario_registro(self):
        self.client.force_login(self.fisio_usuario)

        respuesta = self.client.get(
            self.url_registro()
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

    # =====================================================
    # PRUEBA: REGISTRAR TRATAMIENTO
    # =====================================================

    def test_fisioterapeuta_registra_tratamiento(self):
        self.client.force_login(self.fisio_usuario)

        respuesta = self.client.post(
            self.url_registro(),
            self.datos_validos(),
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        nuevo = Tratamiento.objects.get(
            nombre="Terapia de fortalecimiento"
        )

        self.assertEqual(
            nuevo.consulta_id,
            self.consulta.pk,
        )

        self.assertTrue(nuevo.activo)

    # =====================================================
    # PRUEBA: NO ASIGNAR TRATAMIENTO A CONSULTA AJENA
    # =====================================================

    def test_formulario_no_permite_asignar_otra_consulta(self):
        self.client.force_login(self.fisio_usuario)

        datos = self.datos_validos(
            consulta=str(self.consulta_ajena.pk)
        )

        respuesta = self.client.post(
            self.url_registro(),
            datos,
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        nuevo = Tratamiento.objects.get(
            nombre="Terapia de fortalecimiento"
        )

        self.assertEqual(
            nuevo.consulta_id,
            self.consulta.pk,
        )

    # =====================================================
    # PRUEBA: RECHAZAR FECHAS INCORRECTAS
    # =====================================================

    def test_registro_rechaza_fechas_invertidas(self):
        self.client.force_login(self.fisio_usuario)

        total_anterior = Tratamiento.objects.count()

        respuesta = self.client.post(
            self.url_registro(),
            self.datos_validos(
                fecha_fin="2026-11-01"
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertIn(
            "fecha_fin",
            respuesta.context["formulario"].errors,
        )

        self.assertEqual(
            Tratamiento.objects.count(),
            total_anterior,
        )

    # =====================================================
    # PRUEBA: CONSULTAR HISTORIAL Y DETALLE
    # =====================================================

    def test_fisioterapeuta_ve_detalle_e_historial(self):
        self.client.force_login(self.fisio_usuario)

        detalle = self.client.get(
            self.url_detalle()
        )

        historial = self.client.get(
            self.url_historial()
        )

        self.assertEqual(
            detalle.status_code,
            200,
        )

        self.assertEqual(
            historial.status_code,
            200,
        )

        self.assertContains(
            historial,
            "Rehabilitación de rodilla",
        )

    # =====================================================
    # PRUEBA: EDITAR TRATAMIENTO
    # =====================================================

    def test_fisioterapeuta_edita_tratamiento(self):
        self.client.force_login(self.fisio_usuario)

        respuesta = self.client.post(
            self.url_edicion(),
            self.datos_validos(
                nombre="Tratamiento actualizado"
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.tratamiento.refresh_from_db()

        self.assertEqual(
            self.tratamiento.nombre,
            "Tratamiento actualizado",
        )

    # =====================================================
    # PRUEBA: NO EDITAR CON FECHAS INCORRECTAS
    # =====================================================

    def test_edicion_rechaza_fecha_incorrecta(self):
        self.client.force_login(self.fisio_usuario)

        respuesta = self.client.post(
            self.url_edicion(),
            self.datos_validos(
                fecha_fin="2026-11-01"
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertIn(
            "fecha_fin",
            respuesta.context["formulario"].errors,
        )

        self.tratamiento.refresh_from_db()

        self.assertEqual(
            self.tratamiento.nombre,
            "Rehabilitación de rodilla",
        )

    # =====================================================
    # PRUEBA: NO REGISTRAR EN CONSULTA FINALIZADA
    # =====================================================

    def test_no_registra_si_consulta_finalizada(self):
        self.cita.estado = Cita.Estado.FINALIZADA

        self.cita.save(
            update_fields=["estado"]
        )

        self.client.force_login(self.fisio_usuario)

        total_anterior = Tratamiento.objects.count()

        respuesta = self.client.post(
            self.url_registro(),
            self.datos_validos(),
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.assertEqual(
            Tratamiento.objects.count(),
            total_anterior,
        )

    # =====================================================
    # PRUEBA: NO EDITAR EN CONSULTA FINALIZADA
    # =====================================================

    def test_no_edita_si_consulta_finalizada(self):
        self.cita.estado = Cita.Estado.FINALIZADA

        self.cita.save(
            update_fields=["estado"]
        )

        self.client.force_login(self.fisio_usuario)

        respuesta = self.client.post(
            self.url_edicion(),
            self.datos_validos(
                nombre="Cambio indebido"
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.tratamiento.refresh_from_db()

        self.assertEqual(
            self.tratamiento.nombre,
            "Rehabilitación de rodilla",
        )

    # =====================================================
    # PRUEBA: LEER TRATAMIENTOS FINALIZADOS
    # =====================================================

    def test_consulta_finalizada_permite_lectura(self):
        self.cita.estado = Cita.Estado.FINALIZADA

        self.cita.save(
            update_fields=["estado"]
        )

        self.client.force_login(self.fisio_usuario)

        self.assertEqual(
            self.client.get(
                self.url_detalle()
            ).status_code,
            200,
        )

        self.assertEqual(
            self.client.get(
                self.url_historial()
            ).status_code,
            200,
        )

    # =====================================================
    # PRUEBA: FISIOTERAPEUTA NO ACCEDE A DATOS AJENOS
    # =====================================================

    def test_otro_fisioterapeuta_no_puede_acceder(self):
        self.client.force_login(self.otro_usuario)

        for url in (
            self.url_registro(),
            self.url_edicion(),
            self.url_detalle(),
            self.url_historial(),
        ):

            with self.subTest(url=url):
                self.assertEqual(
                    self.client.get(url).status_code,
                    403,
                )

    # =====================================================
    # PRUEBA: PACIENTE SIN PERMISOS CLÍNICOS
    # =====================================================

    def test_paciente_no_puede_acceder(self):
        self.client.force_login(self.paciente_usuario)

        for url in (
            self.url_registro(),
            self.url_detalle(),
            self.url_historial(),
        ):

            with self.subTest(url=url):
                self.assertEqual(
                    self.client.get(url).status_code,
                    302,
                )

    # =====================================================
    # PRUEBA: RECEPCIONISTA SIN PERMISOS CLÍNICOS
    # =====================================================

    def test_recepcionista_no_puede_acceder(self):
        self.client.force_login(self.recepcionista)

        self.assertEqual(
            self.client.get(
                self.url_historial()
            ).status_code,
            302,
        )

    # =====================================================
    # PRUEBA: ADMINISTRADOR PUEDE GESTIONAR
    # =====================================================

    def test_admin_puede_acceder_a_historial_y_registrar(self):
        self.client.force_login(self.admin)

        self.assertEqual(
            self.client.get(
                self.url_historial()
            ).status_code,
            200,
        )

        respuesta = self.client.post(
            self.url_registro(),
            self.datos_validos(),
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.assertTrue(
            Tratamiento.objects.filter(
                nombre="Terapia de fortalecimiento"
            ).exists()
        )

    # =====================================================
    # PRUEBA: USUARIO SIN INICIAR SESIÓN
    # =====================================================

    def test_sin_sesion_se_rechaza_acceso(self):
        self.assertEqual(
            self.client.get(
                self.url_historial()
            ).status_code,
            302,
        )

    # =====================================================
    # PRUEBA: PERFIL INACTIVO
    # =====================================================

    def test_fisioterapeuta_con_perfil_inactivo_no_puede_entrar(self):
        self.fisio_perfil.activo = False

        self.fisio_perfil.save(
            update_fields=["activo"]
        )

        self.client.force_login(self.fisio_usuario)

        self.assertEqual(
            self.client.get(
                self.url_historial()
            ).status_code,
            403,
        )
