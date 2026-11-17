
from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from citas.models import Cita, MotivoConsulta
from fisioterapeutas.models import Fisioterapeuta
from precios.models import Servicio
from usuarios.models import PerfilUsuario

from .forms import EditarPacienteForm, RegistrarPacienteForm
from .models import Paciente


# =========================================================
# DATOS COMPARTIDOS PARA LAS PRUEBAS
# =========================================================

class DatosPacientes(TestCase):

    @classmethod
    def setUpTestData(cls):

        Usuario = get_user_model()

        def cuenta(nombre, rol, **kwargs):

            user = Usuario.objects.create_user(
                username=nombre,
                password="Prueba12345!",
                email=f"{nombre}@ejemplo.com",
                first_name=kwargs.get(
                    "first_name", nombre
                ),
                last_name=kwargs.get(
                    "last_name", "Apellido"
                ),
            )

            perfil = PerfilUsuario.objects.create(
                usuario=user,
                rol=rol,
                telefono=kwargs.get(
                    "telefono", "5511111111"
                ),
            )

            return user, perfil

        cls.admin, cls.perfil_admin = cuenta(
            "admin_pacientes",
            PerfilUsuario.Rol.ADMINISTRADOR,
        )

        cls.recep, cls.perfil_recep = cuenta(
            "recep_pacientes",
            PerfilUsuario.Rol.RECEPCIONISTA,
        )

        cls.user_fisio, cls.perfil_fisio = cuenta(
            "fisio_pacientes",
            PerfilUsuario.Rol.FISIOTERAPEUTA,
        )

        cls.user_otro_fisio, cls.perfil_otro_fisio = cuenta(
            "otro_fisio_pacientes",
            PerfilUsuario.Rol.FISIOTERAPEUTA,
        )

        cls.user_paciente, cls.perfil_paciente = cuenta(
            "ana_paciente",
            PerfilUsuario.Rol.PACIENTE,
            first_name="Ana",
            last_name="Garcia",
            telefono="5512345678",
        )

        cls.user_ajeno, cls.perfil_ajeno = cuenta(
            "bruno_paciente",
            PerfilUsuario.Rol.PACIENTE,
            first_name="Bruno",
            last_name="Lopez",
            telefono="5598765432",
        )

        cls.paciente = Paciente.objects.create(
            usuario=cls.perfil_paciente,
            antecedentes_medicos="Antecedente confidencial",
        )

        cls.paciente_ajeno = Paciente.objects.create(
            usuario=cls.perfil_ajeno,
        )

        cls.fisio = Fisioterapeuta.objects.create(
            usuario=cls.perfil_fisio,
        )

        cls.otro_fisio = Fisioterapeuta.objects.create(
            usuario=cls.perfil_otro_fisio,
        )

        cls.servicio = Servicio.objects.create(
            nombre="Servicio pacientes pruebas",
            precio_base=Decimal("400.00"),
        )

        cls.motivo = MotivoConsulta.objects.create(
            nombre="Motivo pacientes pruebas"
        )

    def datos_formulario(self, **cambios):

        datos = {
            "nombre": "Luisa",
            "apellidos": "Martinez",
            "email": "luisa.nueva@ejemplo.com",
            "telefono": "5512340000",
            "fecha_nacimiento": "1999-04-15",
            "direccion": "Calle Central 123",
            "contacto_emergencia": "Familiar",
            "telefono_emergencia": "5512349999",
            "antecedentes_medicos": "Dato clínico privado",
            "username": "luisa_nueva_pacientes",
            "password1": "ClaveSegura9876!",
            "password2": "ClaveSegura9876!",
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
            "costo_estimado": Decimal("400.00"),
        }

        datos.update(cambios)
        return Cita.objects.create(**datos)

    def url(self, nombre, paciente=None):

        if paciente is None:
            return reverse(
                f"pacientes:{nombre}"
            )

        return reverse(
            f"pacientes:{nombre}",
            args=[paciente.pk],
        )


# =========================================================
# PRUEBAS DE FORMULARIOS
# =========================================================

