
from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from citas.models import Cita, MotivoConsulta
from fisioterapeutas.models import Fisioterapeuta
from pacientes.models import Paciente
from precios.models import Servicio
from usuarios.models import PerfilUsuario

from .models import Notificacion
from .servicios import notificar_evento_cita


# =========================================================
# DATOS DE PRUEBA
# =========================================================

class DatosNotificaciones(TestCase):

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

        # PACIENTE
        cls.usuario_paciente, cls.perfil_paciente = (
            crear_usuario(
                "paciente_notificaciones",
                PerfilUsuario.Rol.PACIENTE,
            )
        )

        cls.paciente = Paciente.objects.create(
            usuario=cls.perfil_paciente,
        )

        # FISIOTERAPEUTA
        cls.usuario_fisio, cls.perfil_fisio = (
            crear_usuario(
                "fisio_notificaciones",
                PerfilUsuario.Rol.FISIOTERAPEUTA,
            )
        )

        cls.fisio = Fisioterapeuta.objects.create(
            usuario=cls.perfil_fisio,
        )

        # SEGUNDO FISIOTERAPEUTA
        cls.usuario_otro_fisio, cls.perfil_otro_fisio = (
            crear_usuario(
                "otro_fisio_notificaciones",
                PerfilUsuario.Rol.FISIOTERAPEUTA,
            )
        )

        cls.otro_fisio = Fisioterapeuta.objects.create(
            usuario=cls.perfil_otro_fisio,
        )

        # OTRO PACIENTE
        cls.usuario_ajeno, cls.perfil_ajeno = (
            crear_usuario(
                "otro_paciente_notificaciones",
                PerfilUsuario.Rol.PACIENTE,
            )
        )

        cls.otro_paciente = Paciente.objects.create(
            usuario=cls.perfil_ajeno,
        )

        # SERVICIOS
        cls.servicio = Servicio.objects.create(
            nombre="Servicio para notificaciones",
            precio_base=Decimal("400.00"),
        )

        cls.otro_servicio = Servicio.objects.create(
            nombre="Terapia para notificaciones",
            precio_base=Decimal("250.00"),
        )

        # MOTIVO
        cls.motivo = MotivoConsulta.objects.create(
            nombre="Motivo de prueba de notificaciones",
        )

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

    def crear_notificacion(
        self,
        perfil=None,
        titulo="Aviso de prueba",
        leida=False,
        tipo=Notificacion.Tipo.SISTEMA,
    ):

        if perfil is None:
            perfil = self.perfil_paciente

        return Notificacion.objects.create(
            usuario=perfil,
            tipo=tipo,
            titulo=titulo,
            mensaje="Contenido de prueba.",
            leida=leida,
        )


# =========================================================
# PRUEBAS DE VISTAS Y PERMISOS
# =========================================================

