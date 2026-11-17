# Entrega de Jairo - Sistema de Fisioterapia

## Estado del proyecto

Rama de trabajo: main

Verificaciones realizadas:
- Django check: sin errores.
- Migraciones: sin cambios pendientes.
- Pruebas automatizadas: 483 aprobadas.
- Tratamientos: 5 verificaciones visuales correctas.
- Importacion de datos de prueba: 56 registros correctos.

## Trabajo realizado

Se incluyen cambios en:
- Tratamientos y sus interfaces.
- Agenda, calendario y disponibilidad de citas.
- Precios y duracion de servicios.
- Navegacion y componentes reutilizables.
- Formularios, modelos, migraciones y pruebas.

## Base de datos

Archivo: datos_demo.json

Contiene 56 registros de prueba, incluyendo:
- 5 usuarios
- 2 pacientes
- 5 citas
- 1 consulta
- 1 fisioterapeuta
- 2 servicios
- Otros registros relacionados

No contiene tratamientos registrados como datos de ejemplo.

Las contrasenas de los usuarios estan inhabilitadas.

## Como recuperar los datos

En una instalacion nueva, despues de configurar
el entorno virtual y las dependencias:

1. Configurar el archivo .env correspondiente.
2. Ejecutar: python manage.py migrate
3. Ejecutar: python manage.py loaddata datos_demo.json
4. Ejecutar: python manage.py runserver

Para asignar una contrasena a un usuario:

python manage.py changepassword NOMBRE_USUARIO

IMPORTANTE:
Importar los datos en una base nueva.
No reemplazar la base de datos existente sin respaldo.

## Indicaciones para el equipo

Antes de comenzar a trabajar:
git pull --ff-only origin main

Antes de subir cambios:
git status
git fetch origin

No utilizar git push --force.

Coordinar modificaciones en archivos compartidos
para evitar conflictos.

## Estado de entrega

Los cambios indicados fueron verificados mediante
las pruebas mencionadas. El equipo puede continuar
con el desarrollo desde este commit.
