
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

from .models import PerfilUsuario
from .views import obtener_citas_futuras


# =========================================================
# DATOS COMPARTIDOS PARA LAS PRUEBAS
# =========================================================

class DatosUsuarios(TestCase):

    @classmethod
    def setUpTestData(cls):

        Usuario = get_user_model()
        cls.cuentas = {}

        for nombre, rol in (
            ("admin", PerfilUsuario.Rol.ADMINISTRADOR),
            ("recepcion", PerfilUsuario.Rol.RECEPCIONISTA),
            ("fisio", PerfilUsuario.Rol.FISIOTERAPEUTA),
            ("paciente", PerfilUsuario.Rol.PACIENTE),
        ):
            usuario = Usuario.objects.create_user(
                username=f"{nombre}_usuarios_tests",
                password="Prueba12345!",
                email=f"{nombre}@ejemplo.com",
            )

            perfil = PerfilUsuario.objects.create(
                usuario=usuario,
                rol=rol,
            )

            cls.cuentas[nombre] = (usuario, perfil)

        cls.admin, cls.perfil_admin = cls.cuentas["admin"]

        cls.recepcionista, cls.perfil_recepcionista = (
            cls.cuentas["recepcion"]
        )

        cls.usuario_fisio, cls.perfil_fisio = (
            cls.cuentas["fisio"]
        )

        cls.usuario_paciente, cls.perfil_paciente = (
            cls.cuentas["paciente"]
        )

        cls.fisio = Fisioterapeuta.objects.create(
            usuario=cls.perfil_fisio
        )

        cls.paciente = Paciente.objects.create(
            usuario=cls.perfil_paciente
        )

        cls.servicio = Servicio.objects.create(
            nombre="Servicio usuarios tests",
            precio_base=Decimal("400.00"),
        )

        cls.motivo = MotivoConsulta.objects.create(
            nombre="Consulta usuarios tests"
        )

    def datos_registro(self, **cambios):

        datos = {
            "nombre": "Andrea",
            "apellidos": "García",
            "fecha_nacimiento": "2000-05-10",
            "telefono": "5551234567",
            "correo": "nueva@ejemplo.com",
            "usuario": "paciente_nuevo_tests",
            "password": "ClaveSegura9081!",
            "password2": "ClaveSegura9081!",
        }

        datos.update(cambios)
        return datos

    def crear_cita(self, **cambios):

        datos = {
            "paciente": self.paciente,
            "fisioterapeuta": self.fisio,
            "servicio": self.servicio,
            "motivo": self.motivo,
            "fecha": timezone.localdate() + timedelta(days=7),
            "hora": time(10, 0),
            "estado": Cita.Estado.PROGRAMADA,
            "costo_estimado": Decimal("400.00"),
        }

        datos.update(cambios)
        return Cita.objects.create(**datos)


# =========================================================
# PRUEBAS DE AUTENTICACIÓN Y REGISTRO
# =========================================================