class NotificacionesVistasTests(DatosNotificaciones):

    def setUp(self):

        self.client.force_login(
            self.usuario_paciente
        )

    # -----------------------------------------------------
    # 1. LISTAR SOLO NOTIFICACIONES PROPIAS
    # -----------------------------------------------------

    def test_lista_muestra_solo_notificaciones_propias(self):

        propia = self.crear_notificacion()

        ajena = self.crear_notificacion(
            perfil=self.perfil_ajeno,
        )

        respuesta = self.client.get(
            reverse("notificaciones:lista")
        )

        self.assertEqual(respuesta.status_code, 200)

        resultados = list(
            respuesta.context["notificaciones"]
        )

        self.assertIn(propia, resultados)
        self.assertNotIn(ajena, resultados)

    # -----------------------------------------------------
    # 2. CONTADOR DE NOTIFICACIONES SIN LEER
    # -----------------------------------------------------

    def test_contador_sin_leer_es_correcto(self):

        self.crear_notificacion(
            titulo="Pendiente 1",
        )

        self.crear_notificacion(
            titulo="Pendiente 2",
        )

        self.crear_notificacion(
            titulo="Ya leída",
            leida=True,
        )

        respuesta = self.client.get(
            reverse("notificaciones:lista")
        )

        self.assertEqual(
            respuesta.context["sin_leer"],
            2,
        )

    # -----------------------------------------------------
    # 3. LIMITAR LISTADO A 100 NOTIFICACIONES
    # -----------------------------------------------------

    def test_listado_muestra_maximo_100(self):

        Notificacion.objects.bulk_create([
            Notificacion(
                usuario=self.perfil_paciente,
                tipo=Notificacion.Tipo.SISTEMA,
                titulo=f"Aviso {numero}",
                mensaje="Mensaje de prueba.",
            )
            for numero in range(102)
        ])

        respuesta = self.client.get(
            reverse("notificaciones:lista")
        )

        self.assertEqual(
            len(respuesta.context["notificaciones"]),
            100,
        )

        self.assertEqual(
            respuesta.context["sin_leer"],
            102,
        )

    # -----------------------------------------------------
    # 4. VER DETALLE PROPIO
    # -----------------------------------------------------

    def test_paciente_ve_detalle_propio(self):

        notificacion = self.crear_notificacion()

        respuesta = self.client.get(
            reverse(
                "notificaciones:detalle",
                args=[notificacion.pk],
            )
        )

        self.assertEqual(respuesta.status_code, 200)

        self.assertEqual(
            respuesta.context["notificacion"].pk,
            notificacion.pk,
        )

    # -----------------------------------------------------
    # 5. NO VER DETALLE AJENO
    # -----------------------------------------------------

    def test_paciente_no_ve_detalle_ajeno(self):

        ajena = self.crear_notificacion(
            perfil=self.perfil_ajeno,
        )

        respuesta = self.client.get(
            reverse(
                "notificaciones:detalle",
                args=[ajena.pk],
            )
        )

        self.assertEqual(respuesta.status_code, 404)

    # -----------------------------------------------------
    # 6. CONSULTAR DETALLE NO MARCA COMO LEÍDA
    # -----------------------------------------------------

    def test_detalle_no_cambia_estado_lectura(self):

        notificacion = self.crear_notificacion()

        self.client.get(
            reverse(
                "notificaciones:detalle",
                args=[notificacion.pk],
            )
        )

        notificacion.refresh_from_db()

        self.assertFalse(notificacion.leida)
        self.assertIsNone(
            notificacion.fecha_lectura
        )

    # -----------------------------------------------------
    # 7. MARCAR UNA NOTIFICACIÓN COMO LEÍDA
    # -----------------------------------------------------

    def test_marcar_leida_por_post(self):

        notificacion = self.crear_notificacion()

        respuesta = self.client.post(
            reverse(
                "notificaciones:marcar_leida",
                args=[notificacion.pk],
            )
        )

        self.assertEqual(respuesta.status_code, 302)

        notificacion.refresh_from_db()

        self.assertTrue(notificacion.leida)

        self.assertIsNotNone(
            notificacion.fecha_lectura
        )

    # -----------------------------------------------------
    # 8. NO MARCAR COMO LEÍDA MEDIANTE GET
    # -----------------------------------------------------

    def test_marcar_leida_rechaza_get(self):

        notificacion = self.crear_notificacion()

        respuesta = self.client.get(
            reverse(
                "notificaciones:marcar_leida",
                args=[notificacion.pk],
            )
        )

        self.assertEqual(respuesta.status_code, 405)

        notificacion.refresh_from_db()

        self.assertFalse(notificacion.leida)

    # -----------------------------------------------------
    # 9. NO MARCAR NOTIFICACIONES AJENAS
    # -----------------------------------------------------

    def test_no_puede_marcar_notificacion_ajena(self):

        ajena = self.crear_notificacion(
            perfil=self.perfil_ajeno,
        )

        respuesta = self.client.post(
            reverse(
                "notificaciones:marcar_leida",
                args=[ajena.pk],
            )
        )

        self.assertEqual(respuesta.status_code, 404)

        ajena.refresh_from_db()

        self.assertFalse(ajena.leida)

    # -----------------------------------------------------
    # 10. NO MODIFICAR FECHA DE LECTURA REPETIDA
    # -----------------------------------------------------

    def test_marcar_dos_veces_conserva_fecha(self):

        notificacion = self.crear_notificacion()

        url = reverse(
            "notificaciones:marcar_leida",
            args=[notificacion.pk],
        )

        self.client.post(url)

        notificacion.refresh_from_db()

        primera_fecha = notificacion.fecha_lectura

        self.client.post(url)

        notificacion.refresh_from_db()

        self.assertEqual(
            notificacion.fecha_lectura,
            primera_fecha,
        )

    # -----------------------------------------------------
    # 11. MARCAR TODAS LAS PROPIAS
    # -----------------------------------------------------

    def test_marcar_todas_solo_afecta_propias(self):

        propia_1 = self.crear_notificacion(
            titulo="Propia 1",
        )

        propia_2 = self.crear_notificacion(
            titulo="Propia 2",
        )

        ajena = self.crear_notificacion(
            perfil=self.perfil_ajeno,
            titulo="Ajena",
        )

        respuesta = self.client.post(
            reverse("notificaciones:marcar_todas")
        )

        self.assertEqual(respuesta.status_code, 302)

        propia_1.refresh_from_db()
        propia_2.refresh_from_db()
        ajena.refresh_from_db()

        self.assertTrue(propia_1.leida)
        self.assertTrue(propia_2.leida)
        self.assertFalse(ajena.leida)

        self.assertIsNotNone(
            propia_1.fecha_lectura
        )

        self.assertIsNotNone(
            propia_2.fecha_lectura
        )

    # -----------------------------------------------------
    # 12. MARCAR TODAS REQUIERE POST
    # -----------------------------------------------------

    def test_marcar_todas_rechaza_get(self):

        notificacion = self.crear_notificacion()

        respuesta = self.client.get(
            reverse("notificaciones:marcar_todas")
        )

        self.assertEqual(respuesta.status_code, 405)

        notificacion.refresh_from_db()

        self.assertFalse(notificacion.leida)

    # -----------------------------------------------------
    # 13. BLOQUEAR PERFIL INACTIVO
    # -----------------------------------------------------

    def test_perfil_inactivo_no_accede(self):

        self.perfil_paciente.activo = False

        self.perfil_paciente.save(
            update_fields=["activo"]
        )

        respuesta = self.client.get(
            reverse("notificaciones:lista")
        )

        self.assertEqual(respuesta.status_code, 403)

    # -----------------------------------------------------
    # 14. BLOQUEAR USUARIO SIN PERFIL
    # -----------------------------------------------------

    def test_usuario_sin_perfil_no_accede(self):

        Usuario = get_user_model()

        usuario = Usuario.objects.create_user(
            username="sin_perfil_notificaciones",
            password="Prueba12345!",
        )

        self.client.force_login(usuario)

        respuesta = self.client.get(
            reverse("notificaciones:lista")
        )

        self.assertEqual(respuesta.status_code, 403)

    # -----------------------------------------------------
    # 15. SIN SESIÓN SE REDIRIGE
    # -----------------------------------------------------

    def test_sin_sesion_redirige(self):

        self.client.logout()

        respuesta = self.client.get(
            reverse("notificaciones:lista")
        )

        self.assertEqual(respuesta.status_code, 302)

    # -----------------------------------------------------
    # 16. NOTIFICACIÓN INEXISTENTE
    # -----------------------------------------------------

    def test_notificacion_inexistente_devuelve_404(self):

        respuesta = self.client.get(
            reverse(
                "notificaciones:detalle",
                args=[999999],
            )
        )

        self.assertEqual(respuesta.status_code, 404)


