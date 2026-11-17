
"""
Estandariza el acceso al panel en las tres
plantillas del módulo Servicios y Precios.

No modifica vistas, rutas, modelos ni formularios.
"""

from datetime import datetime
from pathlib import Path
import re
import shutil


RAIZ = Path(__file__).resolve().parent.parent

CARPETA = RAIZ / "templates" / "precios"

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
    "lista_precios.html": (
        "usuarios:redireccion_por_rol",
        "Volver al panel",
    ),
    "registrar_precio.html": (
        "precios:lista_precios",
        "Volver a servicios",
    ),
    "editar_precio.html": (
        "precios:lista_precios",
        "Volver a servicios",
    ),
}

ENCABEZADO = re.compile(
    r"<header\b[^>]*>.*?</header>",
    re.I | re.S,
)

ENLACE = re.compile(
    r"<a\b[^>]*>.*?</a>",
    re.I | re.S,
)


def modificar(
    contenido,
    nombre,
    ruta_esperada,
    texto_esperado,
):

    encontrados = list(
        ENCABEZADO.finditer(contenido)
    )

    if len(encontrados) != 1:
        raise ValueError(
            f"{nombre}: encabezado inesperado."
        )

    coincidencia = encontrados[0]
    encabezado = coincidencia.group(0)

    # Evitar duplicados si el script
    # ya fue ejecutado anteriormente.
    if INCLUDE in contenido:

        if (
            contenido.count(INCLUDE) != 1
            or INCLUDE not in encabezado
        ):
            raise ValueError(
                f"{nombre}: componente duplicado "
                "o fuera del encabezado."
            )

        return contenido, False

    etiqueta_url = (
        "{% url '"
        + ruta_esperada
        + "' %}"
    )

    enlaces = [
        enlace
        for enlace in ENLACE.finditer(encabezado)
        if (
            f'href="{etiqueta_url}"'
            in enlace.group(0)
            and texto_esperado in enlace.group(0)
        )
    ]

    if len(enlaces) != 1:
        raise ValueError(
            f"{nombre}: no se encontró "
            "el enlace esperado."
        )

    enlace = enlaces[0]

    # La lista de servicios ya tiene
    # un botón al panel: lo sustituimos.
    if nombre == "lista_precios.html":

        sustituto = INCLUDE

    else:

        # Registrar y Editar mantienen
        # el enlace contextual a servicios.
        sustituto = (
            '<nav aria-label="Navegación de servicios" '
            'class="flex flex-wrap items-center '
            'justify-end gap-3">\n'
            + enlace.group(0)
            + "\n                "
            + INCLUDE
            + "\n            </nav>"
        )

    encabezado = (
        encabezado[:enlace.start()]
        + sustituto
        + encabezado[enlace.end():]
    )

    # Permitir acomodar los botones
    # en pantallas pequeñas.
    clase_original = (
        "items-center justify-between"
    )

    if encabezado.count(clase_original) != 1:
        raise ValueError(
            f"{nombre}: estructura "
            "del encabezado diferente."
        )

    encabezado = encabezado.replace(
        clase_original,
        "flex-wrap items-center "
        "justify-between gap-3",
        1,
    )

    actualizado = (
        contenido[:coincidencia.start()]
        + encabezado
        + contenido[coincidencia.end():]
    )

    if actualizado.count(INCLUDE) != 1:
        raise ValueError(
            f"{nombre}: error al insertar "
            "el componente."
        )

    return actualizado, True


def main():

    if not COMPONENTE.is_file():
        raise SystemExit(
            "Falta el componente "
            "templates/componentes/"
            "boton_volver_panel.html. "
            "No se modificó ningún archivo."
        )

    cambios = {}

    # Primero validamos los tres HTML.
    # Si falla alguno, no modificamos nada.
    try:

        for nombre, datos in ARCHIVOS.items():

            ruta_esperada, texto = datos
            archivo = CARPETA / nombre

            if not archivo.is_file():
                raise ValueError(
                    f"No existe {archivo}."
                )

            original = archivo.read_text(
                encoding="utf-8-sig"
            )

            nuevo, cambiado = modificar(
                original,
                nombre,
                ruta_esperada,
                texto,
            )

            if cambiado:
                cambios[archivo] = nuevo

    except (ValueError, OSError) as error:

        raise SystemExit(
            f"Revisión detenida: {error} "
            "No se modificó ningún archivo."
        )

    if not cambios:

        print(
            "Las tres plantillas ya están "
            "actualizadas. Sin cambios."
        )

        return

    # Guardar respaldos fuera del repositorio.
    respaldo = (
        RAIZ.parent
        / (
            "respaldo_navegacion_precios_"
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

    # Actualizar solo los HTML necesarios.
    for archivo, nuevo in cambios.items():

        archivo.write_text(
            nuevo,
            encoding="utf-8",
        )

        print(
            "Actualizado:",
            archivo.relative_to(RAIZ),
        )

    print()
    print("Respaldo:", respaldo)
    print(
        "Navegación de Servicios "
        "y Precios actualizada."
    )


if __name__ == "__main__":
    main()