class AutenticacionRegistroTests(DatosUsuarios):

    # 1. MOSTRAR FORMULARIO DE LOGIN
    def test_login_get_muestra_formulario(self):

        respuesta = self.client.get(
            reverse("usuarios:login")
        )

        self.assertEqual(respuesta.status_code, 200)

    # 2. INICIO DE SESIÓN CORRECTO
    def test_login_correcto_redirige(self):

        respuesta = self.client.post(
            reverse("usuarios:login"),
            {
                "username": self.usuario_paciente.username,
                "password": "Prueba12345!",
            },
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:redireccion_por_rol"),
            fetch_redirect_response=False,
        )

        self.assertEqual(
            self.client.session.get("_auth_user_id"),
            str(self.usuario_paciente.pk),
        )

    # 3. CONTRASEÑA INCORRECTA
    def test_login_contrasena_incorrecta_no_autentica(self):

        respuesta = self.client.post(
            reverse("usuarios:login"),
            {
                "username": self.usuario_paciente.username,
                "password": "Incorrecta123!",
            },
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

    # 4. PERFIL INACTIVO NO PUEDE INICIAR SESIÓN
    def test_login_perfil_inactivo_bloqueado(self):

        self.perfil_paciente.activo = False

        self.perfil_paciente.save(
            update_fields=["activo"]
        )

        respuesta = self.client.post(
            reverse("usuarios:login"),
            {
                "username": self.usuario_paciente.username,
                "password": "Prueba12345!",
            },
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

    # 5. USUARIO DJANGO INACTIVO
    def test_login_usuario_django_inactivo_bloqueado(self):

        self.usuario_paciente.is_active = False

        self.usuario_paciente.save(
            update_fields=["is_active"]
        )

        respuesta = self.client.post(
            reverse("usuarios:login"),
            {
                "username": self.usuario_paciente.username,
                "password": "Prueba12345!",
            },
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

    # 6. USUARIO NORMAL SIN PERFIL
    def test_login_usuario_normal_sin_perfil_bloqueado(self):

        usuario = get_user_model().objects.create_user(
            username="sin_perfil_login",
            password="Prueba12345!",
        )

        respuesta = self.client.post(
            reverse("usuarios:login"),
            {
                "username": usuario.username,
                "password": "Prueba12345!",
            },
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

    # 7. SUPERUSUARIO SIN PERFIL
    def test_login_superusuario_sin_perfil_permitido(self):

        superusuario = get_user_model().objects.create_superuser(
            username="super_sin_perfil",
            email="super@ejemplo.com",
            password="Prueba12345!",
        )

        respuesta = self.client.post(
            reverse("usuarios:login"),
            {
                "username": superusuario.username,
                "password": "Prueba12345!",
            },
        )

        self.assertEqual(respuesta.status_code, 302)

        self.assertEqual(
            self.client.session.get("_auth_user_id"),
            str(superusuario.pk),
        )

    # 8. SUPERUSUARIO CON PERFIL INACTIVO
    def test_login_superusuario_con_perfil_inactivo_bloqueado(self):

        superusuario = get_user_model().objects.create_superuser(
            username="super_bloqueado",
            email="super2@ejemplo.com",
            password="Prueba12345!",
        )

        PerfilUsuario.objects.create(
            usuario=superusuario,
            rol=PerfilUsuario.Rol.ADMINISTRADOR,
            activo=False,
        )

        respuesta = self.client.post(
            reverse("usuarios:login"),
            {
                "username": superusuario.username,
                "password": "Prueba12345!",
            },
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

    # 9. USUARIO AUTENTICADO NO REGRESA AL LOGIN
    def test_login_usuario_ya_autenticado_redirige(self):

        self.client.force_login(
            self.usuario_paciente
        )

        respuesta = self.client.get(
            reverse("usuarios:login")
        )

        self.assertEqual(respuesta.status_code, 302)

        self.assertEqual(
            respuesta.url,
            reverse("usuarios:redireccion_por_rol"),
        )

    # 10. CERRAR SESIÓN
    def test_logout_cierra_sesion(self):

        self.client.force_login(
            self.usuario_paciente
        )

        respuesta = self.client.get(
            reverse("usuarios:logout")
        )

        self.assertEqual(respuesta.status_code, 302)

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

    # 11. FORMULARIO DE REGISTRO
    def test_registro_get_muestra_formulario(self):

        respuesta = self.client.get(
            reverse("usuarios:registro")
        )

        self.assertEqual(respuesta.status_code, 200)

    # 12. REGISTRO COMPLETO
    def test_registro_crea_usuario_perfil_y_paciente(self):

        respuesta = self.client.post(
            reverse("usuarios:registro"),
            self.datos_registro(),
        )

        self.assertEqual(respuesta.status_code, 302)

        Usuario = get_user_model()

        nuevo = Usuario.objects.get(
            username="paciente_nuevo_tests"
        )

        self.assertTrue(
            nuevo.check_password("ClaveSegura9081!")
        )

        self.assertEqual(
            nuevo.perfil.rol,
            PerfilUsuario.Rol.PACIENTE,
        )

        self.assertEqual(
            nuevo.perfil.telefono,
            "5551234567",
        )

        self.assertTrue(
            Paciente.objects.filter(
                usuario=nuevo.perfil
            ).exists()
        )

    # 13. DATOS OBLIGATORIOS VACÍOS
    def test_registro_rechaza_datos_obligatorios_vacios(self):

        respuesta = self.client.post(
            reverse("usuarios:registro"),
            self.datos_registro(nombre=""),
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertFalse(
            get_user_model().objects.filter(
                username="paciente_nuevo_tests"
            ).exists()
        )

    # 14. CONTRASEÑAS DIFERENTES
    def test_registro_rechaza_contrasenas_diferentes(self):

        respuesta = self.client.post(
            reverse("usuarios:registro"),
            self.datos_registro(
                password2="OtraClave9081!"
            ),
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertFalse(
            get_user_model().objects.filter(
                username="paciente_nuevo_tests"
            ).exists()
        )

    # 15. USUARIO DUPLICADO
    def test_registro_rechaza_usuario_duplicado(self):

        respuesta = self.client.post(
            reverse("usuarios:registro"),
            self.datos_registro(
                usuario=self.usuario_paciente.username
            ),
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertFalse(
            get_user_model().objects.filter(
                email="nueva@ejemplo.com"
            ).exists()
        )

    # 16. CORREO DUPLICADO
    def test_registro_rechaza_correo_duplicado_ignorando_mayusculas(self):

        respuesta = self.client.post(
            reverse("usuarios:registro"),
            self.datos_registro(
                correo="PACIENTE@EJEMPLO.COM"
            ),
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertFalse(
            get_user_model().objects.filter(
                username="paciente_nuevo_tests"
            ).exists()
        )

    # 17. CONTRASEÑA DÉBIL
    def test_registro_rechaza_contrasena_debil(self):

        respuesta = self.client.post(
            reverse("usuarios:registro"),
            self.datos_registro(
                password="123",
                password2="123",
            ),
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertFalse(
            get_user_model().objects.filter(
                username="paciente_nuevo_tests"
            ).exists()
        )

    # 18. CORREO INVÁLIDO
    def test_registro_rechaza_correo_invalido(self):

        respuesta = self.client.post(
            reverse("usuarios:registro"),
            self.datos_registro(
                correo="no-es-un-correo"
            ),
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertFalse(
            get_user_model().objects.filter(
                username="paciente_nuevo_tests"
            ).exists()
        )

    # 19. FECHA DE NACIMIENTO INVÁLIDA
    def test_registro_rechaza_fecha_nacimiento_invalida(self):

        respuesta = self.client.post(
            reverse("usuarios:registro"),
            self.datos_registro(
                fecha_nacimiento="fecha-invalida"
            ),
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertFalse(
            get_user_model().objects.filter(
                username="paciente_nuevo_tests"
            ).exists()
        )

    # 20. FECHA DE NACIMIENTO FUTURA
    def test_registro_rechaza_fecha_futura(self):

        manana = (
            timezone.localdate()
            + timedelta(days=1)
        ).isoformat()

        respuesta = self.client.post(
            reverse("usuarios:registro"),
            self.datos_registro(
                fecha_nacimiento=manana
            ),
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertFalse(
            get_user_model().objects.filter(
                username="paciente_nuevo_tests"
            ).exists()
        )

    # 21. USUARIO AUTENTICADO NO SE REGISTRA OTRA VEZ
    def test_registro_autenticado_redirige(self):

        self.client.force_login(
            self.usuario_paciente
        )

        respuesta = self.client.get(
            reverse("usuarios:registro")
        )

        self.assertEqual(respuesta.status_code, 302)

        self.assertEqual(
            respuesta.url,
            reverse("usuarios:redireccion_por_rol"),
        )


# =========================================================
# PRUEBAS DE PERMISOS Y SEGURIDAD
# =========================================================

class PermisosUsuariosTests(DatosUsuarios):

    # 22. REDIRECCIÓN DE LOS CUATRO ROLES
    def test_redireccion_por_rol_de_los_cuatro_roles(self):

        destinos = {
            "admin": "dashboard_administrador",
            "recepcion": "dashboard_recepcionista",
            "fisio": "dashboard_fisioterapeuta",
            "paciente": "dashboard_paciente",
        }

        for nombre, destino in destinos.items():

            with self.subTest(rol=nombre):

                self.client.force_login(
                    self.cuentas[nombre][0]
                )

                respuesta = self.client.get(
                    reverse(
                        "usuarios:redireccion_por_rol"
                    )
                )

                self.assertEqual(
                    respuesta.status_code,
                    302,
                )

                self.assertEqual(
                    respuesta.url,
                    reverse(f"usuarios:{destino}"),
                )

    # 23. SUPERUSUARIO SIN PERFIL VA A ADMINISTRADOR
    def test_superusuario_sin_perfil_va_a_dashboard_admin(self):

        superusuario = get_user_model().objects.create_superuser(
            username="super_dashboard",
            email="super3@ejemplo.com",
            password="Prueba12345!",
        )

        self.client.force_login(superusuario)

        respuesta = self.client.get(
            reverse("usuarios:redireccion_por_rol")
        )

        self.assertEqual(
            respuesta.url,
            reverse("usuarios:dashboard_administrador"),
        )

    # 24. REDIRECCIÓN SIN PERFIL CIERRA SESIÓN
    def test_redireccion_sin_perfil_cierra_sesion(self):

        usuario = get_user_model().objects.create_user(
            username="sin_perfil_redireccion",
            password="Prueba12345!",
        )

        self.client.force_login(usuario)

        respuesta = self.client.get(
            reverse("usuarios:redireccion_por_rol")
        )

        self.assertEqual(
            respuesta.url,
            reverse("usuarios:login"),
        )

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

    # 25. PERFIL INACTIVO CIERRA SESIÓN
    def test_redireccion_perfil_inactivo_cierra_sesion(self):

        self.perfil_paciente.activo = False

        self.perfil_paciente.save(
            update_fields=["activo"]
        )

        self.client.force_login(
            self.usuario_paciente
        )

        respuesta = self.client.get(
            reverse("usuarios:redireccion_por_rol")
        )

        self.assertEqual(
            respuesta.url,
            reverse("usuarios:login"),
        )

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

    # 26. PERFIL INACTIVO NO ACCEDE A PÁGINAS PERSONALES
    def test_perfil_inactivo_no_ve_paginas_personales(self):

        self.perfil_paciente.activo = False

        self.perfil_paciente.save(
            update_fields=["activo"]
        )

        self.client.force_login(
            self.usuario_paciente
        )

        for ruta in (
            "perfil",
            "editar_perfil",
            "cambiar_contrasena",
        ):

            with self.subTest(ruta=ruta):

                respuesta = self.client.get(
                    reverse(f"usuarios:{ruta}")
                )

                self.assertEqual(
                    respuesta.status_code,
                    403,
                )

    # 27. USUARIO SIN PERFIL NO ACCEDE A PÁGINAS PERSONALES
    def test_usuario_sin_perfil_no_ve_paginas_personales(self):

        usuario = get_user_model().objects.create_user(
            username="sin_perfil_personal",
            password="Prueba12345!",
        )

        self.client.force_login(usuario)

        for ruta in (
            "perfil",
            "editar_perfil",
            "cambiar_contrasena",
        ):

            with self.subTest(ruta=ruta):

                respuesta = self.client.get(
                    reverse(f"usuarios:{ruta}")
                )

                self.assertEqual(
                    respuesta.status_code,
                    403,
                )

    # 28. PÁGINAS PERSONALES REQUIEREN SESIÓN
    def test_paginas_personales_requieren_sesion(self):

        for ruta in (
            "perfil",
            "editar_perfil",
            "cambiar_contrasena",
        ):

            with self.subTest(ruta=ruta):

                respuesta = self.client.get(
                    reverse(f"usuarios:{ruta}")
                )

                self.assertEqual(
                    respuesta.status_code,
                    302,
                )

    # 29. PACIENTE NO PUEDE ENTRAR AL DASHBOARD ADMIN
    # CORREGIDO: EL DECORADOR DEVUELVE 302
    def test_paciente_no_ve_dashboard_administrador(self):

        self.client.force_login(
            self.usuario_paciente
        )

        respuesta = self.client.get(
            reverse("usuarios:dashboard_administrador")
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:redireccion_por_rol"),
            fetch_redirect_response=False,
        )

    # 30. FISIO NO PUEDE ENTRAR AL DASHBOARD RECEPCIÓN
    # CORREGIDO: EL DECORADOR DEVUELVE 302
    def test_fisio_no_ve_dashboard_recepcionista(self):

        self.client.force_login(
            self.usuario_fisio
        )

        respuesta = self.client.get(
            reverse("usuarios:dashboard_recepcionista")
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:redireccion_por_rol"),
            fetch_redirect_response=False,
        )


# =========================================================
# PRUEBAS DE PERFIL Y CONTRASEÑA
# =========================================================

class PerfilUsuariosTests(DatosUsuarios):

    def setUp(self):

        self.client.force_login(
            self.usuario_paciente
        )

    # 31. CONSULTAR PERFIL
    def test_perfil_get_correcto(self):

        respuesta = self.client.get(
            reverse("usuarios:perfil")
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            respuesta.context["perfil_usuario"],
            self.perfil_paciente,
        )

    # 32. MOSTRAR FORMULARIO DE EDICIÓN
    def test_editar_perfil_get_correcto(self):

        respuesta = self.client.get(
            reverse("usuarios:editar_perfil")
        )

        self.assertEqual(respuesta.status_code, 200)

    # 33. ACTUALIZAR DATOS DEL PERFIL
    def test_editar_perfil_actualiza_datos(self):

        respuesta = self.client.post(
            reverse("usuarios:editar_perfil"),
            {
                "nombre": "Nuevo",
                "apellidos": "Apellido",
                "email": "nuevo.correo@ejemplo.com",
                "telefono": "5512345678",
            },
        )

        self.assertEqual(respuesta.status_code, 302)

        self.usuario_paciente.refresh_from_db()
        self.perfil_paciente.refresh_from_db()

        self.assertEqual(
            self.usuario_paciente.first_name,
            "Nuevo",
        )

        self.assertEqual(
            self.usuario_paciente.last_name,
            "Apellido",
        )

        self.assertEqual(
            self.usuario_paciente.email,
            "nuevo.correo@ejemplo.com",
        )

        self.assertEqual(
            self.perfil_paciente.telefono,
            "5512345678",
        )

    # 34. NO PERMITIR CORREO DE OTRO USUARIO
    def test_editar_perfil_rechaza_correo_ajeno(self):

        correo_original = self.usuario_paciente.email

        respuesta = self.client.post(
            reverse("usuarios:editar_perfil"),
            {
                "nombre": "Nuevo",
                "apellidos": "Apellido",
                "email": self.admin.email.upper(),
                "telefono": "5500000000",
            },
        )

        self.assertEqual(respuesta.status_code, 200)

        self.usuario_paciente.refresh_from_db()

        self.assertEqual(
            self.usuario_paciente.email,
            correo_original,
        )

    # 35. NO PERMITIR CORREO INVÁLIDO
    def test_editar_perfil_rechaza_correo_invalido(self):

        correo_original = self.usuario_paciente.email

        respuesta = self.client.post(
            reverse("usuarios:editar_perfil"),
            {
                "nombre": "Nuevo",
                "apellidos": "Apellido",
                "email": "incorrecto",
                "telefono": "5500000000",
            },
        )

        self.assertEqual(respuesta.status_code, 200)

        self.usuario_paciente.refresh_from_db()

        self.assertEqual(
            self.usuario_paciente.email,
            correo_original,
        )

    # 36. NO PERMITIR CORREO VACÍO
    def test_editar_perfil_rechaza_correo_vacio(self):

        respuesta = self.client.post(
            reverse("usuarios:editar_perfil"),
            {
                "nombre": "Nuevo",
                "apellidos": "Apellido",
                "email": "",
                "telefono": "5500000000",
            },
        )

        self.assertEqual(respuesta.status_code, 200)

        self.usuario_paciente.refresh_from_db()

        self.assertEqual(
            self.usuario_paciente.email,
            "paciente@ejemplo.com",
        )

    # 37. MOSTRAR FORMULARIO DE CONTRASEÑA
    def test_cambiar_contrasena_get_correcto(self):

        respuesta = self.client.get(
            reverse("usuarios:cambiar_contrasena")
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertIn(
            "formulario",
            respuesta.context,
        )

    # 38. CAMBIAR CONTRASEÑA CORRECTAMENTE
    def test_cambiar_contrasena_correctamente(self):

        respuesta = self.client.post(
            reverse("usuarios:cambiar_contrasena"),
            {
                "old_password": "Prueba12345!",
                "new_password1": "NuevaClaveSegura9081!",
                "new_password2": "NuevaClaveSegura9081!",
            },
        )

        self.assertEqual(respuesta.status_code, 302)

        self.usuario_paciente.refresh_from_db()

        self.assertTrue(
            self.usuario_paciente.check_password(
                "NuevaClaveSegura9081!"
            )
        )

        self.assertEqual(
            self.client.get(
                reverse("usuarios:perfil")
            ).status_code,
            200,
        )

    # 39. CONTRASEÑA ACTUAL INCORRECTA
    def test_cambiar_contrasena_rechaza_contrasena_actual_incorrecta(self):

        respuesta = self.client.post(
            reverse("usuarios:cambiar_contrasena"),
            {
                "old_password": "NoEsLaActual9081!",
                "new_password1": "NuevaClaveSegura9081!",
                "new_password2": "NuevaClaveSegura9081!",
            },
        )

        self.assertEqual(respuesta.status_code, 200)

        self.usuario_paciente.refresh_from_db()

        self.assertTrue(
            self.usuario_paciente.check_password(
                "Prueba12345!"
            )
        )


# =========================================================
# PRUEBAS DE LOS CUATRO DASHBOARDS
# =========================================================

class DashboardsUsuariosTests(DatosUsuarios):

    # 40. ESTADÍSTICAS DEL ADMINISTRADOR
    def test_dashboard_administrador_muestra_cifras(self):

        cita = self.crear_cita()

        self.crear_cita(
            hora=time(11, 0),
            estado=Cita.Estado.CANCELADA,
        )

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            reverse("usuarios:dashboard_administrador")
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            respuesta.context["total_pacientes"],
            1,
        )

        self.assertEqual(
            respuesta.context["total_fisioterapeutas"],
            1,
        )

        self.assertEqual(
            respuesta.context["ingreso_estimado"],
            Decimal("400.00"),
        )

        self.assertIn(
            cita,
            list(respuesta.context["citas"]),
        )

    # 41. RECEPCIÓN NO CUENTA CITAS CANCELADAS DEL DÍA
    def test_dashboard_recepcionista_excluye_canceladas_del_dia(self):

        hoy = timezone.localdate()

        cita = self.crear_cita(
            fecha=hoy
        )

        self.crear_cita(
            fecha=hoy,
            hora=time(11, 0),
            estado=Cita.Estado.CANCELADA,
        )

        self.client.force_login(
            self.recepcionista
        )

        respuesta = self.client.get(
            reverse("usuarios:dashboard_recepcionista")
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            respuesta.context["citas_hoy"],
            1,
        )

        self.assertIn(
            cita,
            list(respuesta.context["citas"]),
        )

    # 42. FISIOTERAPEUTA SOLO VE SUS CITAS
    def test_dashboard_fisio_solo_muestra_citas_asignadas(self):

        Usuario = get_user_model()

        otro_usuario = Usuario.objects.create_user(
            username="otro_fisio_usuarios",
            password="Prueba12345!",
        )

        otro_perfil = PerfilUsuario.objects.create(
            usuario=otro_usuario,
            rol=PerfilUsuario.Rol.FISIOTERAPEUTA,
        )

        otro_fisio = Fisioterapeuta.objects.create(
            usuario=otro_perfil
        )

        propia = self.crear_cita(
            fecha=timezone.localdate()
        )

        ajena = self.crear_cita(
            fisioterapeuta=otro_fisio,
            fecha=timezone.localdate(),
        )

        self.client.force_login(
            self.usuario_fisio
        )

        respuesta = self.client.get(
            reverse("usuarios:dashboard_fisioterapeuta")
        )

        self.assertEqual(respuesta.status_code, 200)

        resultados = list(
            respuesta.context["citas"]
        )

        self.assertIn(
            propia,
            resultados,
        )

        self.assertNotIn(
            ajena,
            resultados,
        )

    # 43. PACIENTE SOLO VE SUS CITAS
    def test_dashboard_paciente_solo_muestra_citas_propias(self):

        Usuario = get_user_model()

        otro_usuario = Usuario.objects.create_user(
            username="otro_paciente_usuarios",
            password="Prueba12345!",
        )

        otro_perfil = PerfilUsuario.objects.create(
            usuario=otro_usuario,
            rol=PerfilUsuario.Rol.PACIENTE,
        )

        otro_paciente = Paciente.objects.create(
            usuario=otro_perfil
        )

        propia = self.crear_cita()

        ajena = self.crear_cita(
            paciente=otro_paciente,
            hora=time(11, 0),
        )

        self.client.force_login(
            self.usuario_paciente
        )

        respuesta = self.client.get(
            reverse("usuarios:dashboard_paciente")
        )

        self.assertEqual(respuesta.status_code, 200)

        resultados = list(
            respuesta.context["citas"]
        )

        self.assertIn(
            propia,
            resultados,
        )

        self.assertNotIn(
            ajena,
            resultados,
        )

        self.assertEqual(
            respuesta.context["citas_pendientes"],
            1,
        )

    # 44. FILTRO EXCLUYE CITAS CANCELADAS Y FINALIZADAS
    def test_filtro_citas_futuras_excluye_canceladas_y_finalizadas(self):

        programada = self.crear_cita()

        confirmada = self.crear_cita(
            hora=time(11, 0),
            estado=Cita.Estado.CONFIRMADA,
        )

        self.crear_cita(
            hora=time(12, 0),
            estado=Cita.Estado.CANCELADA,
        )

        self.crear_cita(
            hora=time(13, 0),
            estado=Cita.Estado.FINALIZADA,
        )

        resultados = list(
            obtener_citas_futuras(
                Cita.objects.all()
            )
        )

        self.assertEqual(
            set(resultados),
            {programada, confirmada},
        )

    # 45. FILTRO EXCLUYE FECHAS PASADAS
    def test_filtro_citas_futuras_excluye_fechas_pasadas(self):

        self.crear_cita(
            fecha=timezone.localdate() - timedelta(days=1)
        )

        futura = self.crear_cita()

        resultados = list(
            obtener_citas_futuras(
                Cita.objects.all()
            )
        )

        self.assertEqual(
            resultados,
            [futura],
        )
