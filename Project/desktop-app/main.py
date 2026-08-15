# Punto de entrada de la aplicacion desktop ChromaticVision
# Configura la ventana nativa, monta el shell principal, la bandeja del sistema
# y registra los eventos globales, incluyendo el cierre hacia la bandeja

import threading

import flet as ft

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


# Objetivo invocado por Flet al crear una sesion de la aplicacion
def run_application(page: ft.Page) -> None:
    initialize_page(page)
    main_window = build_application(page)
    start_tray_service(page, main_window)
    page.update()


if __name__ == "__main__":
    ft.run(run_application)
