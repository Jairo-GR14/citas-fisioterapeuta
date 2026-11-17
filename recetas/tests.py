
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

from .forms import RecetaForm
from .models import Receta


# =========================================================
# PRUEBAS DEL FORMULARIO
# =========================================================

class RecetaFormTests(TestCase):

    def test_indicaciones_son_obligatorias(self):

        formulario = RecetaForm(data={
            "indicaciones": "",
        })

        self.assertFalse(formulario.is_valid())
        self.assertIn("indicaciones", formulario.errors)

    def test_indicaciones_no_aceptan_solo_espacios(self):

        formulario = RecetaForm(data={
            "indicaciones": "   ",
        })

        self.assertFalse(formulario.is_valid())
        self.assertIn("indicaciones", formulario.errors)

    def test_campos_complementarios_son_opcionales(self):

        formulario = RecetaForm(data={
            "indicaciones": (
                "Caminar con apoyo durante la recuperación."
            ),
        })

        self.assertTrue(
            formulario.is_valid(),
            formulario.errors,
        )

    def test_formulario_completo_es_valido(self):

        formulario = RecetaForm(data={
            "indicaciones": "Realizar movimientos sin dolor.",
            "ejercicios": "Flexión de rodilla.",
            "repeticiones": "3 series de 10",
            "frecuencia": "2 veces al día",
            "duracion": "4 semanas",
            "recomendaciones": "Descansar entre series.",
            "restricciones": "Evitar cargas pesadas.",
        })

        self.assertTrue(
            formulario.is_valid(),
            formulario.errors,
        )


# =========================================================
# PRUEBAS DE VISTAS, PERMISOS E INTEGRACIÓN
# =========================================================

class RecetaVistasTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        Usuario = get_user_model()

        # ADMINISTRADOR
        cls.admin = Usuario.objects.create_user(
            username="admin_recetas",
            password="Prueba12345!",
        )

        PerfilUsuario.objects.create(
            usuario=cls.admin,
            rol=PerfilUsuario.Rol.ADMINISTRADOR,
        )

        # FISIOTERAPEUTA PRINCIPAL
        cls.usuario_fisio = Usuario.objects.create_user(
            username="fisio_recetas",
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
            username="otro_fisio_recetas",
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
            username="paciente_recetas",
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
            username="otro_paciente_recetas",
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
        servicio = Servicio.objects.create(
            nombre="Servicio de prueba para recetas",
            precio_base=Decimal("400.00"),
        )

        # MOTIVO
        motivo = MotivoConsulta.objects.create(
            nombre="Motivo de prueba para recetas",
        )

        # CITA PRINCIPAL
        cls.cita = Cita.objects.create(
            paciente=cls.paciente,
            fisioterapeuta=cls.fisio,
            servicio=servicio,
            motivo=motivo,
            fecha=date(2026, 11, 16),
            hora=time(10, 0),
            estado=Cita.Estado.EN_PROCESO,
            costo_estimado=Decimal("400.00"),
        )

        cls.consulta = Consulta.objects.create(
            cita=cls.cita,
            fecha_inicio=timezone.now(),
        )

        # RECETA PRINCIPAL
        cls.receta = Receta.objects.create(
            consulta=cls.consulta,
            indicaciones="Realizar ejercicios suaves.",
            ejercicios="Movilidad de rodilla.",
            repeticiones="3 series de 10",
        )

        # CITA DE OTRO FISIOTERAPEUTA
        cls.cita_ajena = Cita.objects.create(
            paciente=cls.otro_paciente,
            fisioterapeuta=cls.otro_fisio,
            servicio=servicio,
            motivo=motivo,
            fecha=date(2026, 11, 16),
            hora=time(11, 0),
            estado=Cita.Estado.EN_PROCESO,
            costo_estimado=Decimal("400.00"),
        )

        cls.consulta_ajena = Consulta.objects.create(
            cita=cls.cita_ajena,
            fecha_inicio=timezone.now(),
        )

        cls.receta_ajena = Receta.objects.create(
            consulta=cls.consulta_ajena,
            indicaciones="Indicaciones de otro paciente.",
        )

    def setUp(self):

        self.client.force_login(self.usuario_fisio)

    # =====================================================
    # FUNCIONES AUXILIARES
    # =====================================================

    def datos_validos(self, **cambios):

        datos = {
            "indicaciones": "Nueva indicación terapéutica.",
            "ejercicios": "Ejercicios de equilibrio.",
            "repeticiones": "2 series de 10",
            "frecuencia": "Diaria",
            "duracion": "2 semanas",
            "recomendaciones": "Descansar si aparece dolor.",
            "restricciones": "Evitar saltos.",
        }

        datos.update(cambios)

        return datos

    def url_registro(self, consulta=None):

        consulta = consulta or self.consulta

        return reverse(
            "recetas:registrar_receta",
            args=[consulta.pk],
        )

    def url_lista(self, consulta=None):

        consulta = consulta or self.consulta

        return reverse(
            "recetas:lista_recetas",
            args=[consulta.pk],
        )

    def url_detalle(self, receta=None):

        receta = receta or self.receta

        return reverse(
            "recetas:detalle_receta",
            args=[receta.pk],
        )

    def url_edicion(self, receta=None):

        receta = receta or self.receta

        return reverse(
            "recetas:editar_receta",
            args=[receta.pk],
        )

    def url_paciente(self, receta=None):

        receta = receta or self.receta

        return reverse(
            "recetas:receta_paciente",
            args=[receta.pk],
        )

    # =====================================================
    # 1. VER FORMULARIO DE REGISTRO
    # =====================================================

    def test_fisioterapeuta_ve_formulario_registro(self):

        respuesta = self.client.get(
            self.url_registro()
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertIn(
            "formulario",
            respuesta.context,
        )

    # =====================================================
    # 2. REGISTRAR RECETA
    # =====================================================

    def test_fisioterapeuta_registra_receta(self):

        cantidad = Receta.objects.count()

        respuesta = self.client.post(
            self.url_registro(),
            self.datos_validos(),
        )

        self.assertEqual(respuesta.status_code, 302)

        self.assertEqual(
            Receta.objects.count(),
            cantidad + 1,
        )

        nueva = Receta.objects.get(
            indicaciones="Nueva indicación terapéutica."
        )

        self.assertEqual(
            nueva.consulta_id,
            self.consulta.pk,
        )

    # =====================================================
    # 3. NO CREAR RECETA SIN INDICACIONES
    # =====================================================

    def test_indicaciones_invalidas_no_crean_receta(self):

        cantidad = Receta.objects.count()

        respuesta = self.client.post(
            self.url_registro(),
            self.datos_validos(indicaciones=" "),
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertIn(
            "indicaciones",
            respuesta.context["formulario"].errors,
        )

        self.assertEqual(
            Receta.objects.count(),
            cantidad,
        )

    # =====================================================
    # 4. NO PERMITIR CAMBIAR CONSULTA DESDE EL POST
    # =====================================================

    def test_post_no_permite_cambiar_consulta_asignada(self):

        respuesta = self.client.post(
            self.url_registro(),
            self.datos_validos(
                consulta=str(self.consulta_ajena.pk)
            ),
        )

        self.assertEqual(respuesta.status_code, 302)

        nueva = Receta.objects.get(
            indicaciones="Nueva indicación terapéutica."
        )

        self.assertEqual(
            nueva.consulta_id,
            self.consulta.pk,
        )

    # =====================================================
    # 5. NO REGISTRAR EN CONSULTA FINALIZADA
    # =====================================================

    def test_no_registra_en_consulta_finalizada(self):

        self.cita.estado = Cita.Estado.FINALIZADA

        self.cita.save(
            update_fields=["estado"]
        )

        cantidad = Receta.objects.count()

        respuesta = self.client.post(
            self.url_registro(),
            self.datos_validos(),
        )

        self.assertEqual(respuesta.status_code, 302)

        self.assertEqual(
            Receta.objects.count(),
            cantidad,
        )

    # =====================================================
    # 6. NO REGISTRAR SI LA CITA NO ESTÁ EN PROCESO
    # =====================================================

    def test_no_registra_en_consulta_no_iniciada(self):

        self.cita.estado = Cita.Estado.CONFIRMADA

        self.cita.save(
            update_fields=["estado"]
        )

        cantidad = Receta.objects.count()

        respuesta = self.client.post(
            self.url_registro(),
            self.datos_validos(),
        )

        self.assertEqual(respuesta.status_code, 302)

        self.assertEqual(
            Receta.objects.count(),
            cantidad,
        )

    # =====================================================
    # 7. LISTAR SOLO RECETAS DE LA CONSULTA
    # =====================================================

    def test_listado_muestra_solo_recetas_de_la_consulta(self):

        respuesta = self.client.get(
            self.url_lista()
        )

        self.assertEqual(respuesta.status_code, 200)

        recetas = list(
            respuesta.context["recetas"]
        )

        self.assertIn(
            self.receta,
            recetas,
        )

        self.assertNotIn(
            self.receta_ajena,
            recetas,
        )

    # =====================================================
    # 8. VER DETALLE DE RECETA
    # =====================================================

    def test_detalle_devuelve_receta_correcta(self):

        respuesta = self.client.get(
            self.url_detalle()
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            respuesta.context["receta"].pk,
            self.receta.pk,
        )

    # =====================================================
    # 9. EDITAR RECETA
    # =====================================================

    def test_fisioterapeuta_puede_editar_receta(self):

        respuesta = self.client.post(
            self.url_edicion(),
            self.datos_validos(
                indicaciones="Indicaciones actualizadas."
            ),
        )

        self.assertEqual(respuesta.status_code, 302)

        self.receta.refresh_from_db()

        self.assertEqual(
            self.receta.indicaciones,
            "Indicaciones actualizadas.",
        )

    # =====================================================
    # 10. RECHAZAR EDICIÓN INVÁLIDA
    # =====================================================

    def test_edicion_invalida_no_guarda_cambios(self):

        respuesta = self.client.post(
            self.url_edicion(),
            self.datos_validos(
                indicaciones=""
            ),
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertIn(
            "indicaciones",
            respuesta.context["formulario"].errors,
        )

        self.receta.refresh_from_db()

        self.assertEqual(
            self.receta.indicaciones,
            "Realizar ejercicios suaves.",
        )

    # =====================================================
    # 11. BLOQUEAR EDICIÓN TRAS FINALIZAR
    # =====================================================

    def test_no_edita_receta_si_consulta_finalizada(self):

        self.cita.estado = Cita.Estado.FINALIZADA

        self.cita.save(
            update_fields=["estado"]
        )

        respuesta = self.client.post(
            self.url_edicion(),
            self.datos_validos(
                indicaciones="Cambio indebido."
            ),
        )

        self.assertEqual(respuesta.status_code, 302)

        self.receta.refresh_from_db()

        self.assertEqual(
            self.receta.indicaciones,
            "Realizar ejercicios suaves.",
        )

    # =====================================================
    # 12. PERMITIR LECTURA DE RECETAS FINALIZADAS
    # =====================================================

    def test_consulta_finalizada_permite_lectura(self):

        self.cita.estado = Cita.Estado.FINALIZADA

        self.cita.save(
            update_fields=["estado"]
        )

        self.assertEqual(
            self.client.get(
                self.url_lista()
            ).status_code,
            200,
        )

        self.assertEqual(
            self.client.get(
                self.url_detalle()
            ).status_code,
            200,
        )

    # =====================================================
    # 13. IMPEDIR ACCESO A CONSULTAS AJENAS
    # =====================================================

    def test_fisioterapeuta_ajeno_no_puede_acceder(self):

        for url in (
            self.url_registro(self.consulta_ajena),
            self.url_lista(self.consulta_ajena),
            self.url_detalle(self.receta_ajena),
            self.url_edicion(self.receta_ajena),
        ):

            with self.subTest(url=url):

                self.assertEqual(
                    self.client.get(url).status_code,
                    403,
                )

    # =====================================================
    # 14. PACIENTE VE SU PROPIA RECETA
    # =====================================================

    def test_paciente_puede_ver_su_receta(self):

        self.client.force_login(
            self.usuario_paciente
        )

        respuesta = self.client.get(
            self.url_paciente()
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            respuesta.context["receta"].pk,
            self.receta.pk,
        )

    # =====================================================
    # 15. PACIENTE NO VE RECETAS DE OTROS
    # =====================================================

    def test_paciente_no_puede_ver_receta_ajena(self):

        self.client.force_login(
            self.usuario_paciente
        )

        respuesta = self.client.get(
            self.url_paciente(self.receta_ajena)
        )

        self.assertEqual(
            respuesta.status_code,
            404,
        )

    # =====================================================
    # 16. PACIENTE NO ACCEDE A VISTAS CLÍNICAS
    # =====================================================

    def test_paciente_no_puede_acceder_a_vistas_clinicas(self):

        self.client.force_login(
            self.usuario_paciente
        )

        for url in (
            self.url_registro(),
            self.url_lista(),
            self.url_detalle(),
            self.url_edicion(),
        ):

            with self.subTest(url=url):

                self.assertEqual(
                    self.client.get(url).status_code,
                    302,
                )

    # =====================================================
    # 17. ADMINISTRADOR PUEDE REGISTRAR RECETAS
    # =====================================================

    def test_administrador_puede_registrar_receta(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.url_registro(),
            self.datos_validos(),
        )

        self.assertEqual(respuesta.status_code, 302)

        self.assertTrue(
            Receta.objects.filter(
                consulta=self.consulta,
                indicaciones="Nueva indicación terapéutica.",
            ).exists()
        )

    # =====================================================
    # 18. BLOQUEAR FISIOTERAPEUTA INACTIVO
    # =====================================================

    def test_fisioterapeuta_inactivo_no_puede_acceder(self):

        self.perfil_fisio.activo = False

        self.perfil_fisio.save(
            update_fields=["activo"]
        )

        self.assertEqual(
            self.client.get(
                self.url_lista()
            ).status_code,
            403,
        )

    # =====================================================
    # 19. USUARIO SIN INICIAR SESIÓN
    # =====================================================

    def test_sin_iniciar_sesion_redirige_a_login(self):

        self.client.logout()

        self.assertEqual(
            self.client.get(
                self.url_lista()
            ).status_code,
            302,
        )

    # =====================================================
    # 20. RECETA INEXISTENTE
    # =====================================================

    def test_receta_inexistente_devuelve_404(self):

        url = reverse(
            "recetas:detalle_receta",
            args=[999999],
        )

        self.assertEqual(
            self.client.get(url).status_code,
            404,
        )