# =========================================================
# PRUEBAS DE SEÑALES Y GENERACIÓN AUTOMÁTICA
# =========================================================

class NotificacionesSignalsTests(DatosNotificaciones):

    # -----------------------------------------------------
    # 17. NOTIFICAR CITA PROGRAMADA
    # -----------------------------------------------------

    def test_cita_programada_genero_dos_notificaciones(self):

        with self.captureOnCommitCallbacks(
            execute=True
        ) as callbacks:

            cita = self.crear_cita()

        self.assertEqual(len(callbacks), 1)

        notificaciones = Notificacion.objects.filter(
            tipo=Notificacion.Tipo.CITA,
            titulo="Nueva cita programada",
        )

        self.assertEqual(
            notificaciones.count(),
            2,
        )

        destinatarios = set(
            notificaciones.values_list(
                "usuario_id",
                flat=True,
            )
        )

        self.assertEqual(
            destinatarios,
            {
                self.perfil_paciente.pk,
                self.perfil_fisio.pk,
            },
        )

        self.assertIn(
            str(cita.pk),
            notificaciones.first().mensaje,
        )

    # -----------------------------------------------------
    # 18. NOTIFICAR CONFIRMACIÓN
    # -----------------------------------------------------

    def test_confirmacion_genera_notificaciones(self):

        cita = self.crear_cita()

        with self.captureOnCommitCallbacks(
            execute=True
        ):

            cita.estado = Cita.Estado.CONFIRMADA

            cita.save(
                update_fields=["estado"]
            )

        self.assertEqual(
            Notificacion.objects.filter(
                titulo="Cita confirmada"
            ).count(),
            2,
        )

    # -----------------------------------------------------
    # 19. NOTIFICAR CANCELACIÓN
    # -----------------------------------------------------

    def test_cancelacion_genera_notificaciones(self):

        cita = self.crear_cita()

        with self.captureOnCommitCallbacks(
            execute=True
        ):

            cita.estado = Cita.Estado.CANCELADA

            cita.save(
                update_fields=["estado"]
            )

        self.assertEqual(
            Notificacion.objects.filter(
                titulo="Cita cancelada"
            ).count(),
            2,
        )

    # -----------------------------------------------------
    # 20. NOTIFICAR INICIO DE CONSULTA
    # -----------------------------------------------------

    def test_inicio_consulta_genera_notificaciones(self):

        cita = self.crear_cita()

        with self.captureOnCommitCallbacks(
            execute=True
        ):

            cita.estado = Cita.Estado.EN_PROCESO

            cita.save(
                update_fields=["estado"]
            )

        self.assertEqual(
            Notificacion.objects.filter(
                titulo="Consulta iniciada"
            ).count(),
            2,
        )

    # -----------------------------------------------------
    # 21. NOTIFICAR FINALIZACIÓN
    # -----------------------------------------------------

    def test_finalizacion_genera_notificaciones(self):

        cita = self.crear_cita(
            estado=Cita.Estado.EN_PROCESO
        )

        with self.captureOnCommitCallbacks(
            execute=True
        ):

            cita.estado = Cita.Estado.FINALIZADA

            cita.save(
                update_fields=["estado"]
            )

        self.assertEqual(
            Notificacion.objects.filter(
                titulo="Consulta finalizada"
            ).count(),
            2,
        )

    # -----------------------------------------------------
    # 22. NOTIFICAR CAMBIO DE HORA
    # -----------------------------------------------------

    def test_cambio_hora_genera_notificaciones(self):

        cita = self.crear_cita()

        with self.captureOnCommitCallbacks(
            execute=True
        ):

            cita.hora = time(11, 0)

            cita.save(
                update_fields=["hora"]
            )

        self.assertEqual(
            Notificacion.objects.filter(
                titulo="Cita modificada"
            ).count(),
            2,
        )

    # -----------------------------------------------------
    # 23. NOTIFICAR CAMBIO DE FECHA
    # -----------------------------------------------------

    def test_cambio_fecha_genera_notificaciones(self):

        cita = self.crear_cita()

        with self.captureOnCommitCallbacks(
            execute=True
        ):

            cita.fecha += timedelta(days=1)

            cita.save(
                update_fields=["fecha"]
            )

        self.assertEqual(
            Notificacion.objects.filter(
                titulo="Cita modificada"
            ).count(),
            2,
        )

    # -----------------------------------------------------
    # 24. NOTIFICAR CAMBIO DE SERVICIO
    # -----------------------------------------------------

    def test_cambio_servicio_genera_notificaciones(self):

        cita = self.crear_cita()

        with self.captureOnCommitCallbacks(
            execute=True
        ):

            cita.servicio = self.otro_servicio

            cita.save(
                update_fields=["servicio"]
            )

        self.assertEqual(
            Notificacion.objects.filter(
                titulo="Cita modificada"
            ).count(),
            2,
        )

    # -----------------------------------------------------
    # 25. AVISAR AL FISIOTERAPEUTA ANTERIOR
    # -----------------------------------------------------

    def test_reasignacion_notifica_tres_destinatarios(self):

        cita = self.crear_cita()

        with self.captureOnCommitCallbacks(
            execute=True
        ):

            cita.fisioterapeuta = self.otro_fisio

            cita.save(
                update_fields=["fisioterapeuta"]
            )

        self.assertEqual(
            Notificacion.objects.count(),
            3,
        )

        self.assertTrue(
            Notificacion.objects.filter(
                usuario=self.perfil_paciente,
                titulo="Cita modificada",
            ).exists()
        )

        self.assertTrue(
            Notificacion.objects.filter(
                usuario=self.perfil_otro_fisio,
                titulo="Cita modificada",
            ).exists()
        )

        self.assertTrue(
            Notificacion.objects.filter(
                usuario=self.perfil_fisio,
                titulo="Cita reasignada",
            ).exists()
        )

    # -----------------------------------------------------
    # 26. NO NOTIFICAR CAMBIOS IRRELEVANTES
    # -----------------------------------------------------

    def test_cambio_observaciones_no_genera_notificacion(self):

        cita = self.crear_cita()

        with self.captureOnCommitCallbacks(
            execute=True
        ) as callbacks:

            cita.observaciones = "Nota administrativa."

            cita.save(
                update_fields=["observaciones"]
            )

        self.assertEqual(len(callbacks), 0)

        self.assertEqual(
            Notificacion.objects.count(),
            0,
        )

    # -----------------------------------------------------
    # 27. ESPERAR A CONFIRMAR TRANSACCIÓN
    # -----------------------------------------------------

    def test_notificaciones_se_programan_para_commit(self):

        with self.captureOnCommitCallbacks(
            execute=False
        ) as callbacks:

            self.crear_cita()

        self.assertEqual(len(callbacks), 1)

        self.assertEqual(
            Notificacion.objects.count(),
            0,
        )

    # -----------------------------------------------------
    # 28. NO NOTIFICAR SI SE REVIERTE TRANSACCIÓN
    # -----------------------------------------------------

    def test_rollback_descarta_notificacion(self):

        with self.captureOnCommitCallbacks(
            execute=True
        ) as callbacks:

            try:

                with transaction.atomic():

                    self.crear_cita()

                    raise ValueError(
                        "Simular error en la operación."
                    )

            except ValueError:
                pass

        self.assertEqual(len(callbacks), 0)

        self.assertEqual(
            Notificacion.objects.count(),
            0,
        )

        self.assertEqual(
            Cita.objects.count(),
            0,
        )

    # -----------------------------------------------------
    # 29. CANCELACIÓN ELIMINA RECORDATORIOS PENDIENTES
    # -----------------------------------------------------

    def test_cancelacion_elimina_recordatorios_pendientes(self):

        cita = self.crear_cita()

        titulo = (
            f"Recordatorio de la cita #{cita.pk}"
        )

        pendiente = self.crear_notificacion(
            titulo=titulo,
            tipo=Notificacion.Tipo.RECORDATORIO,
        )

        leido = self.crear_notificacion(
            titulo=titulo,
            tipo=Notificacion.Tipo.RECORDATORIO,
            leida=True,
        )

        otro = self.crear_notificacion(
            titulo="Recordatorio de otra cita",
            tipo=Notificacion.Tipo.RECORDATORIO,
        )

        with self.captureOnCommitCallbacks(
            execute=True
        ):

            cita.estado = Cita.Estado.CANCELADA

            cita.save(
                update_fields=["estado"]
            )

        self.assertFalse(
            Notificacion.objects.filter(
                pk=pendiente.pk
            ).exists()
        )

        self.assertTrue(
            Notificacion.objects.filter(
                pk=leido.pk
            ).exists()
        )

        self.assertTrue(
            Notificacion.objects.filter(
                pk=otro.pk
            ).exists()
        )

    # -----------------------------------------------------
    # 30. IGNORAR EVENTOS O CITAS DESCONOCIDOS
    # -----------------------------------------------------

    def test_servicio_ignora_eventos_invalidos(self):

        cita = self.crear_cita()

        notificar_evento_cita(
            cita.pk,
            "EVENTO_INEXISTENTE",
        )

        notificar_evento_cita(
            999999,
            "PROGRAMADA",
        )

        self.assertEqual(
            Notificacion.objects.count(),
            0,
        )
