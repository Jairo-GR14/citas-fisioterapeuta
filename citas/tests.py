
from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from fisioterapeutas.models import Fisioterapeuta, HorarioDisponible
from pacientes.models import Paciente
from precios.models import Servicio
from usuarios.models import PerfilUsuario

from .forms import CitaForm
from .models import Cita, MotivoConsulta


# =========================================================
# DATOS DE PRUEBA COMPARTIDOS
# =========================================================

class DatosCitas(TestCase):

    @classmethod
    def setUpTestData(cls):
        Usuario = get_user_model()

        def crear_usuario(nombre, rol):
            usuario = Usuario.objects.create_user(
                username=nombre,
                password="Prueba12345!",
            )

            perfil = PerfilUsuario.objects.create(
                usuario=usuario,
                rol=rol,
            )

            return usuario, perfil

        cls.admin, cls.perfil_admin = crear_usuario(
            "admin_citas",
            PerfilUsuario.Rol.ADMINISTRADOR,
        )

        cls.recepcionista, _ = crear_usuario(
            "recepcion_citas",
            PerfilUsuario.Rol.RECEPCIONISTA,
        )

        cls.usuario_paciente, perfil_paciente = crear_usuario(
            "paciente_citas",
            PerfilUsuario.Rol.PACIENTE,
        )

        cls.paciente = Paciente.objects.create(
            usuario=perfil_paciente,
        )

        cls.otro_usuario_paciente, otro_perfil = crear_usuario(
            "otro_paciente_citas",
            PerfilUsuario.Rol.PACIENTE,
        )

        cls.otro_paciente = Paciente.objects.create(
            usuario=otro_perfil,
        )

        cls.usuario_fisio, perfil_fisio = crear_usuario(
            "fisio_citas",
            PerfilUsuario.Rol.FISIOTERAPEUTA,
        )

        cls.fisio = Fisioterapeuta.objects.create(
            usuario=perfil_fisio,
        )

        cls.otro_usuario_fisio, otro_perfil_fisio = crear_usuario(
            "otro_fisio_citas",
            PerfilUsuario.Rol.FISIOTERAPEUTA,
        )

        cls.otro_fisio = Fisioterapeuta.objects.create(
            usuario=otro_perfil_fisio,
        )

        cls.servicio = Servicio.objects.create(
            nombre="Valoración de prueba",
            precio_base=Decimal("400.00"),
        )

        cls.otro_servicio = Servicio.objects.create(
            nombre="Terapia de prueba",
            precio_base=Decimal("250.00"),
        )

        cls.motivo = MotivoConsulta.objects.create(
            nombre="Motivo de prueba de citas",
        )

        cls.fecha_futura = (
            timezone.localdate() + timedelta(days=7)
        )

        cls.fecha_pasada = (
            timezone.localdate() - timedelta(days=7)
        )

        # Horario de 09:00 a 13:00 para ambos fisios.
        for fisio in (cls.fisio, cls.otro_fisio):
            HorarioDisponible.objects.create(
                fisioterapeuta=fisio,
                dia_semana=cls.fecha_futura.isoweekday(),
                hora_inicio=time(9, 0),
                hora_fin=time(13, 0),
                activo=True,
            )

    def datos_cita(self, **cambios):
        datos = {
            "paciente": str(self.paciente.pk),
            "fisioterapeuta": str(self.fisio.pk),
            "servicio": str(self.servicio.pk),
            "motivo": str(self.motivo.pk),
            "fecha": self.fecha_futura.isoformat(),
            "hora": "10:00",
            "observaciones": "Prueba automatizada",
        }

        datos.update(cambios)

        return datos

    def crear_cita(self, **cambios):
        datos = {
            "paciente": self.paciente,
            "fisioterapeuta": self.fisio,
            "servicio": self.servicio,
            "motivo": self.motivo,
            "fecha": self.fecha_futura,
            "hora": time(10, 0),
            "estado": Cita.Estado.PROGRAMADA,
            "costo_estimado": Decimal("400.00"),
        }

        datos.update(cambios)

        return Cita.objects.create(**datos)


# =========================================================
# PRUEBAS DEL FORMULARIO
# =========================================================

