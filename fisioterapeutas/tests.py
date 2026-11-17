
from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from citas.models import Cita, MotivoConsulta
from pacientes.models import Paciente
from precios.models import Servicio
from usuarios.models import PerfilUsuario

from .forms import (
    EditarFisioterapeutaForm,
    RegistrarFisioterapeutaForm,
)
from .horarios_forms import HorarioDisponibleForm
from .models import Fisioterapeuta, HorarioDisponible


# =========================================================
# DATOS COMPARTIDOS
# =========================================================

class DatosFisioterapeutas(TestCase):

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
            "admin_fisio_tests",
            PerfilUsuario.Rol.ADMINISTRADOR,
        )

        cls.recepcionista, cls.perfil_recep = crear_cuenta(
            "recep_fisio_tests",
            PerfilUsuario.Rol.RECEPCIONISTA,
        )

        cls.usuario_fisio, cls.perfil_fisio = crear_cuenta(
            "fisio_principal_tests",
            PerfilUsuario.Rol.FISIOTERAPEUTA,
        )

        cls.usuario_otro, cls.perfil_otro = crear_cuenta(
            "fisio_secundario_tests",
            PerfilUsuario.Rol.FISIOTERAPEUTA,
        )

        cls.usuario_paciente, cls.perfil_paciente = crear_cuenta(
            "paciente_fisio_tests",
            PerfilUsuario.Rol.PACIENTE,
        )

        cls.fisio = Fisioterapeuta.objects.create(
            usuario=cls.perfil_fisio,
            especialidad="Deportiva",
            cedula_profesional="CED-101",
            descripcion="Especialista en recuperación deportiva",
        )

        cls.otro_fisio = Fisioterapeuta.objects.create(
            usuario=cls.perfil_otro,
            especialidad="Neurológica",
            cedula_profesional="CED-102",
        )

        cls.paciente = Paciente.objects.create(
            usuario=cls.perfil_paciente
        )

        cls.servicio = Servicio.objects.create(
            nombre="Servicio prueba fisioterapeutas",
            precio_base=Decimal("400.00"),
        )

        cls.motivo = MotivoConsulta.objects.create(
            nombre="Motivo prueba fisioterapeutas"
        )

    def datos_profesional(self, **cambios):

        datos = {
            "nombre": "Laura",
            "apellidos": "Martinez",
            "email": "laura.nueva@ejemplo.com",
            "telefono": "5512345678",
            "especialidad": "Ortopédica",
            "cedula_profesional": "CED-NUEVA-500",
            "descripcion": "Experiencia clínica",
            "username": "laura_fisio_nueva",
            "password1": "ClaveSegura9876!",
            "password2": "ClaveSegura9876!",
        }

        datos.update(cambios)
        return datos

    def datos_horario(self, **cambios):

        datos = {
            "dia_semana": "1",
            "hora_inicio": "09:00",
            "hora_fin": "13:00",
            "activo": "on",
        }

        datos.update(cambios)
        return datos

    def crear_horario(self, **cambios):

        datos = {
            "fisioterapeuta": self.fisio,
            "dia_semana": 1,
            "hora_inicio": time(9, 0),
            "hora_fin": time(13, 0),
            "activo": True,
        }

        datos.update(cambios)

        return HorarioDisponible.objects.create(**datos)

    def lunes_futuro(self):

        hoy = timezone.localdate()

        return hoy + timedelta(
            days=(1 - hoy.isoweekday()) % 7 + 7
        )

    def crear_cita(self, **cambios):

        datos = {
            "paciente": self.paciente,
            "fisioterapeuta": self.fisio,
            "servicio": self.servicio,
            "motivo": self.motivo,
            "fecha": self.lunes_futuro(),
            "hora": time(10, 0),
            "estado": Cita.Estado.PROGRAMADA,
            "costo_estimado": Decimal("400.00"),
        }

        datos.update(cambios)

        return Cita.objects.create(**datos)

    def ruta(self, nombre, identificador=None):

        if identificador is None:
            return reverse(
                f"fisioterapeutas:{nombre}"
            )

        return reverse(
            f"fisioterapeutas:{nombre}",
            args=[identificador],
        )


