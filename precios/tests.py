
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from citas.forms import CitaForm
from usuarios.models import PerfilUsuario

from .forms import ServicioForm
from .models import Servicio


# =========================================================
# DATOS COMPARTIDOS
# =========================================================

class DatosPrecios(TestCase):

    @classmethod
    def setUpTestData(cls):

        Usuario = get_user_model()

        def crear_usuario(nombre, rol):

            usuario = Usuario.objects.create_user(
                username=f"{nombre}_precios_tests",
                password="Prueba12345!",
                email=f"{nombre}@ejemplo.com",
            )

            perfil = PerfilUsuario.objects.create(
                usuario=usuario,
                rol=rol,
            )

            return usuario, perfil

        cls.admin, cls.perfil_admin = crear_usuario(
            "admin",
            PerfilUsuario.Rol.ADMINISTRADOR,
        )

        cls.recepcionista, cls.perfil_recepcionista = crear_usuario(
            "recepcionista",
            PerfilUsuario.Rol.RECEPCIONISTA,
        )

        cls.usuario_fisio, cls.perfil_fisio = crear_usuario(
            "fisio",
            PerfilUsuario.Rol.FISIOTERAPEUTA,
        )

        cls.usuario_paciente, cls.perfil_paciente = crear_usuario(
            "paciente",
            PerfilUsuario.Rol.PACIENTE,
        )

        cls.servicio_activo = Servicio.objects.create(
            nombre="Consulta general",
            descripcion="Evaluación y recuperación muscular",
            precio_base=Decimal("500.00"),
            activo=True,
        )

        cls.servicio_inactivo = Servicio.objects.create(
            nombre="Terapia avanzada",
            descripcion="Tratamiento especializado",
            precio_base=Decimal("700.00"),
            activo=False,
        )

    def datos_servicio(self, **cambios):

        datos = {
            "nombre": "Rehabilitación funcional",
            "descripcion": "Tratamiento de rehabilitación",
            "precio_base": "350.00",
            "activo": "on",
        }

        datos.update(cambios)
        return datos

    def ruta(self, nombre, servicio=None):

        if servicio is None:
            return reverse(
                f"precios:{nombre}"
            )

        return reverse(
            f"precios:{nombre}",
            args=[servicio.pk],
        )


# =========================================================
# PRUEBAS DEL MODELO Y FORMULARIO
# =========================================================

