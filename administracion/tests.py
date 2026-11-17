
from datetime import time, timedelta
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

from .models import RegistroActividad


# =========================================================
# DATOS COMPARTIDOS
# =========================================================

class DatosAdministracion(TestCase):

    @classmethod
    def setUpTestData(cls):

        Usuario = get_user_model()

        def crear_cuenta(nombre, rol):

            usuario = Usuario.objects.create_user(
                username=f"{nombre}_admin_tests",
                password="Prueba12345!",
                email=f"{nombre}_admin_tests@ejemplo.com",
                first_name=nombre.capitalize(),
                last_name="Prueba",
            )

            perfil = PerfilUsuario.objects.create(
                usuario=usuario,
                rol=rol,
                telefono="5512345678",
            )

            return usuario, perfil

        cls.admin, cls.perfil_admin = crear_cuenta(
            "administrador",
            PerfilUsuario.Rol.ADMINISTRADOR,
        )

        cls.otro_admin, cls.perfil_otro_admin = crear_cuenta(
            "otro_administrador",
            PerfilUsuario.Rol.ADMINISTRADOR,
        )

        cls.recepcionista, cls.perfil_recep = crear_cuenta(
            "recepcionista",
            PerfilUsuario.Rol.RECEPCIONISTA,
        )

        cls.usuario_fisio, cls.perfil_fisio = crear_cuenta(
            "fisioterapeuta",
            PerfilUsuario.Rol.FISIOTERAPEUTA,
        )

        cls.usuario_paciente, cls.perfil_paciente = crear_cuenta(
            "paciente",
            PerfilUsuario.Rol.PACIENTE,
        )

        cls.paciente = Paciente.objects.create(
            usuario=cls.perfil_paciente,
            antecedentes_medicos="Historial que debe conservarse.",
        )

        cls.fisio = Fisioterapeuta.objects.create(
            usuario=cls.perfil_fisio,
            especialidad="Fisioterapia deportiva",
        )

        cls.usuario_sin_perfil = Usuario.objects.create_user(
            username="sin_perfil_admin_tests",
            password="Prueba12345!",
            email="sin_perfil_admin_tests@ejemplo.com",
            first_name="Sin",
            last_name="Perfil",
        )

        cls.superusuario = Usuario.objects.create_superuser(
            username="super_admin_tests",
            email="super_admin_tests@ejemplo.com",
            password="Prueba12345!",
        )

        cls.servicio = Servicio.objects.create(
            nombre="Servicio administración pruebas",
            precio_base=Decimal("450.00"),
        )

        cls.motivo = MotivoConsulta.objects.create(
            nombre="Motivo administración pruebas"
        )

    def ruta(self, nombre, usuario=None):

        if usuario is None:
            return reverse(
                f"administracion:{nombre}"
            )

        return reverse(
            f"administracion:{nombre}",
            args=[
                usuario.pk
                if hasattr(usuario, "pk")
                else usuario
            ],
        )

    def datos_edicion(self, usuario, **cambios):

        perfil = getattr(
            usuario,
            "perfil",
            None,
        )

        datos = {
            "nombre": "NombreNuevo",
            "apellidos": "ApellidoNuevo",
            "email": "actualizado.administracion@ejemplo.com",
            "rol": (
                perfil.rol
                if perfil is not None
                else PerfilUsuario.Rol.PACIENTE
            ),
        }

        datos.update(cambios)

        return datos

    def crear_cita(self, **cambios):

        datos = {
            "paciente": self.paciente,
            "fisioterapeuta": self.fisio,
            "servicio": self.servicio,
            "motivo": self.motivo,
            "fecha": (
                timezone.localdate()
                + timedelta(days=7)
            ),
            "hora": time(10, 0),
            "estado": Cita.Estado.PROGRAMADA,
            "costo_estimado": Decimal("450.00"),
        }

        datos.update(cambios)

        return Cita.objects.create(**datos)


# =========================================================
# 1. MODELO, LISTADO Y PERMISOS
# 13 PRUEBAS
# =========================================================

