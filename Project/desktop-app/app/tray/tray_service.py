# Servicio de bandeja del sistema: icono, menu y bucle de eventos nativo de pystray
# Orden de ciclo de vida: create_tray_icon -> run_tray_loop -> stop_tray_loop;
# update_tray_menu sincroniza el estado interno con la UI en cualquier momento

from typing import Callable

import pystray
from PIL import Image, ImageDraw

from app.config.constants import APP_NAME, APP_VERSION
from app.core import color_matrix_engine, overlay_renderer
from app.tray import tray_menu_actions
from app.ui.theme.design_tokens import LIGHT_PALETTE

# Tamano en pixeles del icono circular generado para la bandeja
ICON_SIZE = 64
ICON_MARGIN = 6

# Perfiles disponibles en el submenu de cambio rapido, en el orden solicitado
QUICK_SWITCH_PROFILES = (
    ("Deuteranomalia", "deuteranomaly"),
    ("Deuteranopia", "deuteranopia"),
    ("Tritanomalia", "tritanomaly"),
    ("Tritanopia", "tritanopia"),
    ("Vision normal", "normal"),
)

# Severidad fija del submenu de cambio rapido; no hay control deslizante en la bandeja
QUICK_SWITCH_SEVERITY = 1.0

# Estado en memoria reflejado por los items de menu con marca de verificacion
_tray_state = {
    "correction_active": False,
    "active_deficiency_type": "normal",
}


# Crea el icono de bandeja con su menu completo, listo para ejecutar
def create_tray_icon(on_open_window: Callable, on_exit: Callable) -> pystray.Icon:
    return pystray.Icon(
        name=APP_NAME,
        icon=_build_icon_image(),
        title=APP_NAME,
        menu=_build_menu(on_open_window, on_exit),
    )


# Bloquea el hilo actual ejecutando el bucle de eventos nativo del icono
def run_tray_loop(icon: pystray.Icon) -> None:
    icon.run()


# Senala al bucle de eventos del icono que debe detenerse
def stop_tray_loop(icon: pystray.Icon) -> None:
    icon.stop()


# Sincroniza el estado interno con la UI y fuerza el repintado del menu
def update_tray_menu(
    icon: pystray.Icon, correction_active: bool, active_profile_label: str
) -> None:
    _tray_state["correction_active"] = correction_active
    _tray_state["active_deficiency_type"] = _resolve_deficiency_type(active_profile_label)
    icon.update_menu()


# Genera un icono circular con Pillow usando el color de acento de la paleta del proyecto
def _build_icon_image() -> Image.Image:
    image = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse(
        (ICON_MARGIN, ICON_MARGIN, ICON_SIZE - ICON_MARGIN, ICON_SIZE - ICON_MARGIN),
        fill=_hex_to_rgba(LIGHT_PALETTE.accent),
    )
    return image


# Convierte un color hexadecimal "#RRGGBB" en una tupla RGBA opaca para Pillow
def _hex_to_rgba(hex_color: str) -> tuple:
    stripped = hex_color.lstrip("#")
    red = int(stripped[0:2], 16)
    green = int(stripped[2:4], 16)
    blue = int(stripped[4:6], 16)
    return (red, green, blue, 255)


# Ensambla el menu completo en el orden fijo definido por la especificacion
def _build_menu(on_open_window: Callable, on_exit: Callable) -> pystray.Menu:
    return pystray.Menu(
        pystray.MenuItem(APP_NAME + " " + APP_VERSION, None, enabled=False),
        pystray.Menu.SEPARATOR,
        _build_toggle_correction_item(),
        _build_quick_switch_submenu(),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Abrir ventana", on_open_window),
        pystray.MenuItem("Salir", on_exit),
    )


# Item de menu que activa o pausa la correccion y refleja su estado con una marca
def _build_toggle_correction_item() -> pystray.MenuItem:
    return pystray.MenuItem(
        "Correccion de color",
        _handle_toggle_correction_click,
        checked=lambda item: _tray_state["correction_active"],
    )


# Submenu de perfiles de deficiencia con marca radial sobre el perfil activo
def _build_quick_switch_submenu() -> pystray.MenuItem:
    items = [
        pystray.MenuItem(
            label,
            _make_switch_profile_handler(deficiency_type),
            checked=_make_deficiency_checker(deficiency_type),
            radio=True,
        )
        for label, deficiency_type in QUICK_SWITCH_PROFILES
    ]
    return pystray.MenuItem("Perfil rapido", pystray.Menu(*items))


# Construye el manejador de clic para un perfil especifico del submenu de cambio rapido
def _make_switch_profile_handler(deficiency_type: str) -> Callable:
    def handler(icon: pystray.Icon, item: pystray.MenuItem) -> None:
        tray_menu_actions.handle_switch_profile(
            icon,
            deficiency_type,
            QUICK_SWITCH_SEVERITY,
            color_matrix_engine,
            overlay_renderer,
        )
        _tray_state["active_deficiency_type"] = deficiency_type
        icon.update_menu()

    return handler


# Construye el evaluador de marca radial para un perfil especifico del submenu
def _make_deficiency_checker(deficiency_type: str) -> Callable:
    def is_checked(item: pystray.MenuItem) -> bool:
        return _tray_state["active_deficiency_type"] == deficiency_type

    return is_checked


# Manejador de clic del item de correccion; delega en tray_menu_actions y sincroniza el estado
def _handle_toggle_correction_click(icon: pystray.Icon, item: pystray.MenuItem) -> None:
    new_state = tray_menu_actions.handle_toggle_correction(
        icon, _tray_state["correction_active"], overlay_renderer
    )
    _tray_state["correction_active"] = new_state
    icon.update_menu()


# Traduce la etiqueta de deficiencia mostrada en el panel a su tipo tecnico interno
def _resolve_deficiency_type(active_profile_label: str) -> str:
    for label, deficiency_type in QUICK_SWITCH_PROFILES:
        if label == active_profile_label:
            return deficiency_type
    return _tray_state["active_deficiency_type"]