class FormulariosPacientesTests(DatosPacientes):

    # 1
    def test_registro_formulario_valido(self):

        form = RegistrarPacienteForm(
            data=self.datos_formulario(),
            incluir_antecedentes=True,
        )

        self.assertTrue(
            form.is_valid(),
            form.errors,
        )

        self.assertEqual(
            form.cleaned_data["email"],
            "luisa.nueva@ejemplo.com",
        )

    # 2
    def test_registro_rechaza_usuario_duplicado_sin_importar_mayusculas(self):

        form = RegistrarPacienteForm(
            data=self.datos_formulario(
                username=self.user_paciente.username.upper()
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    # 3
    def test_registro_rechaza_correo_duplicado_sin_importar_mayusculas(self):

        form = RegistrarPacienteForm(
            data=self.datos_formulario(
                email=self.user_paciente.email.upper()
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    # 4
    def test_registro_rechaza_contrasenas_diferentes(self):

        form = RegistrarPacienteForm(
            data=self.datos_formulario(
                password2="OtraSegura9876!"
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    # 5
    def test_registro_rechaza_contrasena_debil(self):

        form = RegistrarPacienteForm(
            data=self.datos_formulario(
                password1="123",
                password2="123",
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn("password1", form.errors)

    # 6
    def test_registro_rechaza_fecha_futura(self):

        manana = (
            timezone.localdate()
            + timedelta(days=1)
        ).isoformat()

        form = RegistrarPacienteForm(
            data=self.datos_formulario(
                fecha_nacimiento=manana
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn(
            "fecha_nacimiento",
            form.errors,
        )

    # 7
    def test_registro_rechaza_correo_invalido(self):

        form = RegistrarPacienteForm(
            data=self.datos_formulario(
                email="esto-no-es-un-correo"
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    # 8
    def test_registro_rechaza_username_invalido(self):

        form = RegistrarPacienteForm(
            data=self.datos_formulario(
                username="nombre con espacios"
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    # 9
    def test_antecedentes_solo_aparecen_si_se_autorizan(self):

        sin_antecedentes = RegistrarPacienteForm()

        con_antecedentes = RegistrarPacienteForm(
            incluir_antecedentes=True
        )

        self.assertNotIn(
            "antecedentes_medicos",
            sin_antecedentes.fields,
        )

        self.assertIn(
            "antecedentes_medicos",
            con_antecedentes.fields,
        )

    # 10
    def test_edicion_permite_conservar_correo_propio(self):

        form = EditarPacienteForm(
            data=self.datos_formulario(
                email=self.user_paciente.email
            ),
            usuario_actual=self.user_paciente,
        )

        self.assertTrue(
            form.is_valid(),
            form.errors,
        )

    # 11
    def test_edicion_rechaza_correo_de_otro_usuario(self):

        form = EditarPacienteForm(
            data=self.datos_formulario(
                email=self.user_ajeno.email
            ),
            usuario_actual=self.user_paciente,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


# =========================================================
# PRUEBAS DE LISTADO Y DETALLE
# =========================================================

class ConsultasPacientesTests(DatosPacientes):

    # 12
    def test_admin_lista_todos_los_pacientes(self):

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.url("lista_pacientes")
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertEqual(
            set(respuesta.context["pacientes"]),
            {
                self.paciente,
                self.paciente_ajeno,
            },
        )

        self.assertTrue(
            respuesta.context["puede_gestionar"]
        )

    # 13
    def test_recepcionista_lista_todos_los_pacientes(self):

        self.client.force_login(self.recep)

        respuesta = self.client.get(
            self.url("lista_pacientes")
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertEqual(
            len(respuesta.context["pacientes"]),
            2,
        )

    # 14
    def test_fisio_solo_lista_pacientes_asignados(self):

        self.crear_cita()

        self.crear_cita(
            paciente=self.paciente_ajeno,
            fisioterapeuta=self.otro_fisio,
        )

        self.client.force_login(
            self.user_fisio
        )

        respuesta = self.client.get(
            self.url("lista_pacientes")
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertEqual(
            list(respuesta.context["pacientes"]),
            [self.paciente],
        )

        self.assertFalse(
            respuesta.context["puede_gestionar"]
        )

    # 15
    def test_fisio_no_duplica_pacientes_con_varias_citas(self):

        self.crear_cita()
        self.crear_cita(hora=time(11, 0))

        self.client.force_login(
            self.user_fisio
        )

        respuesta = self.client.get(
            self.url("lista_pacientes")
        )

        self.assertEqual(
            len(respuesta.context["pacientes"]),
            1,
        )

    # 16
    def test_paciente_no_accede_al_listado_general(self):

        self.client.force_login(
            self.user_paciente
        )

        respuesta = self.client.get(
            self.url("lista_pacientes")
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

    # 17
    def test_listado_sin_sesion_redirige(self):

        respuesta = self.client.get(
            self.url("lista_pacientes")
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

    # 18
    def test_busqueda_filtra_por_nombre(self):

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.url("lista_pacientes"),
            {"buscar": "Ana"},
        )

        self.assertEqual(
            list(respuesta.context["pacientes"]),
            [self.paciente],
        )

    # 19
    def test_busqueda_filtra_por_correo(self):

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.url("lista_pacientes"),
            {"buscar": "bruno_paciente@"},
        )

        self.assertEqual(
            list(respuesta.context["pacientes"]),
            [self.paciente_ajeno],
        )

    # 20
    def test_perfil_inactivo_no_accede_al_listado(self):

        self.perfil_admin.activo = False

        self.perfil_admin.save(
            update_fields=["activo"]
        )

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.url("lista_pacientes")
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

    # 21
    def test_superusuario_con_perfil_inactivo_no_accede(self):

        superusuario = (
            get_user_model().objects.create_superuser(
                username="super_inactivo_pacientes",
                email="super_inactivo@ejemplo.com",
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
            self.url("lista_pacientes")
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

    # 22
    def test_admin_ve_detalle_de_paciente(self):

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.url(
                "detalle_paciente",
                self.paciente,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertEqual(
            respuesta.context["paciente"],
            self.paciente,
        )

        self.assertTrue(
            respuesta.context["puede_desactivar"]
        )

    # 23
    def test_recepcionista_no_tiene_permiso_para_antecedentes(self):

        self.client.force_login(self.recep)

        respuesta = self.client.get(
            self.url(
                "detalle_paciente",
                self.paciente,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertFalse(
            respuesta.context["puede_ver_antecedentes"]
        )

        self.assertFalse(
            respuesta.context["puede_historial"]
        )

    # 24
    def test_paciente_ve_solo_su_detalle(self):

        self.client.force_login(
            self.user_paciente
        )

        propia = self.client.get(
            self.url(
                "detalle_paciente",
                self.paciente,
            )
        )

        ajena = self.client.get(
            self.url(
                "detalle_paciente",
                self.paciente_ajeno,
            )
        )

        self.assertEqual(propia.status_code, 200)
        self.assertEqual(ajena.status_code, 404)

        self.assertFalse(
            propia.context["puede_gestionar"]
        )

    # 25
    def test_fisio_solo_ve_detalle_de_paciente_asignado(self):

        self.crear_cita()

        self.client.force_login(
            self.user_fisio
        )

        propia = self.client.get(
            self.url(
                "detalle_paciente",
                self.paciente,
            )
        )

        ajena = self.client.get(
            self.url(
                "detalle_paciente",
                self.paciente_ajeno,
            )
        )

        self.assertEqual(propia.status_code, 200)
        self.assertEqual(ajena.status_code, 404)


# =========================================================
# PRUEBAS DE REGISTRO DE PACIENTES
# =========================================================

class RegistrarPacientesTests(DatosPacientes):

    # 26
    def test_admin_puede_abrir_registro(self):

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.url("registrar_paciente")
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertIn(
            "antecedentes_medicos",
            respuesta.context["form"].fields,
        )

    # 27
    def test_recepcionista_puede_abrir_registro_sin_antecedentes(self):

        self.client.force_login(self.recep)

        respuesta = self.client.get(
            self.url("registrar_paciente")
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertNotIn(
            "antecedentes_medicos",
            respuesta.context["form"].fields,
        )

    # 28
    def test_paciente_no_puede_registrar_terceros(self):

        self.client.force_login(
            self.user_paciente
        )

        respuesta = self.client.post(
            self.url("registrar_paciente"),
            self.datos_formulario(),
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

        self.assertFalse(
            get_user_model().objects.filter(
                username="luisa_nueva_pacientes"
            ).exists()
        )

    # 29
    def test_fisio_no_puede_registrar_pacientes(self):

        self.client.force_login(
            self.user_fisio
        )

        respuesta = self.client.get(
            self.url("registrar_paciente")
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

    # 30
    def test_admin_registra_usuario_perfil_y_paciente(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.url("registrar_paciente"),
            self.datos_formulario(),
        )

        nuevo = get_user_model().objects.get(
            username="luisa_nueva_pacientes"
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.assertEqual(
            nuevo.perfil.rol,
            PerfilUsuario.Rol.PACIENTE,
        )

        self.assertTrue(
            nuevo.check_password(
                "ClaveSegura9876!"
            )
        )

        self.assertEqual(
            nuevo.perfil.paciente.antecedentes_medicos,
            "Dato clínico privado",
        )

        self.assertEqual(
            nuevo.perfil.paciente.direccion,
            "Calle Central 123",
        )

        self.assertEqual(
            respuesta.url,
            self.url(
                "detalle_paciente",
                nuevo.perfil.paciente,
            ),
        )

    # 31
    def test_recepcionista_no_puede_inyectar_antecedentes(self):

        self.client.force_login(self.recep)

        respuesta = self.client.post(
            self.url("registrar_paciente"),
            self.datos_formulario(),
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        nuevo = get_user_model().objects.get(
            username="luisa_nueva_pacientes"
        )

        self.assertEqual(
            nuevo.perfil.paciente.antecedentes_medicos,
            "",
        )

    # 32
    def test_registro_invalido_no_crea_usuario(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.url("registrar_paciente"),
            self.datos_formulario(
                password2="NoCoincide987!"
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertIn(
            "password2",
            respuesta.context["form"].errors,
        )

        self.assertFalse(
            get_user_model().objects.filter(
                username="luisa_nueva_pacientes"
            ).exists()
        )

    # 33
    def test_registro_sin_sesion_redirige(self):

        respuesta = self.client.post(
            self.url("registrar_paciente"),
            self.datos_formulario(),
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )


# =========================================================
# PRUEBAS DE EDICIÓN Y PRIVACIDAD
# =========================================================

class EditarPacientesTests(DatosPacientes):

    # 34
    def test_admin_actualiza_todos_los_datos(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.url(
                "editar_paciente",
                self.paciente,
            ),
            self.datos_formulario(),
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.user_paciente.refresh_from_db()
        self.perfil_paciente.refresh_from_db()
        self.paciente.refresh_from_db()

        self.assertEqual(
            self.user_paciente.first_name,
            "Luisa",
        )

        self.assertEqual(
            self.user_paciente.email,
            "luisa.nueva@ejemplo.com",
        )

        self.assertEqual(
            self.perfil_paciente.telefono,
            "5512340000",
        )

        self.assertEqual(
            self.paciente.direccion,
            "Calle Central 123",
        )

        self.assertEqual(
            self.paciente.antecedentes_medicos,
            "Dato clínico privado",
        )

    # 35
    def test_recepcion_no_modifica_antecedentes_medicos(self):

        self.client.force_login(self.recep)

        respuesta = self.client.post(
            self.url(
                "editar_paciente",
                self.paciente,
            ),
            self.datos_formulario(
                antecedentes_medicos="Intento de sobrescritura"
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.paciente.refresh_from_db()

        self.assertEqual(
            self.paciente.antecedentes_medicos,
            "Antecedente confidencial",
        )

        self.assertEqual(
            self.paciente.direccion,
            "Calle Central 123",
        )

    # 36
    def test_paciente_no_puede_usar_vista_de_edicion_administrativa(self):

        self.client.force_login(
            self.user_paciente
        )

        respuesta = self.client.get(
            self.url(
                "editar_paciente",
                self.paciente,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

    # 37
    def test_fisio_no_puede_editar_paciente(self):

        self.client.force_login(
            self.user_fisio
        )

        respuesta = self.client.get(
            self.url(
                "editar_paciente",
                self.paciente,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

    # 38
    def test_edicion_rechaza_correo_duplicado(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.url(
                "editar_paciente",
                self.paciente,
            ),
            self.datos_formulario(
                email=self.user_ajeno.email
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertIn(
            "email",
            respuesta.context["form"].errors,
        )

        self.user_paciente.refresh_from_db()

        self.assertEqual(
            self.user_paciente.email,
            "ana_paciente@ejemplo.com",
        )

    # 39
    def test_edicion_rechaza_fecha_nacimiento_futura(self):

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.url(
                "editar_paciente",
                self.paciente,
            ),
            self.datos_formulario(
                fecha_nacimiento=(
                    timezone.localdate()
                    + timedelta(days=1)
                ).isoformat()
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertIn(
            "fecha_nacimiento",
            respuesta.context["form"].errors,
        )

    # 40
    def test_edicion_get_carga_valores_iniciales(self):

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.url(
                "editar_paciente",
                self.paciente,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertEqual(
            respuesta.context["form"].initial["nombre"],
            "Ana",
        )

        self.assertEqual(
            respuesta.context["form"].initial[
                "antecedentes_medicos"
            ],
            "Antecedente confidencial",
        )


# =========================================================
# HISTORIAL CLÍNICO Y DESACTIVACIÓN
# =========================================================

class HistorialDesactivacionPacientesTests(DatosPacientes):

    # 41
    def test_admin_consulta_historial(self):

        cita = self.crear_cita()

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.url(
                "historial_paciente",
                self.paciente,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertIn(
            cita,
            list(respuesta.context["citas"]),
        )

    # 42
    def test_paciente_consulta_su_historial_no_el_ajeno(self):

        self.client.force_login(
            self.user_paciente
        )

        propia = self.client.get(
            self.url(
                "historial_paciente",
                self.paciente,
            )
        )

        ajena = self.client.get(
            self.url(
                "historial_paciente",
                self.paciente_ajeno,
            )
        )

        self.assertEqual(
            propia.status_code,
            200,
        )

        self.assertEqual(
            ajena.status_code,
            404,
        )

    # 43
    def test_fisio_historial_solo_con_sus_citas(self):

        propia = self.crear_cita()

        ajena = self.crear_cita(
            fisioterapeuta=self.otro_fisio,
            hora=time(11, 0),
        )

        self.client.force_login(
            self.user_fisio
        )

        respuesta = self.client.get(
            self.url(
                "historial_paciente",
                self.paciente,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertIn(
            propia,
            list(respuesta.context["citas"]),
        )

        self.assertNotIn(
            ajena,
            list(respuesta.context["citas"]),
        )

    # 44
    def test_recepcionista_no_consulta_historial_clinico(self):

        self.client.force_login(self.recep)

        respuesta = self.client.get(
            self.url(
                "historial_paciente",
                self.paciente,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

    # 45
    def test_fisio_sin_citas_no_ve_historial(self):

        self.client.force_login(
            self.user_fisio
        )

        respuesta = self.client.get(
            self.url(
                "historial_paciente",
                self.paciente,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            404,
        )

    # 46
    def test_eliminar_get_no_desactiva(self):

        self.client.force_login(self.admin)

        respuesta = self.client.get(
            self.url(
                "eliminar_paciente",
                self.paciente,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.paciente.refresh_from_db()

        self.assertTrue(
            self.paciente.activo
        )

    # 47
    def test_desactivar_bloquea_a_usuarios_no_admin(self):

        for usuario in (
            self.recep,
            self.user_fisio,
            self.user_paciente,
        ):

            with self.subTest(
                usuario=usuario.username
            ):

                self.client.force_login(usuario)

                respuesta = self.client.post(
                    self.url(
                        "eliminar_paciente",
                        self.paciente,
                    )
                )

                self.assertEqual(
                    respuesta.status_code,
                    403,
                )

        self.paciente.refresh_from_db()

        self.assertTrue(
            self.paciente.activo
        )

    # 48
    def test_admin_desactiva_sin_eliminar_historial(self):

        cita = self.crear_cita(
            estado=Cita.Estado.FINALIZADA
        )

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.url(
                "eliminar_paciente",
                self.paciente,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.paciente.refresh_from_db()
        self.perfil_paciente.refresh_from_db()
        self.user_paciente.refresh_from_db()

        self.assertFalse(
            self.paciente.activo
        )

        self.assertFalse(
            self.perfil_paciente.activo
        )

        self.assertFalse(
            self.user_paciente.is_active
        )

        self.assertTrue(
            Cita.objects.filter(
                pk=cita.pk
            ).exists()
        )

        self.assertTrue(
            Paciente.objects.filter(
                pk=self.paciente.pk
            ).exists()
        )

    # 49
    def test_no_desactiva_con_cita_programada_futura(self):

        self.crear_cita()

        self.client.force_login(self.admin)

        respuesta = self.client.post(
            self.url(
                "eliminar_paciente",
                self.paciente,
            )
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        self.paciente.refresh_from_db()
        self.perfil_paciente.refresh_from_db()

        self.assertTrue(
            self.paciente.activo
        )

        self.assertTrue(
            self.perfil_paciente.activo
        )

    # 50
    def test_no_desactiva_con_cita_confirmada_futura(self):

        self.crear_cita(
            estado=Cita.Estado.CONFIRMADA
        )

        self.client.force_login(self.admin)

        self.client.post(
            self.url(
                "eliminar_paciente",
                self.paciente,
            )
        )

        self.paciente.refresh_from_db()

        self.assertTrue(
            self.paciente.activo
        )

    # 51
    def test_no_desactiva_con_consulta_en_proceso(self):

        self.crear_cita(
            fecha=(
                timezone.localdate()
                - timedelta(days=7)
            ),
            estado=Cita.Estado.EN_PROCESO,
        )

        self.client.force_login(self.admin)

        self.client.post(
            self.url(
                "eliminar_paciente",
                self.paciente,
            )
        )

        self.paciente.refresh_from_db()

        self.assertTrue(
            self.paciente.activo
        )

    # 52
    def test_desactiva_si_solo_hay_citas_canceladas(self):

        self.crear_cita(
            estado=Cita.Estado.CANCELADA
        )

        self.client.force_login(self.admin)

        self.client.post(
            self.url(
                "eliminar_paciente",
                self.paciente,
            )
        )

        self.paciente.refresh_from_db()

        self.assertFalse(
            self.paciente.activo
        )