class CitaFormularioTests(DatosCitas):

    def test_reserva_valida(self):
        formulario = CitaForm(
            data=self.datos_cita()
        )

        self.assertTrue(
            formulario.is_valid(),
            formulario.errors,
        )

    def test_rechaza_fecha_pasada(self):
        formulario = CitaForm(
            data=self.datos_cita(
                fecha=self.fecha_pasada.isoformat()
            )
        )

        self.assertFalse(formulario.is_valid())
        self.assertTrue(
            formulario.non_field_errors()
        )

    def test_rechaza_hora_fuera_de_jornada(self):
        formulario = CitaForm(
            data=self.datos_cita(hora="14:00")
        )

        self.assertFalse(formulario.is_valid())

    def test_rechaza_hora_desalineada(self):
        formulario = CitaForm(
            data=self.datos_cita(hora="09:30")
        )

        self.assertFalse(formulario.is_valid())

    def test_rechaza_horario_ocupado(self):
        self.crear_cita()

        formulario = CitaForm(
            data=self.datos_cita()
        )

        self.assertFalse(formulario.is_valid())

    def test_horario_cancelado_vuelve_a_estar_disponible(self):
        self.crear_cita(
            estado=Cita.Estado.CANCELADA
        )

        formulario = CitaForm(
            data=self.datos_cita()
        )

        self.assertTrue(
            formulario.is_valid(),
            formulario.errors,
        )


# =========================================================
# PRUEBAS DE VISTAS Y PERMISOS
# =========================================================

