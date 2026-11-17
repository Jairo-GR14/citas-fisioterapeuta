
"""
Unifica el botón Volver al panel en
las nueve plantillas del módulo Citas.

No modifica:
- Las vistas de Django.
- Los modelos.
- Las rutas.
- Los formularios.
- El JavaScript de FullCalendar.
"""

from datetime import datetime
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent

TEMPLATES = ROOT / "templates" / "citas"

COMPONENTE = (
    ROOT
    / "templates"
    / "componentes"
    / "boton_volver_panel.html"
)

INCLUDE = (
    '{% include '
    '"componentes/boton_volver_panel.html" %}'
)

ARCHIVOS = (
    "agenda.html",
    "agendar_cita.html",
    "detalle_cita.html",
    "editar_cita.html",
    "cancelar_cita.html",
    "confirmar_cita.html",
    "horarios_disponibles.html",
    "mis_citas.html",
    "cita_emergencia.html",
)

HEADER = re.compile(
    r"<header\b[^>]*>.*?</header>",
    re.S | re.I,
)

MAIN = re.compile(
    r"<main\b[^>]*>",
    re.I,
)


def ajustar(codigo, nombre):

    # Evitar agregar botones duplicados.
    if INCLUDE in codigo:
        return codigo, False

    # En Agenda ya existe un enlace al panel
    # en la parte inferior. Lo moveremos arriba.
    if nombre == "agenda.html":

        codigo, reemplazos = re.subn(
            r'\s*<!-- VOLVER AL PANEL -->\s*'
            r'<div class="mt-8 text-right">\s*'
            r'<a\s+href="\{% url '
            r"'usuarios:redireccion_por_rol'"
            r' %\}"[^>]*>'
            r'\s*Volver al panel\s*</a>\s*</div>',
            "",
            codigo,
            count=1,
            flags=re.S,
        )

        if reemplazos != 1:
            raise ValueError(
                "agenda.html: no se encontró "
                "el enlace inferior esperado."
            )

    encabezado = HEADER.search(codigo)

    if encabezado:

        bloque = encabezado.group(0)

        # En Mis citas, quitamos el enlace
        # anterior Mi panel para no duplicarlo.
        if nombre == "mis_citas.html":

            bloque, reemplazos = re.subn(
                r'\s*<a\s+href="\{% url '
                r"'usuarios:redireccion_por_rol'"
                r' %\}"[^>]*>'
                r'\s*Mi panel\s*</a>',
                "",
                bloque,
                count=1,
                flags=re.S,
            )

            if reemplazos != 1:
                raise ValueError(
                    "mis_citas.html: no se encontró "
                    "el enlace Mi panel."
                )

        # En Detalle, el fisioterapeuta
        # tendrá Mi agenda como regreso contextual.
        # El nuevo botón servirá para su panel.
        if nombre == "detalle_cita.html":

            anterior = (
                'href="{% url '
                "'usuarios:dashboard_fisioterapeuta'"
                ' %}"'
            )

            if anterior not in bloque:
                raise ValueError(
                    "detalle_cita.html: no se encontró "
                    "el enlace del fisioterapeuta."
                )

            bloque = bloque.replace(
                anterior,
                'href="{% url '
                "'citas:agenda'"
                ' %}"',
                1,
            )

            bloque = bloque.replace(
                "← Mi panel",
                "← Mi agenda",
                1,
            )

        # Permitir que el encabezado acomode
        # los botones en pantallas pequeñas.
        contenedor = re.search(
            r'<div class="([^"]*\bmx-auto flex\b[^"]*)">',
            bloque,
        )

        if contenedor is None:
            raise ValueError(
                f"{nombre}: encabezado inesperado."
            )

        clases = contenedor.group(1)

        if "flex-wrap" not in clases:

            bloque = bloque.replace(
                contenedor.group(0),
                f'<div class="{clases} flex-wrap">',
                1,
            )

        # Agregar el botón dentro del encabezado.
        posicion = bloque.rfind("</div>")

        if posicion == -1:
            raise ValueError(
                f"{nombre}: falta cerrar el encabezado."
            )

        insercion = (
            "\n            "
            + INCLUDE
            + "\n\n        "
        )

        bloque = (
            bloque[:posicion]
            + insercion
            + bloque[posicion:]
        )

        codigo = (
            codigo[:encabezado.start()]
            + bloque
            + codigo[encabezado.end():]
        )

    else:

        # Cancelar y Confirmar no tienen
        # encabezado general.
        # Colocamos el botón al inicio de main.
        principal = MAIN.search(codigo)

        if principal is None:
            raise ValueError(
                f"{nombre}: no se encontró main."
            )

        insercion = (
            "\n"
            '<nav aria-label="Navegación principal" '
            'class="mb-6 flex justify-end">\n'
            "    "
            + INCLUDE
            + "\n</nav>\n"
        )

        codigo = (
            codigo[:principal.end()]
            + insercion
            + codigo[principal.end():]
        )

    if codigo.count(INCLUDE) != 1:

        raise ValueError(
            f"{nombre}: cantidad incorrecta "
            "de botones."
        )

    return codigo, True


def main():

    # El componente fue creado en el paso
    # anterior de Pacientes y Fisioterapeutas.
    if not COMPONENTE.is_file():

        raise SystemExit(
            "Falta el archivo "
            "templates/componentes/"
            "boton_volver_panel.html. "
            "No se modificó nada."
        )

    preparados = {}

    # Revisar todos los archivos ANTES
    # de modificar cualquiera.
    for archivo in ARCHIVOS:

        ruta = TEMPLATES / archivo

        if not ruta.is_file():

            raise SystemExit(
                f"No existe {ruta}. "
                "No se modificó nada."
            )

        original = ruta.read_text(
            encoding="utf-8-sig"
        )

        nuevo, cambiado = ajustar(
            original,
            archivo,
        )

        if cambiado:

            preparados[ruta] = (
                original,
                nuevo,
            )

    if not preparados:

        print(
            "La navegación ya está actualizada. "
            "No hay cambios."
        )

        return

    # Crear respaldo fuera del repositorio.
    respaldo = (
        ROOT.parent
        / (
            "respaldo_navegacion_citas_"
            + datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )
        )
    )

    respaldo.mkdir(
        parents=True,
        exist_ok=False,
    )

    for ruta, (original, nuevo) in preparados.items():

        (respaldo / ruta.name).write_text(
            original,
            encoding="utf-8",
        )

    # Actualizar las plantillas.
    for ruta, (original, nuevo) in preparados.items():

        ruta.write_text(
            nuevo,
            encoding="utf-8",
        )

        print(
            "Actualizado:",
            ruta.relative_to(ROOT),
        )

    print()
    print("Respaldo:", respaldo)
    print()
    print(
        "Navegación actualizada correctamente."
    )


if __name__ == "__main__":
    main()