# =========================================================
# 1. PRUEBAS DE FORMULARIOS
# =========================================================

class FormulariosFisioterapeutasTests(DatosFisioterapeutas):

    def test_registro_formulario_valido(self):

        form = RegistrarFisioterapeutaForm(
            data=self.datos_profesional()
        )

        self.assertTrue(
            form.is_valid(),
            form.errors,
        )

    def test_registro_rechaza_username_duplicado(self):

        form = RegistrarFisioterapeutaForm(
            data=self.datos_profesional(
                username=self.usuario_fisio.username.upper()
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_registro_rechaza_email_duplicado(self):

        form = RegistrarFisioterapeutaForm(
            data=self.datos_profesional(
                email=self.usuario_fisio.email.upper()
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_registro_rechaza_cedula_duplicada(self):

        form = RegistrarFisioterapeutaForm(
            data=self.datos_profesional(
                cedula_profesional="ced-101"
            )
        )

        self.assertFalse(form.is_valid())

        self.assertIn(
            "cedula_profesional",
            form.errors,
        )

    def test_registro_rechaza_contrasenas_diferentes(self):

        form = RegistrarFisioterapeutaForm(
            data=self.datos_profesional(
                password2="OtraClave9876!"
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_registro_rechaza_contrasena_debil(self):

        form = RegistrarFisioterapeutaForm(
            data=self.datos_profesional(
                password1="123",
                password2="123",
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn("password1", form.errors)

    def test_registro_rechaza_username_invalido(self):

        form = RegistrarFisioterapeutaForm(
            data=self.datos_profesional(
                username="usuario con espacios"
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_registro_rechaza_email_invalido(self):

        form = RegistrarFisioterapeutaForm(
            data=self.datos_profesional(
                email="correo-invalido"
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_edicion_conserva_email_y_cedula_propios(self):

        form = EditarFisioterapeutaForm(
            data=self.datos_profesional(
                email=self.usuario_fisio.email,
                cedula_profesional=(
                    self.fisio.cedula_profesional
                ),
            ),
            usuario_actual=self.usuario_fisio,
            fisioterapeuta_actual=self.fisio,
        )

        self.assertTrue(
            form.is_valid(),
            form.errors,
        )

    def test_edicion_rechaza_cedula_de_otro(self):

        form = EditarFisioterapeutaForm(
            data=self.datos_profesional(
                cedula_profesional=(
                    self.otro_fisio.cedula_profesional
                ),
            ),
            usuario_actual=self.usuario_fisio,
            fisioterapeuta_actual=self.fisio,
        )

        self.assertFalse(form.is_valid())

        self.assertIn(
            "cedula_profesional",
            form.errors,
        )

    def test_edicion_rechaza_email_de_otro(self):

        form = EditarFisioterapeutaForm(
            data=self.datos_profesional(
                email=self.usuario_otro.email
            ),
            usuario_actual=self.usuario_fisio,
            fisioterapeuta_actual=self.fisio,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


# =========================================================
# 2. LISTADOS, DETALLES Y PRIVACIDAD
# =========================================================

class ListadosFisioterapeutasTests(DatosFisioterapeutas):

    def test_admin_lista_todos(self):

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.ruta("lista_fisioterapeutas")
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            set(respuesta.context["fisioterapeutas"]),
            {self.fisio, self.otro_fisio},
        )

        self.assertTrue(
            respuesta.context["puede_gestionar"]
        )

    def test_recepcionista_lista_todos(self):

        self.client.force_login(self.recepcionista)

        respuesta = self.client.get(
            self.ruta("lista_fisioterapeutas")
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            len(respuesta.context["fisioterapeutas"]),
            2,
        )

    def test_paciente_solo_ve_profesionales_activos(self):

        self.otro_fisio.activo = False
        self.otro_fisio.save(update_fields=["activo"])

        self.client.force_login(self.usuario_paciente)

        respuesta = self.client.get(
            self.ruta("lista_fisioterapeutas")
        )

        self.assertEqual(
            list(respuesta.context["fisioterapeutas"]),
            [self.fisio],
        )

        self.assertFalse(
            respuesta.context["puede_gestionar"]
        )

    def test_fisioterapeuta_solo_ve_profesionales_activos(self):

        self.otro_fisio.activo = False
        self.otro_fisio.save(update_fields=["activo"])

        self.client.force_login(self.usuario_fisio)

        respuesta = self.client.get(
            self.ruta("lista_fisioterapeutas")
        )

        self.assertEqual(
            list(respuesta.context["fisioterapeutas"]),
            [self.fisio],
        )

    def test_busqueda_por_especialidad(self):

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.ruta("lista_fisioterapeutas"),
            {"buscar": "Deportiva"},
        )

        self.assertEqual(
            list(respuesta.context["fisioterapeutas"]),
            [self.fisio],
        )

    def test_busqueda_por_cedula(self):

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.ruta("lista_fisioterapeutas"),
            {"buscar": "CED-102"},
        )

        self.assertEqual(
            list(respuesta.context["fisioterapeutas"]),
            [self.otro_fisio],
        )

    def test_sin_sesion_redirige(self):

        respuesta = self.client.get(
            self.ruta("lista_fisioterapeutas")
        )

        self.assertEqual(respuesta.status_code, 302)

    def test_perfil_inactivo_no_accede(self):

        self.perfil_admin.activo = False
        self.perfil_admin.save(
            update_fields=["activo"]
        )

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.ruta("lista_fisioterapeutas")
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_superusuario_con_perfil_inactivo_no_accede(self):

        superusuario = (
            get_user_model().objects.create_superuser(
                username="super_bloqueado_fisio",
                email="super_fisio@ejemplo.com",
                password="Prueba12345!",
            )
        )

        PerfilUsuario.objects.create(
            usuario=superusuario,
            rol=PerfilUsuario.Rol.ADMINISTRADOR,
            activo=False,
        )

        self.client.force_login(superusuario)

        respuesta = self.client.get(
            self.ruta("lista_fisioterapeutas")
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_detalle_paciente_no_muestra_contacto(self):

        self.client.force_login(self.usuario_paciente)

        respuesta = self.client.get(
            self.ruta(
                "detalle_fisioterapeuta",
                self.fisio.pk,
            )
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertFalse(
            respuesta.context["ver_contacto"]
        )

        self.assertFalse(
            respuesta.context["puede_gestionar"]
        )

    def test_detalle_propio_de_fisio_muestra_contacto(self):

        self.client.force_login(self.usuario_fisio)

        respuesta = self.client.get(
            self.ruta(
                "detalle_fisioterapeuta",
                self.fisio.pk,
            )
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertTrue(
            respuesta.context["ver_contacto"]
        )

    def test_paciente_no_ve_detalle_inactivo(self):

        self.otro_fisio.activo = False
        self.otro_fisio.save(
            update_fields=["activo"]
        )

        self.client.force_login(self.usuario_paciente)

        respuesta = self.client.get(
            self.ruta(
                "detalle_fisioterapeuta",
                self.otro_fisio.pk,
            )
        )

        self.assertEqual(respuesta.status_code, 404)


# =========================================================
# 3. REGISTRO, EDICIÓN Y ESTADO
# =========================================================

class GestionFisioterapeutasTests(DatosFisioterapeutas):

    def test_admin_abre_registro(self):

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.ruta("registrar_fisioterapeuta")
        )

        self.assertEqual(respuesta.status_code, 200)

    def test_recepcionista_abre_registro(self):

        self.client.force_login(self.recepcionista)

        respuesta = self.client.get(
            self.ruta("registrar_fisioterapeuta")
        )

        self.assertEqual(respuesta.status_code, 200)

    def test_paciente_no_puede_registrar(self):

        self.client.force_login(self.usuario_paciente)

        respuesta = self.client.post(
            self.ruta("registrar_fisioterapeuta"),
            self.datos_profesional(),
        )

        self.assertEqual(respuesta.status_code, 403)

        self.assertFalse(
            get_user_model().objects.filter(
                username="laura_fisio_nueva"
            ).exists()
        )

    def test_admin_registra_usuario_perfil_y_profesional(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta("registrar_fisioterapeuta"),
            self.datos_profesional(),
        )

        self.assertEqual(respuesta.status_code, 302)

        nuevo = get_user_model().objects.get(
            username="laura_fisio_nueva"
        )

        self.assertTrue(
            nuevo.check_password("ClaveSegura9876!")
        )

        self.assertEqual(
            nuevo.perfil.rol,
            PerfilUsuario.Rol.FISIOTERAPEUTA,
        )

        self.assertEqual(
            nuevo.perfil.fisioterapeuta.especialidad,
            "Ortopédica",
        )

        self.assertEqual(
            nuevo.perfil.fisioterapeuta.cedula_profesional,
            "CED-NUEVA-500",
        )

    def test_registro_invalido_no_crea_cuenta(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta("registrar_fisioterapeuta"),
            self.datos_profesional(
                password2="NoCoincide123!"
            ),
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertIn(
            "password2",
            respuesta.context["form"].errors,
        )

        self.assertFalse(
            get_user_model().objects.filter(
                username="laura_fisio_nueva"
            ).exists()
        )

    def test_admin_edita_profesional(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "editar_fisioterapeuta",
                self.fisio.pk,
            ),
            self.datos_profesional(),
        )

        self.assertEqual(respuesta.status_code, 302)

        self.fisio.refresh_from_db()
        self.usuario_fisio.refresh_from_db()
        self.perfil_fisio.refresh_from_db()

        self.assertEqual(
            self.fisio.especialidad,
            "Ortopédica",
        )

        self.assertEqual(
            self.fisio.cedula_profesional,
            "CED-NUEVA-500",
        )

        self.assertEqual(
            self.usuario_fisio.email,
            "laura.nueva@ejemplo.com",
        )

        self.assertEqual(
            self.perfil_fisio.telefono,
            "5512345678",
        )

    def test_recepcionista_edita_profesional(self):

        self.client.force_login(self.recepcionista)

        respuesta = self.client.post(
            self.ruta(
                "editar_fisioterapeuta",
                self.fisio.pk,
            ),
            self.datos_profesional(),
        )

        self.assertEqual(respuesta.status_code, 302)

        self.fisio.refresh_from_db()

        self.assertEqual(
            self.fisio.especialidad,
            "Ortopédica",
        )

    def test_paciente_no_edita_profesional(self):

        self.client.force_login(self.usuario_paciente)

        respuesta = self.client.get(
            self.ruta(
                "editar_fisioterapeuta",
                self.fisio.pk,
            )
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_cambio_estado_requiere_post(self):

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.ruta(
                "cambiar_estado_fisioterapeuta",
                self.fisio.pk,
            )
        )

        self.assertEqual(respuesta.status_code, 405)

    def test_recepcionista_no_cambia_estado(self):

        self.client.force_login(self.recepcionista)

        respuesta = self.client.post(
            self.ruta(
                "cambiar_estado_fisioterapeuta",
                self.fisio.pk,
            )
        )

        self.assertEqual(respuesta.status_code, 403)

        self.fisio.refresh_from_db()
        self.assertTrue(self.fisio.activo)

    def test_admin_no_desactiva_con_cita_futura(self):

        self.crear_cita()

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "cambiar_estado_fisioterapeuta",
                self.fisio.pk,
            )
        )

        self.assertEqual(respuesta.status_code, 302)

        self.fisio.refresh_from_db()
        self.assertTrue(self.fisio.activo)

    def test_admin_no_desactiva_con_consulta_en_proceso(self):

        self.crear_cita(
            fecha=(
                timezone.localdate()
                - timedelta(days=3)
            ),
            estado=Cita.Estado.EN_PROCESO,
        )

        self.client.force_login(self.admin)

        self.client.post(
            self.ruta(
                "cambiar_estado_fisioterapeuta",
                self.fisio.pk,
            )
        )

        self.fisio.refresh_from_db()
        self.assertTrue(self.fisio.activo)

    def test_admin_desactiva_sin_eliminar_registros(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "cambiar_estado_fisioterapeuta",
                self.fisio.pk,
            )
        )

        self.assertEqual(respuesta.status_code, 302)

        self.fisio.refresh_from_db()
        self.perfil_fisio.refresh_from_db()
        self.usuario_fisio.refresh_from_db()

        self.assertFalse(self.fisio.activo)
        self.assertFalse(self.perfil_fisio.activo)
        self.assertFalse(self.usuario_fisio.is_active)

        self.assertTrue(
            Fisioterapeuta.objects.filter(
                pk=self.fisio.pk
            ).exists()
        )

    def test_admin_reactiva_fisioterapeuta(self):

        self.fisio.activo = False
        self.fisio.save(update_fields=["activo"])

        self.perfil_fisio.activo = False
        self.perfil_fisio.save(
            update_fields=["activo"]
        )

        self.usuario_fisio.is_active = False
        self.usuario_fisio.save(
            update_fields=["is_active"]
        )

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "cambiar_estado_fisioterapeuta",
                self.fisio.pk,
            )
        )

        self.assertEqual(respuesta.status_code, 302)

        self.fisio.refresh_from_db()
        self.perfil_fisio.refresh_from_db()
        self.usuario_fisio.refresh_from_db()

        self.assertTrue(self.fisio.activo)
        self.assertTrue(self.perfil_fisio.activo)
        self.assertTrue(self.usuario_fisio.is_active)


# =========================================================
# 4. HORARIOS Y VALIDACIONES
# =========================================================

class HorariosFisioterapeutasTests(DatosFisioterapeutas):

    def test_form_horario_valido(self):

        form = HorarioDisponibleForm(
            data=self.datos_horario(),
            fisioterapeuta=self.fisio,
        )

        self.assertTrue(
            form.is_valid(),
            form.errors,
        )

    def test_form_rechaza_fin_antes_del_inicio(self):

        form = HorarioDisponibleForm(
            data=self.datos_horario(
                hora_fin="08:00"
            ),
            fisioterapeuta=self.fisio,
        )

        self.assertFalse(form.is_valid())

    def test_form_rechaza_duracion_menor_a_una_hora(self):

        form = HorarioDisponibleForm(
            data=self.datos_horario(
                hora_fin="09:30"
            ),
            fisioterapeuta=self.fisio,
        )

        self.assertFalse(form.is_valid())

    def test_form_rechaza_duracion_fraccionaria(self):

        form = HorarioDisponibleForm(
            data=self.datos_horario(
                hora_fin="10:30"
            ),
            fisioterapeuta=self.fisio,
        )

        self.assertFalse(form.is_valid())

    def test_form_rechaza_traslape(self):

        self.crear_horario()

        form = HorarioDisponibleForm(
            data=self.datos_horario(
                hora_inicio="11:00",
                hora_fin="15:00",
            ),
            fisioterapeuta=self.fisio,
        )

        self.assertFalse(form.is_valid())

    def test_form_acepta_jornadas_contiguas(self):

        self.crear_horario()

        form = HorarioDisponibleForm(
            data=self.datos_horario(
                hora_inicio="13:00",
                hora_fin="15:00",
            ),
            fisioterapeuta=self.fisio,
        )

        self.assertTrue(
            form.is_valid(),
            form.errors,
        )

    def test_form_no_activa_horarios_de_fisio_inactivo(self):

        self.fisio.activo = False
        self.fisio.save(update_fields=["activo"])

        form = HorarioDisponibleForm(
            data=self.datos_horario(),
            fisioterapeuta=self.fisio,
        )

        self.assertFalse(form.is_valid())

    def test_form_permite_guardar_horario_inactivo(self):

        self.fisio.activo = False
        self.fisio.save(update_fields=["activo"])

        form = HorarioDisponibleForm(
            data=self.datos_horario(
                activo=""
            ),
            fisioterapeuta=self.fisio,
        )

        self.assertTrue(
            form.is_valid(),
            form.errors,
        )

    def test_admin_ve_horarios_activos_e_inactivos(self):

        activo = self.crear_horario()

        inactivo = self.crear_horario(
            dia_semana=2,
            activo=False,
        )

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.ruta(
                "horario_fisioterapeuta",
                self.fisio.pk,
            )
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            set(respuesta.context["horarios"]),
            {activo, inactivo},
        )

    def test_paciente_solo_ve_horarios_activos(self):

        activo = self.crear_horario()

        self.crear_horario(
            dia_semana=2,
            activo=False,
        )

        self.client.force_login(self.usuario_paciente)

        respuesta = self.client.get(
            self.ruta(
                "horario_fisioterapeuta",
                self.fisio.pk,
            )
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            list(respuesta.context["horarios"]),
            [activo],
        )

    def test_admin_registra_horario(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "registrar_horario",
                self.fisio.pk,
            ),
            self.datos_horario(),
        )

        self.assertEqual(respuesta.status_code, 302)

        self.assertTrue(
            HorarioDisponible.objects.filter(
                fisioterapeuta=self.fisio,
                dia_semana=1,
                hora_inicio=time(9, 0),
                hora_fin=time(13, 0),
                activo=True,
            ).exists()
        )

    def test_fisio_no_registra_horario(self):

        self.client.force_login(self.usuario_fisio)

        respuesta = self.client.post(
            self.ruta(
                "registrar_horario",
                self.fisio.pk,
            ),
            self.datos_horario(),
        )

        self.assertEqual(respuesta.status_code, 403)

        self.assertEqual(
            HorarioDisponible.objects.count(),
            0,
        )

    def test_admin_edita_horario(self):

        horario = self.crear_horario()

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "editar_horario",
                horario.pk,
            ),
            self.datos_horario(
                hora_inicio="08:00",
                hora_fin="12:00",
            ),
        )

        self.assertEqual(respuesta.status_code, 302)

        horario.refresh_from_db()

        self.assertEqual(
            horario.hora_inicio,
            time(8, 0),
        )

    def test_edicion_rechaza_traslape(self):

        horario = self.crear_horario()

        self.crear_horario(
            hora_inicio=time(15, 0),
            hora_fin=time(18, 0),
        )

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "editar_horario",
                horario.pk,
            ),
            self.datos_horario(
                hora_inicio="14:00",
                hora_fin="17:00",
            ),
        )

        self.assertEqual(respuesta.status_code, 200)

        horario.refresh_from_db()

        self.assertEqual(
            horario.hora_inicio,
            time(9, 0),
        )

    def test_no_edita_horario_que_deja_cita_sin_cobertura(self):

        horario = self.crear_horario()

        self.crear_cita()

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "editar_horario",
                horario.pk,
            ),
            self.datos_horario(
                hora_inicio="12:00",
                hora_fin="16:00",
            ),
        )

        self.assertEqual(respuesta.status_code, 200)

        horario.refresh_from_db()

        self.assertEqual(
            horario.hora_inicio,
            time(9, 0),
        )

    def test_cambiar_estado_horario_requiere_post(self):

        horario = self.crear_horario()

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.ruta(
                "cambiar_estado_horario",
                horario.pk,
            )
        )

        self.assertEqual(respuesta.status_code, 405)

    def test_no_desactiva_horario_con_cita_futura(self):

        horario = self.crear_horario()

        self.crear_cita()

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "cambiar_estado_horario",
                horario.pk,
            )
        )

        self.assertEqual(respuesta.status_code, 302)

        horario.refresh_from_db()

        self.assertTrue(horario.activo)

    def test_desactiva_horario_sin_citas_pendientes(self):

        horario = self.crear_horario()

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "cambiar_estado_horario",
                horario.pk,
            )
        )

        self.assertEqual(respuesta.status_code, 302)

        horario.refresh_from_db()

        self.assertFalse(horario.activo)

    def test_no_activa_horario_traslapado(self):

        self.crear_horario()

        inactivo = self.crear_horario(
            hora_inicio=time(11, 0),
            hora_fin=time(15, 0),
            activo=False,
        )

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "cambiar_estado_horario",
                inactivo.pk,
            )
        )

        self.assertEqual(respuesta.status_code, 302)

        inactivo.refresh_from_db()

        self.assertFalse(inactivo.activo)

    def test_no_activa_horario_de_fisio_inactivo(self):

        inactivo = self.crear_horario(
            activo=False
        )

        self.fisio.activo = False

        self.fisio.save(
            update_fields=["activo"]
        )

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "cambiar_estado_horario",
                inactivo.pk,
            )
        )

        self.assertEqual(respuesta.status_code, 302)

        inactivo.refresh_from_db()

        self.assertFalse(inactivo.activo)
