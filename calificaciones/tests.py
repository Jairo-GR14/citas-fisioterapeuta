
from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from citas.models import Cita, MotivoConsulta
from fisioterapeutas.models import Fisioterapeuta
from pacientes.models import Paciente
from precios.models import Servicio
from usuarios.models import PerfilUsuario

from .forms import CalificacionForm
from .models import Calificacion


# =========================================================
# DATOS COMPARTIDOS
# =========================================================

class DatosCalificaciones(TestCase):

    @classmethod
    def setUpTestData(cls):

        Usuario = get_user_model()

        def crear_cuenta(nombre, rol):

            usuario = Usuario.objects.create_user(
                username=nombre,
                password="Prueba12345!",
                email=f"{nombre}@ejemplo.com",
                first_name=nombre,
                last_name="Prueba",
            )

            perfil = PerfilUsuario.objects.create(
                usuario=usuario,
                rol=rol,
            )

            return usuario, perfil

        cls.admin, cls.perfil_admin = crear_cuenta(
            "admin_calificaciones_tests",
            PerfilUsuario.Rol.ADMINISTRADOR,
        )

        cls.recepcionista, cls.perfil_recep = crear_cuenta(
            "recep_calificaciones_tests",
            PerfilUsuario.Rol.RECEPCIONISTA,
        )

        cls.usuario_fisio, cls.perfil_fisio = crear_cuenta(
            "fisio_calificaciones_tests",
            PerfilUsuario.Rol.FISIOTERAPEUTA,
        )

        cls.ana, cls.perfil_ana = crear_cuenta(
            "ana_calificaciones_tests",
            PerfilUsuario.Rol.PACIENTE,
        )

        cls.bruno, cls.perfil_bruno = crear_cuenta(
            "bruno_calificaciones_tests",
            PerfilUsuario.Rol.PACIENTE,
        )

        cls.fisio = Fisioterapeuta.objects.create(
            usuario=cls.perfil_fisio,
            especialidad="Rehabilitación física",
        )

        cls.paciente_ana = Paciente.objects.create(
            usuario=cls.perfil_ana
        )

        cls.paciente_bruno = Paciente.objects.create(
            usuario=cls.perfil_bruno
        )

        cls.servicio = Servicio.objects.create(
            nombre="Consulta para calificaciones",
            precio_base=Decimal("450.00"),
        )

        cls.motivo = MotivoConsulta.objects.create(
            nombre="Evaluación para calificaciones"
        )

        def crear_cita(paciente, estado, dias, hora):

            return Cita.objects.create(
                paciente=paciente,
                fisioterapeuta=cls.fisio,
                servicio=cls.servicio,
                motivo=cls.motivo,
                fecha=(
                    timezone.localdate()
                    + timedelta(days=dias)
                ),
                hora=time(hora, 0),
                estado=estado,
                costo_estimado=Decimal("450.00"),
            )

        cls.cita_ana_finalizada = crear_cita(
            cls.paciente_ana,
            Cita.Estado.FINALIZADA,
            -15,
            9,
        )

        cls.cita_ana_otra = crear_cita(
            cls.paciente_ana,
            Cita.Estado.FINALIZADA,
            -10,
            10,
        )

        cls.cita_bruno_finalizada = crear_cita(
            cls.paciente_bruno,
            Cita.Estado.FINALIZADA,
            -12,
            11,
        )

        cls.cita_programada = crear_cita(
            cls.paciente_ana,
            Cita.Estado.PROGRAMADA,
            10,
            12,
        )

        cls.cita_confirmada = crear_cita(
            cls.paciente_ana,
            Cita.Estado.CONFIRMADA,
            11,
            13,
        )

        cls.cita_proceso = crear_cita(
            cls.paciente_ana,
            Cita.Estado.EN_PROCESO,
            -1,
            14,
        )

        cls.cita_cancelada = crear_cita(
            cls.paciente_ana,
            Cita.Estado.CANCELADA,
            -2,
            15,
        )

    def ruta(self, nombre, identificador=None):

        if identificador is None:
            return reverse(
                f"calificaciones:{nombre}"
            )

        return reverse(
            f"calificaciones:{nombre}",
            args=[identificador],
        )

    def datos_calificacion(self, **cambios):

        datos = {
            "puntuacion": "5",
            "comentario": "Excelente atención profesional.",
        }

        datos.update(cambios)
        return datos

    def crear_calificacion(
        self,
        cita=None,
        puntuacion=5,
        comentario="Buena atención.",
    ):

        if cita is None:
            cita = self.cita_ana_finalizada

        return Calificacion.objects.create(
            cita=cita,
            puntuacion=puntuacion,
            comentario=comentario,
        )

    def comprobar_cita_no_calificable(self, cita):

        self.client.force_login(self.ana)

        respuesta = self.client.post(
            self.ruta(
                "registrar_calificacion",
                cita.pk,
            ),
            self.datos_calificacion(),
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:redireccion_por_rol"),
            fetch_redirect_response=False,
        )

        self.assertFalse(
            Calificacion.objects.filter(
                cita=cita
            ).exists()
        )