class FormularioPreciosTests(DatosPrecios):

    # 1
    def test_modelo_muestra_nombre_y_precio(self):

        self.assertEqual(
            str(self.servicio_activo),
            "Consulta general - $500.00",
        )

    # 2
    def test_modelo_ordena_servicios_por_nombre(self):

        servicios = list(
            Servicio.objects.all()
        )

        self.assertEqual(
            servicios,
            [
                self.servicio_activo,
                self.servicio_inactivo,
            ],
        )

    # 3
    def test_formulario_acepta_datos_validos(self):

        formulario = ServicioForm(
            data=self.datos_servicio()
        )

        self.assertTrue(
            formulario.is_valid(),
            formulario.errors,
        )

    # 4
    def test_formulario_elimina_espacios_del_nombre(self):

        formulario = ServicioForm(
            data=self.datos_servicio(
                nombre="  Rehabilitación funcional  "
            )
        )

        self.assertTrue(
            formulario.is_valid(),
            formulario.errors,
        )

        self.assertEqual(
            formulario.cleaned_data["nombre"],
            "Rehabilitación funcional",
        )

    # 5
    def test_formulario_rechaza_nombre_vacio(self):

        formulario = ServicioForm(
            data=self.datos_servicio(
                nombre="   "
            )
        )

        self.assertFalse(
            formulario.is_valid()
        )

        self.assertIn(
            "nombre",
            formulario.errors,
        )

    # 6
    def test_formulario_rechaza_nombre_duplicado(self):

        formulario = ServicioForm(
            data=self.datos_servicio(
                nombre="CONSULTA GENERAL"
            )
        )

        self.assertFalse(
            formulario.is_valid()
        )

        self.assertIn(
            "nombre",
            formulario.errors,
        )

    # 7
    def test_edicion_permite_conservar_el_nombre_propio(self):

        formulario = ServicioForm(
            data=self.datos_servicio(
                nombre="Consulta general"
            ),
            instance=self.servicio_activo,
        )

        self.assertTrue(
            formulario.is_valid(),
            formulario.errors,
        )

    # 8
    def test_formulario_rechaza_precio_cero(self):

        formulario = ServicioForm(
            data=self.datos_servicio(
                precio_base="0"
            )
        )

        self.assertFalse(
            formulario.is_valid()
        )

        self.assertIn(
            "precio_base",
            formulario.errors,
        )

    # 9
    def test_formulario_rechaza_precio_negativo(self):

        formulario = ServicioForm(
            data=self.datos_servicio(
                precio_base="-50.00"
            )
        )

        self.assertFalse(
            formulario.is_valid()
        )

        self.assertIn(
            "precio_base",
            formulario.errors,
        )

    # 10
    def test_formulario_rechaza_tres_decimales(self):

        formulario = ServicioForm(
            data=self.datos_servicio(
                precio_base="250.999"
            )
        )

        self.assertFalse(
            formulario.is_valid()
        )

        self.assertIn(
            "precio_base",
            formulario.errors,
        )

    # 11
    def test_formulario_rechaza_precio_demasiado_grande(self):

        formulario = ServicioForm(
            data=self.datos_servicio(
                precio_base="1000000.00"
            )
        )

        self.assertFalse(
            formulario.is_valid()
        )

        self.assertIn(
            "precio_base",
            formulario.errors,
        )

    # 12
    def test_formulario_acepta_precio_minimo(self):

        formulario = ServicioForm(
            data=self.datos_servicio(
                precio_base="0.01"
            )
        )

        self.assertTrue(
            formulario.is_valid(),
            formulario.errors,
        )

        self.assertEqual(
            formulario.cleaned_data["precio_base"],
            Decimal("0.01"),
        )

    # 13
    def test_formulario_permite_servicio_inactivo(self):

        formulario = ServicioForm(
            data=self.datos_servicio(
                activo=""
            )
        )

        self.assertTrue(
            formulario.is_valid(),
            formulario.errors,
        )

        self.assertFalse(
            formulario.cleaned_data["activo"]
        )

    # 14
    def test_formulario_citas_excluye_servicios_inactivos(self):

        formulario = CitaForm()

        servicios = formulario.fields[
            "servicio"
        ].queryset

        self.assertIn(
            self.servicio_activo,
            servicios,
        )

        self.assertNotIn(
            self.servicio_inactivo,
            servicios,
        )


# =========================================================
# PRUEBAS DEL LISTADO Y PERMISOS
# =========================================================