class ModeloListadoAdministracionTests(DatosAdministracion):

    # 1
    def test_modelo_registro_actividad_str(self):

        actividad = RegistroActividad.objects.create(
            usuario=self.perfil_admin,
            accion="REVISAR_USUARIO",
            modulo="administracion",
        )

        self.assertIn(
            "REVISAR_USUARIO",
            str(actividad),
        )

    # 2
    def test_actividades_ordenadas_por_fecha_descendente(self):

        primera = RegistroActividad.objects.create(
            accion="PRIMERA_ACCION"
        )

        segunda = RegistroActividad.objects.create(
            accion="SEGUNDA_ACCION"
        )

        self.assertEqual(
            list(RegistroActividad.objects.all()),
            [segunda, primera],
        )

    # 3
    def test_actividad_permite_usuario_nulo(self):

        actividad = RegistroActividad.objects.create(
            usuario=None,
            accion="ACCION_SIN_PERFIL",
        )

        self.assertIsNone(
            actividad.usuario
        )

    # 4
    def test_administrador_consulta_lista_de_usuarios(self):

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.ruta("lista_usuarios")
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        usuarios = respuesta.context["usuarios"]

        self.assertIn(self.admin, usuarios)
        self.assertIn(self.recepcionista, usuarios)
        self.assertIn(self.usuario_paciente, usuarios)

    # 5
    def test_superusuario_sin_perfil_consulta_lista(self):

        self.client.force_login(self.superusuario)

        respuesta = self.client.get(
            self.ruta("lista_usuarios")
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

    # 6
    def test_lista_usuarios_ordenada_por_username(self):

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.ruta("lista_usuarios")
        )

        nombres = [
            usuario.username
            for usuario in respuesta.context["usuarios"]
        ]

        self.assertEqual(
            nombres,
            sorted(nombres),
        )

    # 7
    def test_recepcionista_no_accede_a_lista(self):

        self.client.force_login(self.recepcionista)

        respuesta = self.client.get(
            self.ruta("lista_usuarios")
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:redireccion_por_rol"),
            fetch_redirect_response=False,
        )

    # 8
    def test_fisioterapeuta_no_accede_a_lista(self):

        self.client.force_login(self.usuario_fisio)

        respuesta = self.client.get(
            self.ruta("lista_usuarios")
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:redireccion_por_rol"),
            fetch_redirect_response=False,
        )

    # 9
    def test_paciente_no_accede_a_lista(self):

        self.client.force_login(self.usuario_paciente)

        respuesta = self.client.get(
            self.ruta("lista_usuarios")
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:redireccion_por_rol"),
            fetch_redirect_response=False,
        )

    # 10
    def test_lista_sin_sesion_redirige(self):

        respuesta = self.client.get(
            self.ruta("lista_usuarios")
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:login"),
            fetch_redirect_response=False,
        )

    # 11
    def test_administrador_inactivo_no_consulta_lista(self):

        self.perfil_admin.activo = False

        self.perfil_admin.save(
            update_fields=["activo"]
        )

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.ruta("lista_usuarios")
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

    # 12
    def test_superusuario_con_perfil_inactivo_no_accede(self):

        PerfilUsuario.objects.create(
            usuario=self.superusuario,
            rol=PerfilUsuario.Rol.ADMINISTRADOR,
            activo=False,
        )

        self.client.force_login(self.superusuario)

        respuesta = self.client.get(
            self.ruta("lista_usuarios")
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

    # 13
    def test_usuario_sin_perfil_no_consulta_lista(self):

        self.client.force_login(
            self.usuario_sin_perfil
        )

        respuesta = self.client.get(
            self.ruta("lista_usuarios")
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:login"),
            fetch_redirect_response=False,
        )


# =========================================================
# 2. DETALLE DE USUARIOS
# 6 PRUEBAS
# =========================================================

class DetalleAdministracionTests(DatosAdministracion):

    # 14
    def test_administrador_ve_detalle_usuario(self):

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.ruta(
                "detalle_usuario",
                self.usuario_paciente,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertEqual(
            respuesta.context["usuario_seleccionado"],
            self.usuario_paciente,
        )

    # 15
    def test_superusuario_ve_detalle(self):

        self.client.force_login(self.superusuario)

        respuesta = self.client.get(
            self.ruta(
                "detalle_usuario",
                self.recepcionista,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

    # 16
    def test_detalle_de_usuario_sin_perfil(self):

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.ruta(
                "detalle_usuario",
                self.usuario_sin_perfil,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

    # 17
    def test_recepcionista_no_ve_detalle(self):

        self.client.force_login(self.recepcionista)

        respuesta = self.client.get(
            self.ruta(
                "detalle_usuario",
                self.usuario_paciente,
            )
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:redireccion_por_rol"),
            fetch_redirect_response=False,
        )

    # 18
    def test_detalle_usuario_inexistente_devuelve_404(self):

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.ruta(
                "detalle_usuario",
                999999,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            404,
        )

    # 19
    def test_detalle_sin_sesion_redirige(self):

        respuesta = self.client.get(
            self.ruta(
                "detalle_usuario",
                self.usuario_paciente,
            )
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:login"),
            fetch_redirect_response=False,
        )


# =========================================================
# 3. EDICIÓN Y CAMBIO DE ROLES
# 21 PRUEBAS
# =========================================================

class EdicionAdministracionTests(DatosAdministracion):

    # 20
    def test_administrador_abre_edicion(self):

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.ruta(
                "editar_usuario",
                self.recepcionista,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertEqual(
            respuesta.context["perfil"],
            self.perfil_recep,
        )

    # 21
    def test_get_edicion_sin_perfil_no_crea_registro(self):

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.ruta(
                "editar_usuario",
                self.usuario_sin_perfil,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertFalse(
            PerfilUsuario.objects.filter(
                usuario=self.usuario_sin_perfil
            ).exists()
        )

    # 22
    def test_edicion_actualiza_nombre_apellidos_email(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "editar_usuario",
                self.recepcionista,
            ),
            self.datos_edicion(self.recepcionista),
        )

        self.assertRedirects(
            respuesta,
            self.ruta(
                "detalle_usuario",
                self.recepcionista,
            ),
            fetch_redirect_response=False,
        )

        self.recepcionista.refresh_from_db()

        self.assertEqual(
            self.recepcionista.first_name,
            "NombreNuevo",
        )

        self.assertEqual(
            self.recepcionista.last_name,
            "ApellidoNuevo",
        )

        self.assertEqual(
            self.recepcionista.email,
            "actualizado.administracion@ejemplo.com",
        )

    # 23
    def test_administrador_cambia_rol_recepcion_a_admin(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "editar_usuario",
                self.recepcionista,
            ),
            self.datos_edicion(
                self.recepcionista,
                rol=PerfilUsuario.Rol.ADMINISTRADOR,
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.perfil_recep.refresh_from_db()

        self.assertEqual(
            self.perfil_recep.rol,
            PerfilUsuario.Rol.ADMINISTRADOR,
        )

    # 24
    def test_cambiar_rol_a_paciente_crea_paciente(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "editar_usuario",
                self.recepcionista,
            ),
            self.datos_edicion(
                self.recepcionista,
                rol=PerfilUsuario.Rol.PACIENTE,
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.perfil_recep.refresh_from_db()

        self.assertEqual(
            self.perfil_recep.rol,
            PerfilUsuario.Rol.PACIENTE,
        )

        self.assertTrue(
            Paciente.objects.filter(
                usuario=self.perfil_recep
            ).exists()
        )

    # 25
    def test_cambiar_rol_a_fisioterapeuta_crea_profesional(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "editar_usuario",
                self.recepcionista,
            ),
            self.datos_edicion(
                self.recepcionista,
                rol=PerfilUsuario.Rol.FISIOTERAPEUTA,
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.perfil_recep.refresh_from_db()

        self.assertEqual(
            self.perfil_recep.rol,
            PerfilUsuario.Rol.FISIOTERAPEUTA,
        )

        self.assertTrue(
            Fisioterapeuta.objects.filter(
                usuario=self.perfil_recep
            ).exists()
        )

    # 26
    def test_cambio_rol_conserva_historial_paciente(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "editar_usuario",
                self.usuario_paciente,
            ),
            self.datos_edicion(
                self.usuario_paciente,
                rol=PerfilUsuario.Rol.FISIOTERAPEUTA,
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.perfil_paciente.refresh_from_db()
        self.paciente.refresh_from_db()

        self.assertEqual(
            self.perfil_paciente.rol,
            PerfilUsuario.Rol.FISIOTERAPEUTA,
        )

        self.assertEqual(
            self.paciente.antecedentes_medicos,
            "Historial que debe conservarse.",
        )

        self.assertTrue(
            Fisioterapeuta.objects.filter(
                usuario=self.perfil_paciente
            ).exists()
        )

    # 27
    def test_edicion_crea_perfil_y_paciente_si_no_existen(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "editar_usuario",
                self.usuario_sin_perfil,
            ),
            self.datos_edicion(
                self.usuario_sin_perfil,
                rol=PerfilUsuario.Rol.PACIENTE,
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        perfil = PerfilUsuario.objects.get(
            usuario=self.usuario_sin_perfil
        )

        self.assertEqual(
            perfil.rol,
            PerfilUsuario.Rol.PACIENTE,
        )

        self.assertTrue(
            Paciente.objects.filter(
                usuario=perfil
            ).exists()
        )

    # 28
    def test_edicion_rechaza_rol_invalido(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "editar_usuario",
                self.recepcionista,
            ),
            self.datos_edicion(
                self.recepcionista,
                rol="SUPER_ADMIN_FALSO",
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.perfil_recep.refresh_from_db()
        self.recepcionista.refresh_from_db()

        self.assertEqual(
            self.perfil_recep.rol,
            PerfilUsuario.Rol.RECEPCIONISTA,
        )

        self.assertNotEqual(
            self.recepcionista.first_name,
            "NombreNuevo",
        )

    # 29
    def test_edicion_rechaza_rol_vacio(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "editar_usuario",
                self.recepcionista,
            ),
            self.datos_edicion(
                self.recepcionista,
                rol="",
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.perfil_recep.refresh_from_db()

        self.assertEqual(
            self.perfil_recep.rol,
            PerfilUsuario.Rol.RECEPCIONISTA,
        )

    # 30
    def test_edicion_rechaza_email_invalido(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "editar_usuario",
                self.recepcionista,
            ),
            self.datos_edicion(
                self.recepcionista,
                email="correo-invalido",
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.recepcionista.refresh_from_db()

        self.assertEqual(
            self.recepcionista.email,
            "recepcionista_admin_tests@ejemplo.com",
        )

    # 31
    def test_edicion_rechaza_email_duplicado(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "editar_usuario",
                self.recepcionista,
            ),
            self.datos_edicion(
                self.recepcionista,
                email=self.usuario_paciente.email.upper(),
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.recepcionista.refresh_from_db()

        self.assertEqual(
            self.recepcionista.email,
            "recepcionista_admin_tests@ejemplo.com",
        )

    # 32
    def test_edicion_rechaza_nombre_vacio(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "editar_usuario",
                self.recepcionista,
            ),
            self.datos_edicion(
                self.recepcionista,
                nombre="   ",
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.recepcionista.refresh_from_db()

        self.assertEqual(
            self.recepcionista.first_name,
            "Recepcionista",
        )

    # 33
    def test_edicion_rechaza_apellidos_vacios(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "editar_usuario",
                self.recepcionista,
            ),
            self.datos_edicion(
                self.recepcionista,
                apellidos="",
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

    # 34
    def test_edicion_rechaza_nombre_demasiado_largo(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "editar_usuario",
                self.recepcionista,
            ),
            self.datos_edicion(
                self.recepcionista,
                nombre="A" * 151,
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

    # 35
    def test_administrador_no_cambia_su_propio_rol(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "editar_usuario",
                self.admin,
            ),
            self.datos_edicion(
                self.admin,
                rol=PerfilUsuario.Rol.PACIENTE,
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.perfil_admin.refresh_from_db()

        self.assertEqual(
            self.perfil_admin.rol,
            PerfilUsuario.Rol.ADMINISTRADOR,
        )

    # 36
    def test_administrador_puede_editar_sus_datos(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "editar_usuario",
                self.admin,
            ),
            self.datos_edicion(self.admin),
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.admin.refresh_from_db()

        self.assertEqual(
            self.admin.first_name,
            "NombreNuevo",
        )

    # 37
    def test_administrador_normal_no_edita_superusuario(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "editar_usuario",
                self.superusuario,
            ),
            self.datos_edicion(
                self.superusuario,
                rol=PerfilUsuario.Rol.ADMINISTRADOR,
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

        self.assertFalse(
            PerfilUsuario.objects.filter(
                usuario=self.superusuario
            ).exists()
        )

    # 38
    def test_recepcionista_no_edita_usuarios(self):

        self.client.force_login(self.recepcionista)

        respuesta = self.client.post(
            self.ruta(
                "editar_usuario",
                self.usuario_paciente,
            ),
            self.datos_edicion(self.usuario_paciente),
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:redireccion_por_rol"),
            fetch_redirect_response=False,
        )

        self.usuario_paciente.refresh_from_db()

        self.assertEqual(
            self.usuario_paciente.first_name,
            "Paciente",
        )

    # 39
    def test_edicion_sin_sesion_redirige(self):

        respuesta = self.client.post(
            self.ruta(
                "editar_usuario",
                self.recepcionista,
            ),
            self.datos_edicion(self.recepcionista),
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:login"),
            fetch_redirect_response=False,
        )

    # 40
    def test_edicion_registra_actividad(self):

        self.client.force_login(self.admin)

        self.client.post(
            self.ruta(
                "editar_usuario",
                self.recepcionista,
            ),
            self.datos_edicion(self.recepcionista),
        )

        actividad = RegistroActividad.objects.get(
            accion="EDITAR_USUARIO"
        )

        self.assertEqual(
            actividad.usuario,
            self.perfil_admin,
        )

        self.assertEqual(
            actividad.modulo,
            "administracion",
        )

        self.assertIn(
            self.recepcionista.username,
            actividad.descripcion,
        )


# =========================================================
# 4. ACTIVACIÓN Y DESACTIVACIÓN
# 20 PRUEBAS
# =========================================================

class EstadoAdministracionTests(DatosAdministracion):

    # 41
    def test_cambiar_estado_requiere_post(self):

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.ruta(
                "cambiar_estado_usuario",
                self.recepcionista,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            405,
        )

    # 42
    def test_desactivar_recepcionista_sincroniza_estados(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "cambiar_estado_usuario",
                self.recepcionista,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.recepcionista.refresh_from_db()
        self.perfil_recep.refresh_from_db()

        self.assertFalse(
            self.recepcionista.is_active
        )

        self.assertFalse(
            self.perfil_recep.activo
        )

    # 43
    def test_reactivar_recepcionista_sincroniza_estados(self):

        self.recepcionista.is_active = False
        self.recepcionista.save(
            update_fields=["is_active"]
        )

        self.perfil_recep.activo = False
        self.perfil_recep.save(
            update_fields=["activo"]
        )

        self.client.force_login(self.admin)

        self.client.post(
            self.ruta(
                "cambiar_estado_usuario",
                self.recepcionista,
            )
        )

        self.recepcionista.refresh_from_db()
        self.perfil_recep.refresh_from_db()

        self.assertTrue(
            self.recepcionista.is_active
        )

        self.assertTrue(
            self.perfil_recep.activo
        )

    # 44
    def test_desactivar_paciente_sincroniza_tres_estados(self):

        self.client.force_login(self.admin)

        self.client.post(
            self.ruta(
                "cambiar_estado_usuario",
                self.usuario_paciente,
            )
        )

        self.usuario_paciente.refresh_from_db()
        self.perfil_paciente.refresh_from_db()
        self.paciente.refresh_from_db()

        self.assertFalse(
            self.usuario_paciente.is_active
        )

        self.assertFalse(
            self.perfil_paciente.activo
        )

        self.assertFalse(
            self.paciente.activo
        )

    # 45
    def test_reactivar_paciente_sincroniza_tres_estados(self):

        self.usuario_paciente.is_active = False
        self.usuario_paciente.save(
            update_fields=["is_active"]
        )

        self.perfil_paciente.activo = False
        self.perfil_paciente.save(
            update_fields=["activo"]
        )

        self.paciente.activo = False
        self.paciente.save(
            update_fields=["activo"]
        )

        self.client.force_login(self.admin)

        self.client.post(
            self.ruta(
                "cambiar_estado_usuario",
                self.usuario_paciente,
            )
        )

        self.usuario_paciente.refresh_from_db()
        self.perfil_paciente.refresh_from_db()
        self.paciente.refresh_from_db()

        self.assertTrue(
            self.usuario_paciente.is_active
        )

        self.assertTrue(
            self.perfil_paciente.activo
        )

        self.assertTrue(
            self.paciente.activo
        )

    # 46
    def test_desactivar_fisio_sincroniza_tres_estados(self):

        self.client.force_login(self.admin)

        self.client.post(
            self.ruta(
                "cambiar_estado_usuario",
                self.usuario_fisio,
            )
        )

        self.usuario_fisio.refresh_from_db()
        self.perfil_fisio.refresh_from_db()
        self.fisio.refresh_from_db()

        self.assertFalse(
            self.usuario_fisio.is_active
        )

        self.assertFalse(
            self.perfil_fisio.activo
        )

        self.assertFalse(
            self.fisio.activo
        )

    # 47
    def test_reactivar_fisio_sincroniza_tres_estados(self):

        self.usuario_fisio.is_active = False
        self.usuario_fisio.save(
            update_fields=["is_active"]
        )

        self.perfil_fisio.activo = False
        self.perfil_fisio.save(
            update_fields=["activo"]
        )

        self.fisio.activo = False
        self.fisio.save(
            update_fields=["activo"]
        )

        self.client.force_login(self.admin)

        self.client.post(
            self.ruta(
                "cambiar_estado_usuario",
                self.usuario_fisio,
            )
        )

        self.usuario_fisio.refresh_from_db()
        self.perfil_fisio.refresh_from_db()
        self.fisio.refresh_from_db()

        self.assertTrue(
            self.usuario_fisio.is_active
        )

        self.assertTrue(
            self.perfil_fisio.activo
        )

        self.assertTrue(
            self.fisio.activo
        )

    # 48
    def test_no_desactiva_paciente_con_cita_futura(self):

        self.crear_cita()

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "cambiar_estado_usuario",
                self.usuario_paciente,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.usuario_paciente.refresh_from_db()
        self.perfil_paciente.refresh_from_db()

        self.assertTrue(
            self.usuario_paciente.is_active
        )

        self.assertTrue(
            self.perfil_paciente.activo
        )

    # 49
    def test_no_desactiva_fisio_con_cita_confirmada_futura(self):

        self.crear_cita(
            estado=Cita.Estado.CONFIRMADA
        )

        self.client.force_login(self.admin)

        self.client.post(
            self.ruta(
                "cambiar_estado_usuario",
                self.usuario_fisio,
            )
        )

        self.usuario_fisio.refresh_from_db()
        self.fisio.refresh_from_db()

        self.assertTrue(
            self.usuario_fisio.is_active
        )

        self.assertTrue(
            self.fisio.activo
        )

    # 50
    def test_no_desactiva_fisio_con_cita_en_proceso_pasada(self):

        self.crear_cita(
            fecha=(
                timezone.localdate()
                - timedelta(days=5)
            ),
            estado=Cita.Estado.EN_PROCESO,
        )

        self.client.force_login(self.admin)

        self.client.post(
            self.ruta(
                "cambiar_estado_usuario",
                self.usuario_fisio,
            )
        )

        self.usuario_fisio.refresh_from_db()
        self.fisio.refresh_from_db()

        self.assertTrue(
            self.usuario_fisio.is_active
        )

        self.assertTrue(
            self.fisio.activo
        )

    # 51
    def test_administrador_no_puede_desactivarse(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "cambiar_estado_usuario",
                self.admin,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.admin.refresh_from_db()

        self.assertTrue(
            self.admin.is_active
        )

    # 52
    def test_no_se_cambia_estado_de_superusuario(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "cambiar_estado_usuario",
                self.superusuario,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.superusuario.refresh_from_db()

        self.assertTrue(
            self.superusuario.is_active
        )

    # 53
    def test_recepcionista_no_cambia_estado(self):

        self.client.force_login(self.recepcionista)

        respuesta = self.client.post(
            self.ruta(
                "cambiar_estado_usuario",
                self.usuario_paciente,
            )
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:redireccion_por_rol"),
            fetch_redirect_response=False,
        )

        self.usuario_paciente.refresh_from_db()

        self.assertTrue(
            self.usuario_paciente.is_active
        )

    # 54
    def test_cambiar_estado_sin_sesion_redirige(self):

        respuesta = self.client.post(
            self.ruta(
                "cambiar_estado_usuario",
                self.recepcionista,
            )
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:login"),
            fetch_redirect_response=False,
        )

    # 55
    def test_cambiar_estado_registra_actividad(self):

        self.client.force_login(self.admin)

        self.client.post(
            self.ruta(
                "cambiar_estado_usuario",
                self.recepcionista,
            )
        )

        actividad = RegistroActividad.objects.get(
            accion="DESACTIVAR_USUARIO"
        )

        self.assertEqual(
            actividad.usuario,
            self.perfil_admin,
        )

        self.assertEqual(
            actividad.modulo,
            "administracion",
        )

        self.assertIn(
            self.recepcionista.username,
            actividad.descripcion,
        )

    # 56
    def test_bloqueo_por_citas_no_registra_cambio(self):

        self.crear_cita()

        self.client.force_login(self.admin)

        self.client.post(
            self.ruta(
                "cambiar_estado_usuario",
                self.usuario_paciente,
            )
        )

        self.assertFalse(
            RegistroActividad.objects.filter(
                accion="DESACTIVAR_USUARIO"
            ).exists()
        )

    # 57
    def test_permite_desactivar_con_cita_programada_pasada(self):

        self.crear_cita(
            fecha=(
                timezone.localdate()
                - timedelta(days=30)
            ),
            estado=Cita.Estado.PROGRAMADA,
        )

        self.client.force_login(self.admin)

        self.client.post(
            self.ruta(
                "cambiar_estado_usuario",
                self.usuario_paciente,
            )
        )

        self.usuario_paciente.refresh_from_db()

        self.assertFalse(
            self.usuario_paciente.is_active
        )

    # 58
    def test_permite_desactivar_con_cita_cancelada_futura(self):

        self.crear_cita(
            estado=Cita.Estado.CANCELADA
        )

        self.client.force_login(self.admin)

        self.client.post(
            self.ruta(
                "cambiar_estado_usuario",
                self.usuario_fisio,
            )
        )

        self.usuario_fisio.refresh_from_db()

        self.assertFalse(
            self.usuario_fisio.is_active
        )

    # 59
    def test_cambiar_estado_usuario_sin_perfil(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "cambiar_estado_usuario",
                self.usuario_sin_perfil,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.usuario_sin_perfil.refresh_from_db()

        self.assertFalse(
            self.usuario_sin_perfil.is_active
        )

        self.assertFalse(
            PerfilUsuario.objects.filter(
                usuario=self.usuario_sin_perfil
            ).exists()
        )

    # 60
    def test_cambiar_estado_usuario_inexistente_devuelve_404(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.ruta(
                "cambiar_estado_usuario",
                999999,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            404,
        )