# =========================================================
# 1. FORMULARIOS Y UNICIDAD
# 10 PRUEBAS
# =========================================================

class FormulariosCalificacionesTests(DatosCalificaciones):

    # 1
    def test_formulario_acepta_cinco_estrellas(self):

        formulario = CalificacionForm(
            data=self.datos_calificacion()
        )

        self.assertTrue(
            formulario.is_valid(),
            formulario.errors,
        )

        self.assertEqual(
            formulario.cleaned_data["puntuacion"],
            5,
        )

    # 2
    def test_formulario_acepta_una_estrella(self):

        formulario = CalificacionForm(
            data=self.datos_calificacion(
                puntuacion="1"
            )
        )

        self.assertTrue(
            formulario.is_valid(),
            formulario.errors,
        )

        self.assertEqual(
            formulario.cleaned_data["puntuacion"],
            1,
        )

    # 3
    def test_formulario_permite_comentario_vacio(self):

        formulario = CalificacionForm(
            data=self.datos_calificacion(
                comentario=""
            )
        )

        self.assertTrue(
            formulario.is_valid(),
            formulario.errors,
        )

    # 4
    def test_formulario_rechaza_cero_estrellas(self):

        formulario = CalificacionForm(
            data=self.datos_calificacion(
                puntuacion="0"
            )
        )

        self.assertFalse(formulario.is_valid())
        self.assertIn("puntuacion", formulario.errors)

    # 5
    def test_formulario_rechaza_seis_estrellas(self):

        formulario = CalificacionForm(
            data=self.datos_calificacion(
                puntuacion="6"
            )
        )

        self.assertFalse(formulario.is_valid())
        self.assertIn("puntuacion", formulario.errors)

    # 6
    def test_formulario_rechaza_puntuacion_negativa(self):

        formulario = CalificacionForm(
            data=self.datos_calificacion(
                puntuacion="-1"
            )
        )

        self.assertFalse(formulario.is_valid())
        self.assertIn("puntuacion", formulario.errors)

    # 7
    def test_formulario_rechaza_puntuacion_en_texto(self):

        formulario = CalificacionForm(
            data=self.datos_calificacion(
                puntuacion="excelente"
            )
        )

        self.assertFalse(formulario.is_valid())
        self.assertIn("puntuacion", formulario.errors)

    # 8
    def test_formulario_rechaza_puntuacion_decimal(self):

        formulario = CalificacionForm(
            data=self.datos_calificacion(
                puntuacion="3.5"
            )
        )

        self.assertFalse(formulario.is_valid())
        self.assertIn("puntuacion", formulario.errors)

    # 9
    def test_formulario_requiere_puntuacion(self):

        formulario = CalificacionForm(
            data={
                "comentario": "Sin estrellas."
            }
        )

        self.assertFalse(formulario.is_valid())
        self.assertIn("puntuacion", formulario.errors)

    # 10
    def test_modelo_no_permite_dos_calificaciones_por_cita(self):

        self.crear_calificacion()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():

                Calificacion.objects.create(
                    cita=self.cita_ana_finalizada,
                    puntuacion=3,
                    comentario="Intento duplicado",
                )

        self.assertEqual(
            Calificacion.objects.filter(
                cita=self.cita_ana_finalizada
            ).count(),
            1,
        )