class ListadoPreciosTests(DatosPrecios):

    # 15
    def test_administrador_ve_todos_los_servicios(self):

        self.client.force_login(
            self.admin
        )

        respuesta = self.client.get(
            self.ruta("lista_precios")
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertEqual(
            set(respuesta.context["servicios"]),
            {
                self.servicio_activo,
                self.servicio_inactivo,
            },
        )

        self.assertTrue(
            respuesta.context["puede_gestionar"]
        )

    # 16
    def test_recepcionista_solo_ve_servicios_activos(self):

        self.client.force_login(
            self.recepcionista
        )

        respuesta = self.client.get(
            self.ruta("lista_precios")
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertEqual(
            list(respuesta.context["servicios"]),
            [self.servicio_activo],
        )

        self.assertFalse(
            respuesta.context["puede_gestionar"]
        )

    # 17
    def test_paciente_solo_ve_servicios_activos(self):

        self.client.force_login(
            self.usuario_paciente
        )

        respuesta = self.client.get(
            self.ruta("lista_precios")
        )

        self.assertEqual(
            list(respuesta.context["servicios"]),
            [self.servicio_activo],
        )

    # 18
    def test_fisioterapeuta_solo_ve_servicios_activos(self):

        self.client.force_login(
            self.usuario_fisio
        )

        respuesta = self.client.get(
            self.ruta("lista_precios")
        )

        self.assertEqual(
            list(respuesta.context["servicios"]),
            [self.servicio_activo],
        )

    # 19
    def test_busqueda_por_nombre(self):

        self.client.force_login(
            self.admin
        )

        respuesta = self.client.get(
            self.ruta("lista_precios"),
            {
                "buscar": "Terapia avanzada",
            },
        )

        self.assertEqual(
            list(respuesta.context["servicios"]),
            [self.servicio_inactivo],
        )

    # 20
    def test_busqueda_por_descripcion(self):

        self.client.force_login(
            self.usuario_paciente
        )

        respuesta = self.client.get(
            self.ruta("lista_precios"),
            {
                "buscar": "recuperación muscular",
            },
        )

        self.assertEqual(
            list(respuesta.context["servicios"]),
            [self.servicio_activo],
        )

    # 21
    def test_busqueda_sin_resultados(self):

        self.client.force_login(
            self.usuario_paciente
        )

        respuesta = self.client.get(
            self.ruta("lista_precios"),
            {
                "buscar": "Servicio inexistente",
            },
        )

        self.assertEqual(
            list(respuesta.context["servicios"]),
            [],
        )

    # 22
    def test_listado_requiere_inicio_de_sesion(self):

        respuesta = self.client.get(
            self.ruta("lista_precios")
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

    # 23
    def test_perfil_inactivo_no_accede(self):

        self.perfil_admin.activo = False

        self.perfil_admin.save(
            update_fields=["activo"]
        )

        self.client.force_login(
            self.admin
        )

        respuesta = self.client.get(
            self.ruta("lista_precios")
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

    # 24
    def test_superusuario_con_perfil_inactivo_no_accede(self):

        superusuario = (
            get_user_model().objects.create_superuser(
                username="super_inactivo_precios",
                email="super_inactivo@ejemplo.com",
                password="Prueba12345!",
            )
        )

        PerfilUsuario.objects.create(
            usuario=superusuario,
            rol=PerfilUsuario.Rol.ADMINISTRADOR,
            activo=False,
        )

        self.client.force_login(
            superusuario
        )

        respuesta = self.client.get(
            self.ruta("lista_precios")
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

    # 25
    def test_superusuario_sin_perfil_ve_todos(self):

        superusuario = (
            get_user_model().objects.create_superuser(
                username="super_sin_perfil_precios",
                email="super_sin_perfil@ejemplo.com",
                password="Prueba12345!",
            )
        )

        self.client.force_login(
            superusuario
        )

        respuesta = self.client.get(
            self.ruta("lista_precios")
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertTrue(
            respuesta.context["puede_gestionar"]
        )

        self.assertEqual(
            len(respuesta.context["servicios"]),
            2,
        )

    # 26
    def test_usuario_normal_sin_perfil_no_accede(self):

        usuario = get_user_model().objects.create_user(
            username="sin_perfil_precios",
            password="Prueba12345!",
        )

        self.client.force_login(
            usuario
        )

        respuesta = self.client.get(
            self.ruta("lista_precios")
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )


# =========================================================
# PRUEBAS DE REGISTRO Y EDICIÓN
# =========================================================

class GestionPreciosTests(DatosPrecios):

    # 27
    def test_administrador_abre_formulario_registro(self):

        self.client.force_login(
            self.admin
        )

        respuesta = self.client.get(
            self.ruta("registrar_precio")
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertTrue(
            respuesta.context["form"].initial["activo"]
        )

    # 28
    def test_administrador_registra_servicio(self):

        self.client.force_login(
            self.admin
        )

        respuesta = self.client.post(
            self.ruta("registrar_precio"),
            self.datos_servicio(),
        )

        self.assertRedirects(
            respuesta,
            self.ruta("lista_precios"),
            fetch_redirect_response=False,
        )

        nuevo = Servicio.objects.get(
            nombre="Rehabilitación funcional"
        )

        self.assertEqual(
            nuevo.precio_base,
            Decimal("350.00"),
        )

        self.assertTrue(
            nuevo.activo
        )

    # 29
    def test_administrador_registra_servicio_inactivo(self):

        self.client.force_login(
            self.admin
        )

        respuesta = self.client.post(
            self.ruta("registrar_precio"),
            self.datos_servicio(
                activo=""
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        nuevo = Servicio.objects.get(
            nombre="Rehabilitación funcional"
        )

        self.assertFalse(
            nuevo.activo
        )

    # 30
    def test_registro_rechaza_nombre_duplicado(self):

        self.client.force_login(
            self.admin
        )

        respuesta = self.client.post(
            self.ruta("registrar_precio"),
            self.datos_servicio(
                nombre="consulta general"
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertIn(
            "nombre",
            respuesta.context["form"].errors,
        )

        self.assertEqual(
            Servicio.objects.count(),
            2,
        )

    # 31
    def test_registro_rechaza_precio_invalido(self):

        self.client.force_login(
            self.admin
        )

        respuesta = self.client.post(
            self.ruta("registrar_precio"),
            self.datos_servicio(
                precio_base="-100.00"
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertIn(
            "precio_base",
            respuesta.context["form"].errors,
        )

        self.assertEqual(
            Servicio.objects.count(),
            2,
        )

    # 32
    def test_registro_rechaza_nombre_solo_espacios(self):

        self.client.force_login(
            self.admin
        )

        respuesta = self.client.post(
            self.ruta("registrar_precio"),
            self.datos_servicio(
                nombre="   "
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertEqual(
            Servicio.objects.count(),
            2,
        )

    # 33
    def test_paciente_no_puede_registrar_servicios(self):

        self.client.force_login(
            self.usuario_paciente
        )

        respuesta = self.client.post(
            self.ruta("registrar_precio"),
            self.datos_servicio(),
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:redireccion_por_rol"),
            fetch_redirect_response=False,
        )

        self.assertFalse(
            Servicio.objects.filter(
                nombre="Rehabilitación funcional"
            ).exists()
        )

    # 34
    def test_recepcionista_no_puede_registrar_servicios(self):

        self.client.force_login(
            self.recepcionista
        )

        respuesta = self.client.post(
            self.ruta("registrar_precio"),
            self.datos_servicio(),
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:redireccion_por_rol"),
            fetch_redirect_response=False,
        )

        self.assertEqual(
            Servicio.objects.count(),
            2,
        )

    # 35
    def test_administrador_abre_formulario_edicion(self):

        self.client.force_login(
            self.admin
        )

        respuesta = self.client.get(
            self.ruta(
                "editar_precio",
                self.servicio_activo,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertEqual(
            respuesta.context["servicio"],
            self.servicio_activo,
        )

    # 36
    def test_administrador_actualiza_servicio(self):

        self.client.force_login(
            self.admin
        )

        respuesta = self.client.post(
            self.ruta(
                "editar_precio",
                self.servicio_activo,
            ),
            self.datos_servicio(
                nombre="Consulta actualizada",
                descripcion="Servicio actualizado",
                precio_base="650.50",
                activo="",
            ),
        )

        self.assertRedirects(
            respuesta,
            self.ruta("lista_precios"),
            fetch_redirect_response=False,
        )

        self.servicio_activo.refresh_from_db()

        self.assertEqual(
            self.servicio_activo.nombre,
            "Consulta actualizada",
        )

        self.assertEqual(
            self.servicio_activo.precio_base,
            Decimal("650.50"),
        )

        self.assertFalse(
            self.servicio_activo.activo
        )

    # 37
    def test_edicion_rechaza_precio_invalido(self):

        self.client.force_login(
            self.admin
        )

        respuesta = self.client.post(
            self.ruta(
                "editar_precio",
                self.servicio_activo,
            ),
            self.datos_servicio(
                precio_base="0"
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.servicio_activo.refresh_from_db()

        self.assertEqual(
            self.servicio_activo.precio_base,
            Decimal("500.00"),
        )

    # 38
    def test_edicion_rechaza_nombre_de_otro_servicio(self):

        self.client.force_login(
            self.admin
        )

        respuesta = self.client.post(
            self.ruta(
                "editar_precio",
                self.servicio_activo,
            ),
            self.datos_servicio(
                nombre="TERAPIA AVANZADA"
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertIn(
            "nombre",
            respuesta.context["form"].errors,
        )

        self.servicio_activo.refresh_from_db()

        self.assertEqual(
            self.servicio_activo.nombre,
            "Consulta general",
        )

    # 39
    def test_recepcionista_no_puede_editar_precios(self):

        self.client.force_login(
            self.recepcionista
        )

        respuesta = self.client.post(
            self.ruta(
                "editar_precio",
                self.servicio_activo,
            ),
            self.datos_servicio(
                precio_base="1.00"
            ),
        )

        self.assertRedirects(
            respuesta,
            reverse("usuarios:redireccion_por_rol"),
            fetch_redirect_response=False,
        )

        self.servicio_activo.refresh_from_db()

        self.assertEqual(
            self.servicio_activo.precio_base,
            Decimal("500.00"),
        )

    # 40
    def test_editar_servicio_inexistente_devuelve_404(self):

        self.client.force_login(
            self.admin
        )

        respuesta = self.client.get(
            reverse(
                "precios:editar_precio",
                args=[999999],
            )
        )

        self.assertEqual(
            respuesta.status_code,
            404,
        )
