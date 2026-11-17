
"""
Unifica los botones de navegación de Administración.

No modifica vistas, modelos, rutas ni formularios.
"""

from datetime import datetime
from pathlib import Path
import re


RAIZ = Path(__file__).resolve().parent.parent

CARPETA = RAIZ / "templates" / "administracion"

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
    "lista_usuarios.html": (
        "usuarios:dashboard_administrador",
        "Volver al panel",
    ),
    "detalle_usuario.html": (
        "administracion:lista_usuarios",
        "Volver",
    ),
    "editar_usuario.html": (
        "administracion:detalle_usuario",
        "Cancelar",
    ),
}


PATRON_HEADER = re.compile(
    r"<header\b[^>]*>.*?</header>",
    re.I | re.S,
)

PATRON_ENLACE = re.compile(
    r"<a\b[^>]*>.*?</a>",
    re.I | re.S,
)


def preparar(
    codigo,
    nombre,
    ruta_esperada,
    texto_esperado,
):

    cabeceras = list(
        PATRON_HEADER.finditer(codigo)
    )

    if len(cabeceras) != 1:
        raise ValueError(
            f"{nombre}: encabezado inesperado."
        )

    coincidencia = cabeceras[0]
    cabecera = coincidencia.group()

    # No duplicar botones existentes.
    if INCLUDE in cabecera:
        return codigo, False

    enlaces = list(
        PATRON_ENLACE.finditer(cabecera)
    )

    if len(enlaces) != 1:
        raise ValueError(
            f"{nombre}: enlaces inesperados."
        )

    enlace = enlaces[0]
    original = enlace.group()

    if (
        ruta_esperada not in original
        or texto_esperado not in original
    ):
        raise ValueError(
            f"{nombre}: enlace diferente al revisado."
        )

    piezas = []

    # Conservar el botón contextual en
    # Detalle y Editar usuario.
    if nombre != "lista_usuarios.html":
        piezas.append(original.strip())

    # Agregar el botón estándar.
    piezas.append(INCLUDE)

    navegacion = (
        '<nav aria-label="Navegación de Administración" '
        'class="flex flex-wrap items-center '
        'justify-end gap-3">\n'
        + "\n".join(
            "                " + pieza
            for pieza in piezas
        )
        + "\n            </nav>"
    )

    cabecera = (
        cabecera[:enlace.start()]
        + navegacion
        + cabecera[enlace.end():]
    )

    if "items-center justify-between" not in cabecera:
        raise ValueError(
            f"{nombre}: diseño de encabezado inesperado."
        )

    cabecera = cabecera.replace(
        "items-center justify-between",
        "flex-wrap items-center justify-between gap-3",
        1,
    )

    actualizado = (
        codigo[:coincidencia.start()]
        + cabecera
        + codigo[coincidencia.end():]
    )

    if actualizado.count(INCLUDE) != 1:
        raise ValueError(
            f"{nombre}: error al agregar el botón."
        )

    return actualizado, True


def main():

    if not COMPONENTE.is_file():
        raise SystemExit(
            "Falta el componente "
            "templates/componentes/"
            "boton_volver_panel.html"
        )

    cambios = {}

    # Validar todos los archivos primero.
    for nombre, datos in ARCHIVOS.items():

        ruta = CARPETA / nombre

        if not ruta.is_file():
            raise SystemExit(
                f"No existe {ruta}. "
                "No se modificó nada."
            )

        original = ruta.read_text(
            encoding="utf-8-sig"
        )

        try:
            nuevo, cambiado = preparar(
                original,
                nombre,
                datos[0],
                datos[1],
            )

        except ValueError as error:
            raise SystemExit(
                f"{error} No se modificó nada."
            )

        if cambiado:
            cambios[ruta] = (
                original,
                nuevo,
            )

    if not cambios:
        print(
            "La navegación ya está actualizada."
        )
        return

    # Guardar respaldo fuera del repositorio.
    respaldo = (
        RAIZ.parent
        / (
            "respaldo_navegacion_administracion_"
            + datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )
        )
    )

    respaldo.mkdir(
        parents=True,
        exist_ok=False,
    )

    for ruta, (original, _) in cambios.items():

        (respaldo / ruta.name).write_text(
            original,
            encoding="utf-8",
        )

    # Actualizar plantillas.
    for ruta, (_, nuevo) in cambios.items():

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
        "Navegación de Administración actualizada."
    )


if __name__ == "__main__":
    main()