# =========================================================
# 2. REGISTRAR CALIFICACIONES
# 20 PRUEBAS
# =========================================================

class RegistrarCalificacionesTests(DatosCalificaciones):

    # 11
    def test_paciente_abre_formulario_de_cita_finalizada(self):

        self.client.force_login(self.ana)

        respuesta = self.client.get(
            self.ruta(
                "registrar_calificacion",
                self.cita_ana_finalizada.pk,
            )
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            respuesta.context["cita"],
            self.cita_ana_finalizada,
        )

        self.assertIn(
            "puntuacion",
            respuesta.context["formulario"].fields,
        )

    # 12
    def test_paciente_registra_calificacion_correctamente(self):

        self.client.force_login(self.ana)

        respuesta = self.client.post(
            self.ruta(
                "registrar_calificacion",
                self.cita_ana_finalizada.pk,
            ),
            self.datos_calificacion(
                puntuacion="4",
                comentario="Muy buena experiencia.",
            ),
        )

        calificacion = Calificacion.objects.get(
            cita=self.cita_ana_finalizada
        )

        self.assertRedirects(
            respuesta,
            self.ruta(
                "detalle_calificacion",
                calificacion.pk,
            ),
            fetch_redirect_response=False,
        )

        self.assertEqual(
            calificacion.puntuacion,
            4,
        )

        self.assertEqual(
            calificacion.comentario,
            "Muy buena experiencia.",
        )

    # 13
    def test_registro_permite_comentario_vacio(self):

        self.client.force_login(self.ana)

        respuesta = self.client.post(
            self.ruta(
                "registrar_calificacion",
                self.cita_ana_finalizada.pk,
            ),
            self.datos_calificacion(
                comentario=""
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        calificacion = Calificacion.objects.get(
            cita=self.cita_ana_finalizada
        )

        self.assertEqual(
            calificacion.comentario,
            "",
        )

    # 14
    def test_registro_sin_sesion_redirige_al_login(self):

        respuesta = self.client.get(
            self.ruta(
                "registrar_calificacion",
                self.cita_ana_finalizada.pk,
            )
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:login"),
            fetch_redirect_response=False,
        )

    # 15
    def test_paciente_no_califica_cita_de_otro(self):

        self.client.force_login(self.ana)

        respuesta = self.client.post(
            self.ruta(
                "registrar_calificacion",
                self.cita_bruno_finalizada.pk,
            ),
            self.datos_calificacion(),
        )

        self.assertEqual(
            respuesta.status_code,
            404,
        )

        self.assertFalse(
            Calificacion.objects.filter(
                cita=self.cita_bruno_finalizada
            ).exists()
        )

    # 16
    def test_no_califica_cita_programada(self):

        self.comprobar_cita_no_calificable(
            self.cita_programada
        )

    # 17
    def test_no_califica_cita_confirmada(self):

        self.comprobar_cita_no_calificable(
            self.cita_confirmada
        )

    # 18
    def test_no_califica_cita_en_proceso(self):

        self.comprobar_cita_no_calificable(
            self.cita_proceso
        )

    # 19
    def test_no_califica_cita_cancelada(self):

        self.comprobar_cita_no_calificable(
            self.cita_cancelada
        )

    # 20
    def test_registro_rechaza_puntuacion_cero(self):

        self.client.force_login(self.ana)

        respuesta = self.client.post(
            self.ruta(
                "registrar_calificacion",
                self.cita_ana_finalizada.pk,
            ),
            self.datos_calificacion(
                puntuacion="0"
            ),
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertIn(
            "puntuacion",
            respuesta.context["formulario"].errors,
        )

        self.assertEqual(
            Calificacion.objects.count(),
            0,
        )

    # 21
    def test_registro_rechaza_puntuacion_seis(self):

        self.client.force_login(self.ana)

        respuesta = self.client.post(
            self.ruta(
                "registrar_calificacion",
                self.cita_ana_finalizada.pk,
            ),
            self.datos_calificacion(
                puntuacion="6"
            ),
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            Calificacion.objects.count(),
            0,
        )

    # 22
    def test_registro_rechaza_puntuacion_ausente(self):

        self.client.force_login(self.ana)

        respuesta = self.client.post(
            self.ruta(
                "registrar_calificacion",
                self.cita_ana_finalizada.pk,
            ),
            {
                "comentario": "Sin puntuación"
            },
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertIn(
            "puntuacion",
            respuesta.context["formulario"].errors,
        )

    # 23
    def test_cita_ya_calificada_get_redirige_al_detalle(self):

        calificacion = self.crear_calificacion()

        self.client.force_login(self.ana)

        respuesta = self.client.get(
            self.ruta(
                "registrar_calificacion",
                self.cita_ana_finalizada.pk,
            )
        )

        self.assertRedirects(
            respuesta,
            self.ruta(
                "detalle_calificacion",
                calificacion.pk,
            ),
            fetch_redirect_response=False,
        )

    # 24
    def test_cita_ya_calificada_no_se_sobrescribe(self):

        calificacion = self.crear_calificacion(
            puntuacion=5,
            comentario="Original",
        )

        self.client.force_login(self.ana)

        respuesta = self.client.post(
            self.ruta(
                "registrar_calificacion",
                self.cita_ana_finalizada.pk,
            ),
            self.datos_calificacion(
                puntuacion="1",
                comentario="Intento de cambio",
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        calificacion.refresh_from_db()

        self.assertEqual(
            calificacion.puntuacion,
            5,
        )

        self.assertEqual(
            calificacion.comentario,
            "Original",
        )

        self.assertEqual(
            Calificacion.objects.count(),
            1,
        )

    # 25
    def test_no_puede_asignar_otra_cita_por_post(self):

        self.client.force_login(self.ana)

        datos = self.datos_calificacion()

        datos["cita"] = str(
            self.cita_bruno_finalizada.pk
        )

        respuesta = self.client.post(
            self.ruta(
                "registrar_calificacion",
                self.cita_ana_finalizada.pk,
            ),
            datos,
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.assertTrue(
            Calificacion.objects.filter(
                cita=self.cita_ana_finalizada
            ).exists()
        )

        self.assertFalse(
            Calificacion.objects.filter(
                cita=self.cita_bruno_finalizada
            ).exists()
        )

    # 26
    def test_fisioterapeuta_no_puede_calificar(self):

        self.client.force_login(
            self.usuario_fisio
        )

        respuesta = self.client.post(
            self.ruta(
                "registrar_calificacion",
                self.cita_ana_finalizada.pk,
            ),
            self.datos_calificacion(),
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:redireccion_por_rol"),
            fetch_redirect_response=False,
        )

    # 27
    def test_recepcionista_no_puede_calificar(self):

        self.client.force_login(
            self.recepcionista
        )

        respuesta = self.client.post(
            self.ruta(
                "registrar_calificacion",
                self.cita_ana_finalizada.pk,
            ),
            self.datos_calificacion(),
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:redireccion_por_rol"),
            fetch_redirect_response=False,
        )

    # 28
    def test_administrador_normal_no_puede_calificar(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "registrar_calificacion",
                self.cita_ana_finalizada.pk,
            ),
            self.datos_calificacion(),
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:redireccion_por_rol"),
            fetch_redirect_response=False,
        )

    # 29
    def test_paciente_con_perfil_inactivo_no_califica(self):

        self.perfil_ana.activo = False

        self.perfil_ana.save(
            update_fields=["activo"]
        )

        self.client.force_login(self.ana)

        respuesta = self.client.post(
            self.ruta(
                "registrar_calificacion",
                self.cita_ana_finalizada.pk,
            ),
            self.datos_calificacion(),
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

        self.assertEqual(
            Calificacion.objects.count(),
            0,
        )

    # 30
    def test_registrar_cita_inexistente_devuelve_404(self):

        self.client.force_login(self.ana)

        respuesta = self.client.get(
            self.ruta(
                "registrar_calificacion",
                999999,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            404,
        )


# =========================================================
# 3. DETALLE DE CALIFICACIONES
# 8 PRUEBAS
# =========================================================

class DetalleCalificacionesTests(DatosCalificaciones):

    # 31
    def test_paciente_ve_su_calificacion(self):

        calificacion = self.crear_calificacion()

        self.client.force_login(self.ana)

        respuesta = self.client.get(
            self.ruta(
                "detalle_calificacion",
                calificacion.pk,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertEqual(
            respuesta.context["calificacion"],
            calificacion,
        )

    # 32
    def test_paciente_no_ve_calificacion_ajena(self):

        calificacion = self.crear_calificacion(
            cita=self.cita_bruno_finalizada
        )

        self.client.force_login(self.ana)

        respuesta = self.client.get(
            self.ruta(
                "detalle_calificacion",
                calificacion.pk,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            404,
        )

    # 33
    def test_administrador_ve_calificacion_de_paciente(self):

        calificacion = self.crear_calificacion()

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.ruta(
                "detalle_calificacion",
                calificacion.pk,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

    # 34
    def test_superusuario_sin_perfil_ve_calificacion(self):

        superusuario = (
            get_user_model().objects.create_superuser(
                username="super_calificaciones_tests",
                email="super_calificaciones@ejemplo.com",
                password="Prueba12345!",
            )
        )

        calificacion = self.crear_calificacion()

        self.client.force_login(superusuario)

        respuesta = self.client.get(
            self.ruta(
                "detalle_calificacion",
                calificacion.pk,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

    # 35
    def test_fisioterapeuta_no_accede_al_detalle(self):

        calificacion = self.crear_calificacion()

        self.client.force_login(
            self.usuario_fisio
        )

        respuesta = self.client.get(
            self.ruta(
                "detalle_calificacion",
                calificacion.pk,
            )
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:redireccion_por_rol"),
            fetch_redirect_response=False,
        )

    # 36
    def test_recepcionista_no_accede_al_detalle(self):

        calificacion = self.crear_calificacion()

        self.client.force_login(
            self.recepcionista
        )

        respuesta = self.client.get(
            self.ruta(
                "detalle_calificacion",
                calificacion.pk,
            )
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:redireccion_por_rol"),
            fetch_redirect_response=False,
        )

    # 37
    def test_detalle_sin_sesion_redirige(self):

        calificacion = self.crear_calificacion()

        respuesta = self.client.get(
            self.ruta(
                "detalle_calificacion",
                calificacion.pk,
            )
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:login"),
            fetch_redirect_response=False,
        )

    # 38
    def test_detalle_inexistente_devuelve_404(self):

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.ruta(
                "detalle_calificacion",
                999999,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            404,
        )


# =========================================================
# 4. MIS CALIFICACIONES
# 5 PRUEBAS
# =========================================================

class MisCalificacionesTests(DatosCalificaciones):

    # 39
    def test_paciente_solo_ve_sus_calificaciones(self):

        propia = self.crear_calificacion()

        self.crear_calificacion(
            cita=self.cita_bruno_finalizada,
        )

        self.client.force_login(self.ana)

        respuesta = self.client.get(
            self.ruta("mis_calificaciones")
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertEqual(
            list(respuesta.context["calificaciones"]),
            [propia],
        )

    # 40
    def test_mis_calificaciones_ordenadas_de_reciente_a_antigua(self):

        primera = self.crear_calificacion(
            cita=self.cita_ana_finalizada,
        )

        segunda = self.crear_calificacion(
            cita=self.cita_ana_otra,
        )

        self.client.force_login(self.ana)

        respuesta = self.client.get(
            self.ruta("mis_calificaciones")
        )

        self.assertEqual(
            list(respuesta.context["calificaciones"]),
            [segunda, primera],
        )

    # 41
    def test_mis_calificaciones_sin_sesion_redirige(self):

        respuesta = self.client.get(
            self.ruta("mis_calificaciones")
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:login"),
            fetch_redirect_response=False,
        )

    # 42
    def test_administrador_normal_no_accede_a_mis_calificaciones(self):

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.ruta("mis_calificaciones")
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:redireccion_por_rol"),
            fetch_redirect_response=False,
        )

    # 43
    def test_paciente_inactivo_no_consulta_sus_calificaciones(self):

        self.crear_calificacion()

        self.perfil_ana.activo = False

        self.perfil_ana.save(
            update_fields=["activo"]
        )

        self.client.force_login(self.ana)

        respuesta = self.client.get(
            self.ruta("mis_calificaciones")
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )


# =========================================================
# 5. LISTADO Y ESTADÍSTICAS DE ADMINISTRACIÓN
# 7 PRUEBAS
# =========================================================

class ListaCalificacionesTests(DatosCalificaciones):

    # 44
    def test_administrador_ve_todas_y_promedio(self):

        calificacion_1 = self.crear_calificacion(
            cita=self.cita_ana_finalizada,
            puntuacion=5,
        )

        calificacion_2 = self.crear_calificacion(
            cita=self.cita_ana_otra,
            puntuacion=3,
        )

        calificacion_3 = self.crear_calificacion(
            cita=self.cita_bruno_finalizada,
            puntuacion=4,
        )

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.ruta("lista_calificaciones")
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertEqual(
            respuesta.context["total_calificaciones"],
            3,
        )

        self.assertAlmostEqual(
            respuesta.context["promedio_calificaciones"],
            4.0,
        )

        self.assertEqual(
            set(respuesta.context["calificaciones"]),
            {
                calificacion_1,
                calificacion_2,
                calificacion_3,
            },
        )

    # 45
    def test_sin_calificaciones_promedio_es_none(self):

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.ruta("lista_calificaciones")
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertEqual(
            respuesta.context["total_calificaciones"],
            0,
        )

        self.assertIsNone(
            respuesta.context["promedio_calificaciones"]
        )

    # 46
    def test_superusuario_sin_perfil_ve_estadisticas(self):

        superusuario = (
            get_user_model().objects.create_superuser(
                username="super_estadisticas_tests",
                email="super_estadisticas@ejemplo.com",
                password="Prueba12345!",
            )
        )

        self.crear_calificacion()

        self.client.force_login(superusuario)

        respuesta = self.client.get(
            self.ruta("lista_calificaciones")
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertEqual(
            respuesta.context["total_calificaciones"],
            1,
        )

    # 47
    def test_lista_sin_sesion_redirige(self):

        respuesta = self.client.get(
            self.ruta("lista_calificaciones")
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:login"),
            fetch_redirect_response=False,
        )

    # 48
    def test_paciente_no_ve_lista_administrativa(self):

        self.client.force_login(self.ana)

        respuesta = self.client.get(
            self.ruta("lista_calificaciones")
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:redireccion_por_rol"),
            fetch_redirect_response=False,
        )

    # 49
    def test_recepcionista_no_ve_lista_administrativa(self):

        self.client.force_login(
            self.recepcionista
        )

        respuesta = self.client.get(
            self.ruta("lista_calificaciones")
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:redireccion_por_rol"),
            fetch_redirect_response=False,
        )

    # 50
    def test_administrador_inactivo_no_ve_estadisticas(self):

        self.perfil_admin.activo = False

        self.perfil_admin.save(
            update_fields=["activo"]
        )

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.ruta("lista_calificaciones")
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )
