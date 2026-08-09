# Punto de entrada de la aplicacion desktop ChromaticVision
# Configura la ventana nativa, monta el shell principal y registra los eventos globales

import flet as ft

from app.config.constants import (
    APP_NAME,
    DEFAULT_ROUTE,
    WINDOW_DEFAULT_HEIGHT,
    WINDOW_DEFAULT_WIDTH,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
)
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
    page.window.center()


# Monta el shell principal y conecta los manejadores globales de la pagina
def build_application(page: ft.Page) -> MainWindow:
    main_window = MainWindow(page)
    page.on_keyboard_event = main_window.handle_keyboard_event
    page.on_resize = main_window.handle_resize
    page.add(main_window)
    main_window.navigate_to(DEFAULT_ROUTE)
    return main_window


# Objetivo invocado por Flet al crear una sesion de la aplicacion
def run_application(page: ft.Page) -> None:
    initialize_page(page)
    build_application(page)
    page.update()


if __name__ == "__main__":
    ft.run(run_application)
