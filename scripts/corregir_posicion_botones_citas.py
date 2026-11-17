
"""
Corrige la posición de los botones superiores
en las pantallas pendientes de Citas.

Agrupa los botones a la derecha sin cambiar
sus enlaces, formularios ni funcionalidades.
"""

from datetime import datetime
from pathlib import Path
import re
import shutil


RAIZ = Path(__file__).resolve().parent.parent
CARPETA = RAIZ / "templates" / "citas"

INCLUDE = (
    '{% include '
    '"componentes/boton_volver_panel.html" %}'
)

ARCHIVOS = {
    "editar_cita.html": (
        "{% url 'citas:detalle_cita' cita.pk %}"
    ),
    "cita_emergencia.html": (
        "{% url 'citas:agendar_cita' %}"
    ),
    "horarios_disponibles.html": (
        "{% url 'citas:agendar_cita' %}"
    ),
}

SOLO_VERIFICAR = (
    "cancelar_cita.html",
    "confirmar_cita.html",
)

ENCABEZADO = re.compile(
    r"<header\b[^>]*>.*?</header>",
    re.I | re.S,
)

ENLACE = re.compile(
    r"<a\b[^>]*>.*?</a>",
    re.I | re.S,
)

NAV = re.compile(
    r"<nav\b[^>]*>.*?</nav>",
    re.I | re.S,
)


def corregir(texto, nombre, ruta_esperada):

    if texto.count(INCLUDE) != 1:
        raise ValueError(
            f"{nombre}: debe existir exactamente "
            "un botón Volver al panel."
        )

    encontrados = list(
        ENCABEZADO.finditer(texto)
    )

    if len(encontrados) != 1:
        raise ValueError(
            f"{nombre}: encabezado inesperado."
        )

    marca = encontrados[0]
    header = marca.group(0)

    enlaces = list(
        ENLACE.finditer(header)
    )

    if (
        len(enlaces) != 1
        or f'href="{ruta_esperada}"'
        not in enlaces[0].group(0)
    ):
        raise ValueError(
            f"{nombre}: enlace de regreso "
            "diferente al esperado."
        )

    if INCLUDE not in header:
        raise ValueError(
            f"{nombre}: Volver al panel "
            "está fuera del encabezado."
        )

    # Si los botones ya están agrupados,
    # no se modifica la plantilla.
    if "<nav" in header.lower():

        for nav in NAV.finditer(header):

            if (
                INCLUDE in nav.group(0)
                and enlaces[0].group(0)
                in nav.group(0)
            ):
                return texto, False

        raise ValueError(
            f"{nombre}: navegación "
            "diferente a la esperada."
        )

    ancla = enlaces[0]
    resto = header[ancla.end():]

    posicion = resto.find(INCLUDE)

    if (
        posicion < 0
        or resto[:posicion].strip()
    ):
        raise ValueError(
            f"{nombre}: los botones "
            "no están consecutivos."
        )

    # Conservar el botón original
    # y agruparlo con Volver al panel.
    grupo = (
        '<nav aria-label="Navegación de citas"\n'
        '     class="ml-auto flex flex-wrap '
        'items-center justify-end gap-3">\n'
        + ancla.group(0)
        + "\n"
        + INCLUDE
        + "\n</nav>"
    )

    header = (
        header[:ancla.start()]
        + grupo
        + resto[posicion + len(INCLUDE):]
    )

    # Ajustar el contenedor exterior
    # para pantallas pequeñas.
    contenedor = re.search(
        r'<div\s+class="([^"]*\bmx-auto flex\b[^"]*)">',
        header,
    )

    if (
        contenedor is None
        or "justify-between"
        not in contenedor.group(1)
    ):
        raise ValueError(
            f"{nombre}: estructura de "
            "encabezado inesperada."
        )

    clases = contenedor.group(1)

    if "flex-wrap" not in clases:
        clases += " flex-wrap"

    if not re.search(r"\bgap-\d+\b", clases):
        clases += " gap-4"

    header = header.replace(
        contenedor.group(0),
        f'<div class="{clases}">',
        1,
    )

    nuevo = (
        texto[:marca.start()]
        + header
        + texto[marca.end():]
    )

    if nuevo.count(INCLUDE) != 1:
        raise ValueError(
            f"{nombre}: se duplicó el botón."
        )

    return nuevo, True


def main():

    componente = (
        RAIZ
        / "templates"
        / "componentes"
        / "boton_volver_panel.html"
    )

    if not componente.is_file():
        raise SystemExit(
            "Falta el componente "
            "boton_volver_panel.html."
        )

    cambios = {}

    # Revisar todo antes de modificar.
    try:

        for nombre, ruta in ARCHIVOS.items():

            archivo = CARPETA / nombre

            original = archivo.read_text(
                encoding="utf-8-sig"
            )

            nuevo, cambiado = corregir(
                original,
                nombre,
                ruta,
            )

            if cambiado:
                cambios[archivo] = nuevo
            else:
                print("Ya alineado:", nombre)

        # Confirmar y Cancelar ya
        # tienen navegación superior.
        for nombre in SOLO_VERIFICAR:

            archivo = CARPETA / nombre

            original = archivo.read_text(
                encoding="utf-8-sig"
            )

            correcto = (
                original.count(INCLUDE) == 1
                and any(
                    INCLUDE in nav.group(0)
                    for nav in NAV.finditer(original)
                )
            )

            if not correcto:
                raise ValueError(
                    f"{nombre}: revisar "
                    "navegación superior."
                )

            print(
                "Navegación encontrada:",
                nombre,
            )

    except (OSError, ValueError) as error:
        raise SystemExit(
            f"Sin cambios: {error}"
        )

    if not cambios:
        print(
            "No hay archivos pendientes."
        )
        return

    # Respaldar los archivos originales.
    respaldo = (
        RAIZ.parent
        / (
            "respaldo_posicion_citas_"
            + datetime.now().strftime(
                "%Y%m%d_%H%M%S_%f"
            )
        )
    )

    respaldo.mkdir(
        parents=True,
        exist_ok=False,
    )

    for archivo in cambios:

        shutil.copy2(
            archivo,
            respaldo / archivo.name,
        )

    # Aplicar los cambios.
    for archivo, contenido in cambios.items():

        archivo.write_text(
            contenido,
            encoding="utf-8",
        )

        print(
            "Actualizado:",
            archivo.relative_to(RAIZ),
        )

    print()
    print("Respaldo:", respaldo)
    print("Botones agrupados correctamente.")


if __name__ == "__main__":
    main()
