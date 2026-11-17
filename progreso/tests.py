
from datetime import time
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

from .forms import ProgresoForm
from .models import Progreso


# =========================================================
# PRUEBAS DEL FORMULARIO
# =========================================================

class ProgresoFormTests(TestCase):

    def test_campos_opcionales(self):
        formulario = ProgresoForm(data={})

        self.assertTrue(
            formulario.is_valid(),
            formulario.errors,
        )

    def test_nivel_dolor_cero_es_valido(self):
        formulario = ProgresoForm(
            data={"nivel_dolor": "0"}
        )

        self.assertTrue(
            formulario.is_valid(),
            formulario.errors,
        )

    def test_nivel_dolor_diez_es_valido(self):
        formulario = ProgresoForm(
            data={"nivel_dolor": "10"}
        )

        self.assertTrue(
            formulario.is_valid(),
            formulario.errors,
        )

    def test_nivel_dolor_negativo_es_invalido(self):
        formulario = ProgresoForm(
            data={"nivel_dolor": "-1"}
        )

        self.assertFalse(formulario.is_valid())
        self.assertIn(
            "nivel_dolor",
            formulario.errors,
        )

    def test_nivel_dolor_mayor_a_diez_es_invalido(self):
        formulario = ProgresoForm(
            data={"nivel_dolor": "11"}
        )

        self.assertFalse(formulario.is_valid())
        self.assertIn(
            "nivel_dolor",
            formulario.errors,
        )

    def test_nivel_dolor_no_numerico_es_invalido(self):
        formulario = ProgresoForm(
            data={"nivel_dolor": "mucho"}
        )

        self.assertFalse(formulario.is_valid())
        self.assertIn(
            "nivel_dolor",
            formulario.errors,
        )


# =========================================================
# PRUEBAS DE VISTAS Y PERMISOS
# =========================================================

class ProgresoVistasTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        Usuario = get_user_model()

        # ADMINISTRADOR
        cls.admin = Usuario.objects.create_user(
            username="admin_progreso",
            password="Prueba12345!",
        )

        PerfilUsuario.objects.create(
            usuario=cls.admin,
            rol=PerfilUsuario.Rol.ADMINISTRADOR,
        )

        # FISIOTERAPEUTA PRINCIPAL
        cls.usuario_fisio = Usuario.objects.create_user(
            username="fisio_progreso",
            password="Prueba12345!",
        )

        cls.perfil_fisio = PerfilUsuario.objects.create(
            usuario=cls.usuario_fisio,
            rol=PerfilUsuario.Rol.FISIOTERAPEUTA,
        )

        cls.fisio = Fisioterapeuta.objects.create(
            usuario=cls.perfil_fisio,
        )

        # SEGUNDO FISIOTERAPEUTA
        cls.usuario_otro_fisio = Usuario.objects.create_user(
            username="otro_fisio_progreso",
            password="Prueba12345!",
        )

        perfil_otro_fisio = PerfilUsuario.objects.create(
            usuario=cls.usuario_otro_fisio,
            rol=PerfilUsuario.Rol.FISIOTERAPEUTA,
        )

        cls.otro_fisio = Fisioterapeuta.objects.create(
            usuario=perfil_otro_fisio,
        )

        # PACIENTE PRINCIPAL
        cls.usuario_paciente = Usuario.objects.create_user(
            username="paciente_progreso",
            password="Prueba12345!",
        )

        perfil_paciente = PerfilUsuario.objects.create(
            usuario=cls.usuario_paciente,
            rol=PerfilUsuario.Rol.PACIENTE,
        )

        cls.paciente = Paciente.objects.create(
            usuario=perfil_paciente,
        )

        # SEGUNDO PACIENTE
        cls.usuario_otro_paciente = Usuario.objects.create_user(
            username="otro_paciente_progreso",
            password="Prueba12345!",
        )

        perfil_otro_paciente = PerfilUsuario.objects.create(
            usuario=cls.usuario_otro_paciente,
            rol=PerfilUsuario.Rol.PACIENTE,
        )

        cls.otro_paciente = Paciente.objects.create(
            usuario=perfil_otro_paciente,
        )

        # SERVICIO
        cls.servicio = Servicio.objects.create(
            nombre="Rehabilitación de prueba",
            precio_base=Decimal("400.00"),
        )

        # MOTIVO
        cls.motivo = MotivoConsulta.objects.create(
            nombre="Seguimiento de rehabilitación",
        )

        # CITA PRINCIPAL CON PROGRESO EXISTENTE
        cls.cita_principal = Cita.objects.create(
            paciente=cls.paciente,
            fisioterapeuta=cls.fisio,
            servicio=cls.servicio,
            motivo=cls.motivo,
            fecha=timezone.localdate(),
            hora=time(9, 0),
            estado=Cita.Estado.EN_PROCESO,
            costo_estimado=Decimal("400.00"),
        )

        cls.consulta_principal = Consulta.objects.create(
            cita=cls.cita_principal,
            fecha_inicio=timezone.now(),
        )

        cls.progreso = Progreso.objects.create(
            consulta=cls.consulta_principal,
            movilidad="Movilidad limitada.",
            nivel_dolor=5,
            ejercicios_realizados="Ejercicios suaves.",
            avances="Mejoría inicial.",
            observaciones="Paciente estable.",
            recomendaciones="Continuar ejercicios.",
        )

        # SEGUNDA CONSULTA SIN PROGRESO,
        # PARA PROBAR EL REGISTRO
        cls.cita_nueva = Cita.objects.create(
            paciente=cls.paciente,
            fisioterapeuta=cls.fisio,
            servicio=cls.servicio,
            motivo=cls.motivo,
            fecha=timezone.localdate(),
            hora=time(10, 0),
            estado=Cita.Estado.EN_PROCESO,
            costo_estimado=Decimal("400.00"),
        )

        cls.consulta_nueva = Consulta.objects.create(
            cita=cls.cita_nueva,
            fecha_inicio=timezone.now(),
        )

        # CONSULTA AJENA CON SU PROPIO PROGRESO
        cls.cita_ajena = Cita.objects.create(
            paciente=cls.otro_paciente,
            fisioterapeuta=cls.otro_fisio,
            servicio=cls.servicio,
            motivo=cls.motivo,
            fecha=timezone.localdate(),
            hora=time(11, 0),
            estado=Cita.Estado.EN_PROCESO,
            costo_estimado=Decimal("400.00"),
        )

        cls.consulta_ajena = Consulta.objects.create(
            cita=cls.cita_ajena,
            fecha_inicio=timezone.now(),
        )

        cls.progreso_ajeno = Progreso.objects.create(
            consulta=cls.consulta_ajena,
            movilidad="Movilidad de otro paciente.",
            nivel_dolor=7,
        )

    def setUp(self):
        self.client.force_login(self.usuario_fisio)

    # =====================================================
    # DATOS Y DIRECCIONES AUXILIARES
    # =====================================================

    def datos_validos(self, **cambios):
        datos = {
            "movilidad": "Mayor movilidad articular.",
            "nivel_dolor": "3",
            "ejercicios_realizados": "Flexiones asistidas.",
            "avances": "Mejoría de fuerza.",
            "observaciones": "Buena evolución.",
            "recomendaciones": "Continuar terapia.",
        }

        datos.update(cambios)
        return datos

    def url_registro(self, consulta=None):
        consulta = consulta or self.consulta_nueva

        return reverse(
            "progreso:registrar_progreso",
            args=[consulta.pk],
        )

    def url_edicion(self, consulta=None):
        consulta = consulta or self.consulta_principal

        return reverse(
            "progreso:editar_progreso",
            args=[consulta.pk],
        )

    def url_detalle(self, consulta=None):
        consulta = consulta or self.consulta_principal

        return reverse(
            "progreso:detalle_progreso",
            args=[consulta.pk],
        )

    def url_paciente(self, consulta=None):
        consulta = consulta or self.consulta_principal

        return reverse(
            "progreso:progreso_paciente",
            args=[consulta.pk],
        )

    # =====================================================
    # 1. ABRIR FORMULARIO DE REGISTRO
    # =====================================================

    def test_fisioterapeuta_abre_formulario_registro(self):
        respuesta = self.client.get(
            self.url_registro()
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(
            "formulario",
            respuesta.context,
        )

    # =====================================================
    # 2. REGISTRAR PROGRESO
    # =====================================================

    def test_fisioterapeuta_registra_progreso(self):
        respuesta = self.client.post(
            self.url_registro(),
            self.datos_validos(),
        )

        self.assertEqual(respuesta.status_code, 302)

        nuevo = Progreso.objects.get(
            consulta=self.consulta_nueva
        )

        self.assertEqual(nuevo.nivel_dolor, 3)
        self.assertEqual(
            nuevo.avances,
            "Mejoría de fuerza.",
        )

    # =====================================================
    # 3. RECHAZAR NIVEL DE DOLOR INVÁLIDO
    # =====================================================

    def test_registro_rechaza_nivel_dolor_invalido(self):
        respuesta = self.client.post(
            self.url_registro(),
            self.datos_validos(nivel_dolor="15"),
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(
            "nivel_dolor",
            respuesta.context["formulario"].errors,
        )

        self.assertFalse(
            Progreso.objects.filter(
                consulta=self.consulta_nueva
            ).exists()
        )

    # =====================================================
    # 4. IMPEDIR CAMBIAR LA CONSULTA DESDE POST
    # =====================================================

    def test_post_no_cambia_consulta_asignada(self):
        datos = self.datos_validos(
            consulta=str(self.consulta_ajena.pk)
        )

        respuesta = self.client.post(
            self.url_registro(),
            datos,
        )

        self.assertEqual(respuesta.status_code, 302)

        nuevo = Progreso.objects.get(
            consulta=self.consulta_nueva
        )

        self.assertEqual(
            nuevo.consulta_id,
            self.consulta_nueva.pk,
        )

    # =====================================================
    # 5. EVITAR DOS REGISTROS EN UNA CONSULTA
    # =====================================================

    def test_registro_duplicado_redirige_a_edicion(self):
        respuesta = self.client.post(
            self.url_registro(self.consulta_principal),
            self.datos_validos(),
        )

        self.assertRedirects(
            respuesta,
            self.url_edicion(),
            fetch_redirect_response=False,
        )

        self.assertEqual(
            Progreso.objects.filter(
                consulta=self.consulta_principal
            ).count(),
            1,
        )

    # =====================================================
    # 6. NO REGISTRAR EN CONSULTA FINALIZADA
    # =====================================================

    def test_no_registra_en_consulta_finalizada(self):
        self.cita_nueva.estado = Cita.Estado.FINALIZADA
        self.cita_nueva.save(
            update_fields=["estado"]
        )

        respuesta = self.client.post(
            self.url_registro(),
            self.datos_validos(),
        )

        self.assertEqual(respuesta.status_code, 302)

        self.assertFalse(
            Progreso.objects.filter(
                consulta=self.consulta_nueva
            ).exists()
        )

    # =====================================================
    # 7. NO REGISTRAR EN CITA CONFIRMADA
    # =====================================================

    def test_no_registra_en_cita_confirmada(self):
        self.cita_nueva.estado = Cita.Estado.CONFIRMADA
        self.cita_nueva.save(
            update_fields=["estado"]
        )

        respuesta = self.client.post(
            self.url_registro(),
            self.datos_validos(),
        )

        self.assertEqual(respuesta.status_code, 302)

        self.assertFalse(
            Progreso.objects.filter(
                consulta=self.consulta_nueva
            ).exists()
        )

    # =====================================================
    # 8. EDITAR PROGRESO EXISTENTE
    # =====================================================

    def test_fisioterapeuta_edita_progreso(self):
        respuesta = self.client.post(
            self.url_edicion(),
            self.datos_validos(
                movilidad="Movilidad recuperada.",
                nivel_dolor="2",
            ),
        )

        self.assertEqual(respuesta.status_code, 302)

        self.progreso.refresh_from_db()

        self.assertEqual(
            self.progreso.movilidad,
            "Movilidad recuperada.",
        )
        self.assertEqual(
            self.progreso.nivel_dolor,
            2,
        )

    # =====================================================
    # 9. NO GUARDAR EDICIÓN INVÁLIDA
    # =====================================================

    def test_edicion_invalida_no_guarda(self):
        respuesta = self.client.post(
            self.url_edicion(),
            self.datos_validos(nivel_dolor="-5"),
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(
            "nivel_dolor",
            respuesta.context["formulario"].errors,
        )

        self.progreso.refresh_from_db()

        self.assertEqual(
            self.progreso.nivel_dolor,
            5,
        )

    # =====================================================
    # 10. NO EDITAR PROGRESO FINALIZADO
    # =====================================================

    def test_no_edita_progreso_finalizado(self):
        self.cita_principal.estado = Cita.Estado.FINALIZADA
        self.cita_principal.save(
            update_fields=["estado"]
        )

        respuesta = self.client.post(
            self.url_edicion(),
            self.datos_validos(
                nivel_dolor="1"
            ),
        )

        self.assertEqual(respuesta.status_code, 302)

        self.progreso.refresh_from_db()

        self.assertEqual(
            self.progreso.nivel_dolor,
            5,
        )

    # =====================================================
    # 11. CONSULTAR PROGRESO FINALIZADO
    # =====================================================

    def test_detalle_permite_consulta_finalizada(self):
        self.cita_principal.estado = Cita.Estado.FINALIZADA
        self.cita_principal.save(
            update_fields=["estado"]
        )

        respuesta = self.client.get(
            self.url_detalle()
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            respuesta.context["progreso"].pk,
            self.progreso.pk,
        )

    # =====================================================
    # 12. BLOQUEAR FISIOTERAPEUTA NO ASIGNADO
    # =====================================================

    def test_fisioterapeuta_ajeno_no_puede_acceder(self):
        self.client.force_login(
            self.usuario_otro_fisio
        )

        urls = [
            self.url_registro(),
            self.url_edicion(),
            self.url_detalle(),
        ]

        for url in urls:
            with self.subTest(url=url):
                respuesta = self.client.get(url)

                self.assertEqual(
                    respuesta.status_code,
                    403,
                )

    # =====================================================
    # 13. ADMINISTRADOR PUEDE REGISTRAR PROGRESO
    # =====================================================

    def test_administrador_puede_registrar_progreso(self):
        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.url_registro(),
            self.datos_validos(),
        )

        self.assertEqual(respuesta.status_code, 302)

        self.assertTrue(
            Progreso.objects.filter(
                consulta=self.consulta_nueva
            ).exists()
        )

    # =====================================================
    # 14. PACIENTE VE SU PROPIO PROGRESO
    # =====================================================

    def test_paciente_ve_su_progreso(self):
        self.client.force_login(
            self.usuario_paciente
        )

        respuesta = self.client.get(
            self.url_paciente()
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            respuesta.context["progreso"].pk,
            self.progreso.pk,
        )

    # =====================================================
    # 15. PACIENTE NO VE PROGRESO AJENO
    # =====================================================

    def test_paciente_no_ve_progreso_ajeno(self):
        self.client.force_login(
            self.usuario_paciente
        )

        respuesta = self.client.get(
            self.url_paciente(self.consulta_ajena)
        )

        self.assertEqual(
            respuesta.status_code,
            404,
        )

    # =====================================================
    # 16. PACIENTE NO MODIFICA PROGRESOS
    # =====================================================

    def test_paciente_no_accede_a_vistas_clinicas(self):
        self.client.force_login(
            self.usuario_paciente
        )

        urls = [
            self.url_registro(),
            self.url_edicion(),
            self.url_detalle(),
        ]

        for url in urls:
            with self.subTest(url=url):
                respuesta = self.client.get(url)

                self.assertEqual(
                    respuesta.status_code,
                    302,
                )

    # =====================================================
    # 17. BLOQUEAR FISIOTERAPEUTA DESACTIVADO
    # =====================================================

    def test_fisioterapeuta_inactivo_no_accede(self):
        self.perfil_fisio.activo = False
        self.perfil_fisio.save(
            update_fields=["activo"]
        )

        respuesta = self.client.get(
            self.url_detalle()
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

    # =====================================================
    # 18. BLOQUEAR USUARIO SIN INICIAR SESIÓN
    # =====================================================

    def test_sin_sesion_redirige_al_login(self):
        self.client.logout()

        respuesta = self.client.get(
            self.url_detalle()
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )
