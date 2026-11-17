
"""
Agrupa los botones del encabezado en Consultas
sin modificar formularios, vistas ni rutas.
"""

from datetime import datetime
from pathlib import Path
import re
import shutil
import textwrap


RAIZ = Path(__file__).resolve().parent.parent
CARPETA = RAIZ / "templates" / "consultas"

COMPONENTE = (
    RAIZ
    / "templates"
    / "componentes"
    / "boton_volver_panel.html"
)

INCLUDE = (
    '{% include '
    '"componentes/boton_volver_panel.html" %}'
)

ARCHIVOS = {
    "detalle_consulta.html": "usuarios:redireccion_por_rol",
    "iniciar_consulta.html": "usuarios:redireccion_por_rol",
    "motivo_consulta.html": "consultas:detalle_consulta",
    "finalizar_consulta.html": "consultas:detalle_consulta",
}

PATRON_HEADER = re.compile(
    r"<header\b[^>]*>.*?</header>",
    re.I | re.S,
)

PATRON_GRUPO = re.compile(
    r'<div class="flex flex-wrap gap-3">'
    r'(?P<interior>.*?)</div>',
    re.S,
)

PATRON_ENLACE = re.compile(
    r"<a\b[^>]*>.*?</a>",
    re.I | re.S,
)


def corregir(html, archivo, ruta_esperada):

    cabeceras = list(
        PATRON_HEADER.finditer(html)
    )

    if len(cabeceras) != 1:
        raise ValueError(
            f"{archivo}: se esperaba un solo encabezado."
        )

    cabecera = cabeceras[0]
    bloque = cabecera.group(0)

    # Evitar duplicar botones ya actualizados.
    if INCLUDE in html:

        if (
            html.count(INCLUDE) == 1
            and INCLUDE in bloque
            and '<nav aria-label="Navegación de consultas"'
            in bloque
        ):
            return html, False

        raise ValueError(
            f"{archivo}: botón duplicado "
            "o fuera del encabezado."
        )

    grupos = list(
        PATRON_GRUPO.finditer(bloque)
    )

    if len(grupos) != 1:
        raise ValueError(
            f"{archivo}: contenedor de "
            "botones inesperado."
        )

    grupo = grupos[0]
    interior = grupo.group("interior")

    enlaces = list(
        PATRON_ENLACE.finditer(interior)
    )

    if len(enlaces) != 2:
        raise ValueError(
            f"{archivo}: se esperaban "
            "dos enlaces superiores."
        )

    if PATRON_ENLACE.sub("", interior).strip():
        raise ValueError(
            f"{archivo}: el grupo contiene "
            "elementos desconocidos."
        )

    enlaces_html = [
        enlace.group(0)
        for enlace in enlaces
    ]

    if (
        "{% url 'usuarios:perfil' %}"
        not in enlaces_html[0]
    ):
        raise ValueError(
            f"{archivo}: no se encontró Mi perfil."
        )

    ruta_django = (
        "{% url '"
        + ruta_esperada
        + "'"
    )

    if ruta_django not in enlaces_html[1]:
        raise ValueError(
            f"{archivo}: el enlace de regreso "
            "es distinto al esperado."
        )

    # Siempre conservar Mi perfil.
    conservar = [
        enlaces_html[0]
    ]

    # Conservar Volver a consulta en
    # Valoración y Finalizar.
    if ruta_esperada != "usuarios:redireccion_por_rol":
        conservar.append(
            enlaces_html[1]
        )

    # Crear un único grupo de navegación
    # alineado al extremo derecho.
    navegacion = (
        '<nav aria-label="Navegación de consultas" '
        'class="ml-auto flex flex-wrap '
        'items-center justify-end gap-3">\n'
    )

    for enlace in conservar:

        navegacion += textwrap.indent(
            textwrap.dedent(enlace).strip(),
            " " * 16,
        )

        navegacion += "\n\n"

    navegacion += (
        " " * 16
        + INCLUDE
        + "\n"
        + " " * 12
        + "</nav>"
    )

    bloque_modificado = (
        bloque[:grupo.start()]
        + navegacion
        + bloque[grupo.end():]
    )

    actualizado = (
        html[:cabecera.start()]
        + bloque_modificado
        + html[cabecera.end():]
    )

    if actualizado.count(INCLUDE) != 1:
        raise ValueError(
            f"{archivo}: no se pudo verificar "
            "el botón estándar."
        )

    return actualizado, True


def main():

    if not COMPONENTE.is_file():
        raise SystemExit(
            "Falta templates/componentes/"
            "boton_volver_panel.html"
        )

    cambios = {}

    # Validar las cuatro plantillas
    # antes de modificar archivos.
    try:

        for nombre, ruta_esperada in ARCHIVOS.items():

            ruta = CARPETA / nombre

            original = ruta.read_text(
                encoding="utf-8-sig"
            )

            nuevo, cambiado = corregir(
                original,
                nombre,
                ruta_esperada,
            )

            if cambiado:
                cambios[ruta] = nuevo
            else:
                print(
                    "Ya actualizado:",
                    nombre,
                )

    except (OSError, ValueError) as error:
        raise SystemExit(
            f"Sin modificar archivos: {error}"
        )

    if not cambios:
        print(
            "Las cuatro plantillas ya tienen "
            "los botones alineados."
        )
        return

    # Crear respaldo fuera del repositorio.
    respaldo = (
        RAIZ.parent
        / (
            "respaldo_navegacion_consultas_"
            + datetime.now().strftime(
                "%Y%m%d_%H%M%S_%f"
            )
        )
    )

    respaldo.mkdir(
        parents=True,
        exist_ok=False,
    )

    # Respaldar originales.
    for ruta in cambios:
        shutil.copy2(
            ruta,
            respaldo / ruta.name,
        )

    # Aplicar actualizaciones.
    for ruta, nuevo in cambios.items():

        ruta.write_text(
            nuevo,
            encoding="utf-8",
        )

        print(
            "Actualizado:",
            ruta.relative_to(RAIZ),
        )

    print()
    print("Respaldo:", respaldo)
    print(
        "Navegación de Consultas actualizada."
    )


if __name__ == "__main__":
    main()
