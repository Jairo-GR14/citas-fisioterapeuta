
"""
Agrupa la navegación superior de Tratamientos.

Solo cambia encabezados HTML.
No modifica formularios ni lógica Django.
"""

from datetime import datetime
from pathlib import Path
import re
import shutil


RAIZ = Path(__file__).resolve().parent.parent

CARPETA = (
    RAIZ / "templates" / "tratamientos"
)

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
    "registrar_tratamiento.html": (
        "usuarios:perfil",
        "consultas:detalle_consulta",
    ),
    "editar_tratamiento.html": (
        "tratamientos:detalle_tratamiento",
        "usuarios:perfil",
    ),
    "detalle_tratamiento.html": (
        "tratamientos:historial_tratamientos",
        "consultas:detalle_consulta",
    ),
    "historial_tratamientos.html": (
        "consultas:detalle_consulta",
    ),
}

HEADER = re.compile(
    r"<header\b[^>]*>.*?</header>",
    re.I | re.S,
)

GRUPO = re.compile(
    r'<div\s+class="flex flex-wrap gap-3">'
    r".*?</div>",
    re.I | re.S,
)

ENLACE = re.compile(
    r"<a\b[^>]*>.*?</a>",
    re.I | re.S,
)

NAV_MARCA = (
    '<nav aria-label="Navegación '
    'de tratamientos"'
)


def transformar(html, nombre, rutas):

    coincidencias = list(
        HEADER.finditer(html)
    )

    if len(coincidencias) != 1:
        raise ValueError(
            f"{nombre}: se esperaba un encabezado."
        )

    coincidencia = coincidencias[0]
    header = coincidencia.group(0)

    # Evitar insertar botones duplicados.
    if INCLUDE in html:

        if (
            html.count(INCLUDE) == 1
            and NAV_MARCA in header
            and INCLUDE in header
        ):
            return html, False

        raise ValueError(
            f"{nombre}: el botón ya existe "
            "en otra posición."
        )

    grupos = list(
        GRUPO.finditer(header)
    )

    if len(grupos) > 1:
        raise ValueError(
            f"{nombre}: hay varios grupos "
            "de botones."
        )

    if grupos:

        bloque = grupos[0]
        contenido = bloque.group(0)

    else:

        enlaces = list(
            ENLACE.finditer(header)
        )

        if len(enlaces) != 1:
            raise ValueError(
                f"{nombre}: encabezado con "
                "enlaces inesperados."
            )

        bloque = enlaces[0]
        contenido = bloque.group(0)

    enlaces = ENLACE.findall(contenido)

    if len(enlaces) != len(rutas):
        raise ValueError(
            f"{nombre}: cantidad de enlaces "
            "distinta a la esperada."
        )

    # Verificar las rutas antes de editar.
    for enlace, ruta in zip(
        enlaces,
        rutas,
    ):

        if "{% url '" + ruta + "'" not in enlace:
            raise ValueError(
                f"{nombre}: cambió una ruta "
                f"del encabezado ({ruta})."
            )

    # Conservar los enlaces originales.
    # Todos estarán dentro del mismo nav.
    navegacion = (
        '<nav aria-label="Navegación de tratamientos" '
        'class="ml-auto flex flex-wrap '
        'items-center justify-end gap-3">\n'
        + "\n".join(
            enlace.strip()
            for enlace in enlaces
        )
        + "\n"
        + INCLUDE
        + "\n</nav>"
    )

    header_nuevo = (
        header[:bloque.start()]
        + navegacion
        + header[bloque.end():]
    )

    nuevo = (
        html[:coincidencia.start()]
        + header_nuevo
        + html[coincidencia.end():]
    )

    if nuevo.count(INCLUDE) != 1:
        raise ValueError(
            f"{nombre}: el botón se insertó "
            "de forma incorrecta."
        )

    return nuevo, True


def main():

    if not COMPONENTE.is_file():
        raise SystemExit(
            "Falta el componente "
            "templates/componentes/"
            "boton_volver_panel.html."
        )

    cambios = {}

    # Revisar todos los archivos antes
    # de realizar cualquier modificación.
    try:

        for nombre, rutas in ARCHIVOS.items():

            ruta = CARPETA / nombre

            original = ruta.read_text(
                encoding="utf-8-sig"
            )

            nuevo, cambio = transformar(
                original,
                nombre,
                rutas,
            )

            if cambio:
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
            "Los cuatro encabezados "
            "ya están actualizados."
        )
        return

    # Guardar respaldos fuera del repositorio.
    respaldo = (
        RAIZ.parent
        / (
            "respaldo_tratamientos_"
            + datetime.now().strftime(
                "%Y%m%d_%H%M%S_%f"
            )
        )
    )

    respaldo.mkdir(
        parents=True,
        exist_ok=False,
    )

    for ruta in cambios:
        shutil.copy2(
            ruta,
            respaldo / ruta.name,
        )

    # Aplicar solo los cambios de navegación.
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
        "Encabezados de Tratamientos "
        "actualizados."
    )


if __name__ == "__main__":
    main()
