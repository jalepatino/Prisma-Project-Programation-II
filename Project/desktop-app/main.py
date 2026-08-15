# Punto de entrada de la aplicacion desktop ChromaticVision
# Configura la ventana nativa, monta el shell principal, la bandeja del sistema,
# aplica las preferencias de arranque guardadas y registra los eventos globales

import sys
import threading
import winreg
from pathlib import Path

import flet as ft

from app.config.app_config import load_config
from app.config.constants import (
    APP_NAME,
    DEFAULT_ROUTE,
    WINDOW_DEFAULT_HEIGHT,
    WINDOW_DEFAULT_WIDTH,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
)
from app.tray import tray_menu_actions, tray_service
from app.ui.main_window import MainWindow
from app.ui.theme.design_tokens import get_palette
from app.ui.theme.theme_builder import build_theme

# Clave del registro de Windows donde se declaran los programas de arranque automatico
STARTUP_REGISTRY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


# Prepara la pagina y la ventana nativa antes de montar cualquier control
def initialize_page(page: ft.Page) -> None:
    palette = get_palette(ft.ThemeMode.LIGHT)
    page.title = APP_NAME
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = build_theme(palette)
    page.bgcolor = palette.bg_primary
    page.padding = 0
    page.spacing = 0
    page.window.width = WINDOW_DEFAULT_WIDTH
    page.window.height = WINDOW_DEFAULT_HEIGHT
    page.window.min_width = WINDOW_MIN_WIDTH
    page.window.min_height = WINDOW_MIN_HEIGHT
    page.window.prevent_close = True
    page.window.center()


# Monta el shell principal y conecta los manejadores globales de la pagina
def build_application(page: ft.Page) -> MainWindow:
    main_window = MainWindow(page)
    page.on_keyboard_event = main_window.handle_keyboard_event
    page.on_resize = main_window.handle_resize

    # Oculta la ventana en el cierre; solo "Salir" en la bandeja termina el proceso
    def handle_window_event(event: ft.WindowEvent) -> None:
        if event.type == ft.WindowEventType.CLOSE:
            page.window.visible = False
            page.update()

    page.window.on_event = handle_window_event
    page.add(main_window)
    main_window.navigate_to(DEFAULT_ROUTE)
    return main_window


# Crea el icono de bandeja, lo vincula al shell y arranca su bucle en un hilo independiente
def start_tray_service(page: ft.Page, main_window: MainWindow) -> None:
    def open_window_action(icon, item) -> None:
        tray_menu_actions.handle_open_window(icon, page)

    def exit_action(icon, item) -> None:
        tray_menu_actions.handle_exit(icon, page)

    icon = tray_service.create_tray_icon(open_window_action, exit_action)
    main_window.set_tray_icon(icon)
    tray_thread = threading.Thread(target=tray_service.run_tray_loop, args=(icon,), daemon=True)
    tray_thread.start()


# Registra o quita la aplicacion del arranque automatico de Windows segun la preferencia
def apply_startup_preference(launch_on_startup: bool) -> None:
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, STARTUP_REGISTRY_PATH, 0, winreg.KEY_SET_VALUE
        )
    except OSError:
        return
    try:
        if launch_on_startup:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _resolve_executable_command())
        else:
            _remove_startup_registry_value(key)
    finally:
        winreg.CloseKey(key)


# Objetivo invocado por Flet al crear una sesion de la aplicacion
def run_application(page: ft.Page) -> None:
    config = load_config()
    initialize_page(page)
    main_window = build_application(page)
    start_tray_service(page, main_window)
    apply_startup_preference(bool(config.get("launch_on_startup", False)))
    if config.get("start_minimized", True):
        page.window.visible = False
    page.update()


# Quita el valor de arranque automatico si existe; no falla si ya estaba ausente
def _remove_startup_registry_value(key) -> None:
    try:
        winreg.DeleteValue(key, APP_NAME)
    except FileNotFoundError:
        pass


# Comando para relanzar la aplicacion: el ejecutable congelado, o el interprete mas este script
def _resolve_executable_command() -> str:
    if getattr(sys, "frozen", False):
        return sys.executable
    return sys.executable + ' "' + str(Path(__file__).resolve()) + '"'


if __name__ == "__main__":
    ft.run(run_application)