class CitaVistasTests(DatosCitas):

    def setUp(self):
        self.client.force_login(self.admin)

    # =====================================================
    # AGENDA
    # =====================================================

    def test_admin_ve_todas_las_citas_en_agenda(self):
        self.crear_cita()

        self.crear_cita(
            paciente=self.otro_paciente,
            hora=time(11, 0),
        )

        respuesta = self.client.get(
            reverse("citas:agenda")
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            len(respuesta.context["citas"]),
            2,
        )

    def test_paciente_solo_ve_sus_citas(self):
        propia = self.crear_cita()

        ajena = self.crear_cita(
            paciente=self.otro_paciente,
            hora=time(11, 0),
        )

        self.client.force_login(
            self.usuario_paciente
        )

        respuesta = self.client.get(
            reverse("citas:agenda")
        )

        ids = [
            cita.pk
            for cita in respuesta.context["citas"]
        ]

        self.assertIn(propia.pk, ids)
        self.assertNotIn(ajena.pk, ids)

    def test_fisioterapeuta_solo_ve_citas_asignadas(self):
        propia = self.crear_cita()

        ajena = self.crear_cita(
            fisioterapeuta=self.otro_fisio
        )

        self.client.force_login(
            self.usuario_fisio
        )

        respuesta = self.client.get(
            reverse("citas:agenda")
        )

        ids = [
            cita.pk
            for cita in respuesta.context["citas"]
        ]

        self.assertIn(propia.pk, ids)
        self.assertNotIn(ajena.pk, ids)

    def test_mis_citas_muestra_proxima_cita(self):
        cita = self.crear_cita()

        self.client.force_login(
            self.usuario_paciente
        )

        respuesta = self.client.get(
            reverse("citas:mis_citas")
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            respuesta.context["proxima_cita"].pk,
            cita.pk,
        )

    def test_paciente_no_ve_detalle_ajeno(self):
        ajena = self.crear_cita(
            paciente=self.otro_paciente
        )

        self.client.force_login(
            self.usuario_paciente
        )

        respuesta = self.client.get(
            reverse(
                "citas:detalle_cita",
                args=[ajena.pk],
            )
        )

        self.assertEqual(respuesta.status_code, 404)

    # =====================================================
    # AGENDAR CITA
    # =====================================================

    def test_paciente_agenda_solo_para_si_mismo(self):
        self.client.force_login(
            self.usuario_paciente
        )

        respuesta = self.client.post(
            reverse("citas:agendar_cita"),
            self.datos_cita(
                paciente=str(self.otro_paciente.pk)
            ),
        )

        self.assertEqual(respuesta.status_code, 302)

        cita = Cita.objects.get()

        self.assertEqual(
            cita.paciente_id,
            self.paciente.pk,
        )

        self.assertEqual(
            cita.estado,
            Cita.Estado.PROGRAMADA,
        )

        self.assertEqual(
            cita.costo_estimado,
            Decimal("400.00"),
        )

    def test_recepcionista_puede_agendar(self):
        self.client.force_login(
            self.recepcionista
        )

        respuesta = self.client.post(
            reverse("citas:agendar_cita"),
            self.datos_cita(),
        )

        self.assertEqual(respuesta.status_code, 302)

        self.assertEqual(
            Cita.objects.count(),
            1,
        )

    def test_vista_no_reserva_horario_ocupado(self):
        self.crear_cita()

        respuesta = self.client.post(
            reverse("citas:agendar_cita"),
            self.datos_cita(),
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            Cita.objects.count(),
            1,
        )

    # =====================================================
    # EDITAR CITA
    # =====================================================

    def test_edicion_de_confirmada_reprograma(self):
        cita = self.crear_cita(
            estado=Cita.Estado.CONFIRMADA
        )

        respuesta = self.client.post(
            reverse(
                "citas:editar_cita",
                args=[cita.pk],
            ),
            self.datos_cita(hora="11:00"),
        )

        self.assertEqual(respuesta.status_code, 302)

        cita.refresh_from_db()

        self.assertEqual(cita.hora, time(11, 0))

        self.assertEqual(
            cita.estado,
            Cita.Estado.PROGRAMADA,
        )

    def test_cambio_servicio_actualiza_costo_estimado(self):
        cita = self.crear_cita(
            estado=Cita.Estado.CONFIRMADA
        )

        respuesta = self.client.post(
            reverse(
                "citas:editar_cita",
                args=[cita.pk],
            ),
            self.datos_cita(
                servicio=str(self.otro_servicio.pk)
            ),
        )

        self.assertEqual(respuesta.status_code, 302)

        cita.refresh_from_db()

        self.assertEqual(
            cita.costo_estimado,
            Decimal("250.00"),
        )

        self.assertEqual(
            cita.estado,
            Cita.Estado.PROGRAMADA,
        )

    def test_paciente_no_edita_cita_ajena(self):
        ajena = self.crear_cita(
            paciente=self.otro_paciente
        )

        self.client.force_login(
            self.usuario_paciente
        )

        respuesta = self.client.get(
            reverse(
                "citas:editar_cita",
                args=[ajena.pk],
            )
        )

        self.assertEqual(respuesta.status_code, 404)

    def test_no_edita_cita_finalizada(self):
        cita = self.crear_cita(
            estado=Cita.Estado.FINALIZADA
        )

        respuesta = self.client.post(
            reverse(
                "citas:editar_cita",
                args=[cita.pk],
            ),
            self.datos_cita(hora="11:00"),
        )

        self.assertEqual(respuesta.status_code, 302)

        cita.refresh_from_db()

        self.assertEqual(
            cita.hora,
            time(10, 0),
        )

    # =====================================================
    # CANCELAR CITA
    # =====================================================

    def test_cancelacion_guarda_motivo(self):
        cita = self.crear_cita()

        respuesta = self.client.post(
            reverse(
                "citas:cancelar_cita",
                args=[cita.pk],
            ),
            {
                "motivo_cancelacion": "cambio_horario",
                "observaciones": "Otro compromiso",
            },
        )

        self.assertEqual(respuesta.status_code, 302)

        cita.refresh_from_db()

        self.assertEqual(
            cita.estado,
            Cita.Estado.CANCELADA,
        )

        self.assertIn(
            "Cambio de horario",
            cita.motivo_cancelacion,
        )

        self.assertIn(
            "Otro compromiso",
            cita.motivo_cancelacion,
        )

    def test_cancelacion_rechaza_motivo_invalido(self):
        cita = self.crear_cita()

        respuesta = self.client.post(
            reverse(
                "citas:cancelar_cita",
                args=[cita.pk],
            ),
            {
                "motivo_cancelacion": "inventado",
            },
        )

        self.assertEqual(respuesta.status_code, 200)

        cita.refresh_from_db()

        self.assertEqual(
            cita.estado,
            Cita.Estado.PROGRAMADA,
        )

    def test_no_cancela_cita_finalizada(self):
        cita = self.crear_cita(
            estado=Cita.Estado.FINALIZADA
        )

        respuesta = self.client.post(
            reverse(
                "citas:cancelar_cita",
                args=[cita.pk],
            ),
            {
                "motivo_cancelacion": "otro",
            },
        )

        self.assertEqual(respuesta.status_code, 302)

        cita.refresh_from_db()

        self.assertEqual(
            cita.estado,
            Cita.Estado.FINALIZADA,
        )

    # =====================================================
    # CONFIRMAR CITA
    # =====================================================

    def test_administrador_confirma_cita_futura(self):
        cita = self.crear_cita()

        respuesta = self.client.post(
            reverse("citas:confirmar_cita"),
            {
                "cita_id": str(cita.pk),
            },
        )

        self.assertEqual(respuesta.status_code, 302)

        cita.refresh_from_db()

        self.assertEqual(
            cita.estado,
            Cita.Estado.CONFIRMADA,
        )

    def test_no_confirma_cita_pasada(self):
        cita = self.crear_cita(
            fecha=self.fecha_pasada
        )

        respuesta = self.client.post(
            reverse("citas:confirmar_cita"),
            {
                "cita_id": str(cita.pk),
            },
        )

        self.assertEqual(respuesta.status_code, 302)

        cita.refresh_from_db()

        self.assertEqual(
            cita.estado,
            Cita.Estado.PROGRAMADA,
        )

    def test_no_confirma_cita_ya_confirmada(self):
        cita = self.crear_cita(
            estado=Cita.Estado.CONFIRMADA
        )

        self.client.post(
            reverse("citas:confirmar_cita"),
            {
                "cita_id": str(cita.pk),
            },
        )

        cita.refresh_from_db()

        self.assertEqual(
            cita.estado,
            Cita.Estado.CONFIRMADA,
        )

    def test_fisioterapeuta_no_puede_confirmar(self):
        cita = self.crear_cita()

        self.client.force_login(
            self.usuario_fisio
        )

        respuesta = self.client.post(
            reverse("citas:confirmar_cita"),
            {
                "cita_id": str(cita.pk),
            },
        )

        self.assertEqual(respuesta.status_code, 403)

        cita.refresh_from_db()

        self.assertEqual(
            cita.estado,
            Cita.Estado.PROGRAMADA,
        )

    # =====================================================
    # HORARIOS DISPONIBLES
    # =====================================================

    def test_horarios_ofrecen_bloques_de_60_minutos(self):
        respuesta = self.client.get(
            reverse("citas:horarios_disponibles"),
            {
                "fisioterapeuta": str(self.fisio.pk),
                "fecha": self.fecha_futura.isoformat(),
            },
        )

        self.assertEqual(respuesta.status_code, 200)

        horarios = {
            item["hora"]: item["disponible"]
            for item in respuesta.context["horarios"]
        }

        self.assertEqual(
            set(horarios),
            {
                "09:00",
                "10:00",
                "11:00",
                "12:00",
            },
        )

        self.assertTrue(all(horarios.values()))

    def test_horario_ocupado_se_muestra_no_disponible(self):
        self.crear_cita()

        respuesta = self.client.get(
            reverse("citas:horarios_disponibles"),
            {
                "fisioterapeuta": str(self.fisio.pk),
                "fecha": self.fecha_futura.isoformat(),
            },
        )

        horarios = {
            item["hora"]: item["disponible"]
            for item in respuesta.context["horarios"]
        }

        self.assertFalse(horarios["10:00"])
        self.assertTrue(horarios["11:00"])

    def test_consultar_horarios_pasados_muestra_error(self):
        respuesta = self.client.get(
            reverse("citas:horarios_disponibles"),
            {
                "fisioterapeuta": str(self.fisio.pk),
                "fecha": self.fecha_pasada.isoformat(),
            },
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertTrue(
            respuesta.context["error"]
        )

    # =====================================================
    # SEGURIDAD
    # =====================================================

    def test_sin_sesion_redirige_al_login(self):
        self.client.logout()

        respuesta = self.client.get(
            reverse("citas:agenda")
        )

        self.assertEqual(respuesta.status_code, 302)

    def test_superusuario_con_perfil_inactivo_no_accede(self):
        self.admin.is_superuser = True

        self.admin.save(
            update_fields=["is_superuser"]
        )

        self.perfil_admin.activo = False

        self.perfil_admin.save(
            update_fields=["activo"]
        )

        respuesta = self.client.get(
            reverse("citas:agenda")
        )

        self.assertEqual(respuesta.status_code, 403)
