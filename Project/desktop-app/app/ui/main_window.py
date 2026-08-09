# Shell raiz de la aplicacion: barra lateral, cabecera y area de contenido enrutada
# Unico punto que conoce el mapa de rutas y coordina los cambios de tema

from typing import Dict, Optional

import flet as ft

from app.config.constants import (
    DEFAULT_ROUTE,
    NAVIGATION_DESTINATIONS,
    NavigationDestination,
    RESPONSIVE_COLLAPSE_WIDTH,
)
from app.ui.components.app_header import AppHeader
from app.ui.components.navigation_bar import NavigationSidebar
from app.ui.theme.design_tokens import (
    Curve,
    Duration,
    get_opposite_theme_mode,
    get_palette,
)
from app.ui.theme.theme_builder import build_theme
from app.ui.views.base_view import BaseView
from app.ui.views.dashboard_view import DashboardView
from app.ui.views.filters_view import FiltersView
from app.ui.views.picker_view import PickerView
from app.ui.views.settings_view import SettingsView
from app.utils.control_sync import request_update

# Mapa de rutas a clases de vista; ampliar aqui al agregar nuevas pantallas
VIEW_REGISTRY = (DashboardView, PickerView, FiltersView, SettingsView)


class MainWindow(ft.Container):
    # Construye el layout completo y deja la ruta por defecto activa
    def __init__(self, page: ft.Page) -> None:
        super().__init__(expand=True)
        self.host_page = page
        self.palette = get_palette(page.theme_mode)
        self.active_route = DEFAULT_ROUTE
        self.sidebar_collapsed = False
        self.correction_active = False
        self._auto_collapsed = False
        self._views: Dict[str, BaseView] = {}
        self.bgcolor = self.palette.bg_primary
        self.content = self._build_shell()

    # Cambia la vista visible y sincroniza barra lateral y cabecera
    def navigate_to(self, route: str) -> None:
        destination = self._find_destination(route)
        if destination is None or route not in self._views:
            return
        previous_view = self._views.get(self.active_route)
        if previous_view is not None and route != self.active_route:
            previous_view.deactivate()
        self.active_route = route
        target_view = self._views[route]
        self._content_switcher.content = target_view
        self._sidebar.select_route(route)
        self._header.set_view_context(destination.title, destination.subtitle)
        request_update(self._content_switcher)
        target_view.activate()

    # Alterna el modo de tema y reconstruye el shell con la nueva paleta
    def toggle_theme(self) -> None:
        self.host_page.theme_mode = get_opposite_theme_mode(self.host_page.theme_mode)
        self.palette = get_palette(self.host_page.theme_mode)
        self.host_page.theme = build_theme(self.palette)
        self.host_page.bgcolor = self.palette.bg_primary
        self.bgcolor = self.palette.bg_primary
        self.content = self._build_shell()
        self.host_page.update()

    # Alterna el ancho de la barra lateral entre expandido y compacto
    def toggle_sidebar(self) -> None:
        self.sidebar_collapsed = not self.sidebar_collapsed
        self._auto_collapsed = False
        self._sidebar.set_collapsed(self.sidebar_collapsed)

    # Atajos globales de navegacion, colapso y tema
    def handle_keyboard_event(self, event: ft.KeyboardEvent) -> None:
        if event.ctrl:
            self._handle_control_shortcut(event.key)
            return
        if event.key == "Arrow Down":
            self._sidebar.move_focus(1)
        elif event.key == "Arrow Up":
            self._sidebar.move_focus(-1)
        elif event.key == "Enter":
            self._sidebar.activate_focused_item()
        elif event.key == "Escape":
            self._sidebar.clear_focus()

    # Colapsa la barra lateral automaticamente en ventanas estrechas
    def handle_resize(self, event: ft.ControlEvent) -> None:
        width = self.host_page.window.width or RESPONSIVE_COLLAPSE_WIDTH
        should_collapse = width < RESPONSIVE_COLLAPSE_WIDTH
        if should_collapse and not self.sidebar_collapsed:
            self.sidebar_collapsed = True
            self._auto_collapsed = True
            self._sidebar.set_collapsed(True)
            return
        if not should_collapse and self._auto_collapsed:
            self.sidebar_collapsed = False
            self._auto_collapsed = False
            self._sidebar.set_collapsed(False)

    # Ensambla barra lateral, cabecera y area de contenido animada
    def _build_shell(self) -> ft.Control:
        self._create_views()
        destination = self._find_destination(self.active_route)
        self._sidebar = NavigationSidebar(
            palette=self.palette,
            destinations=NAVIGATION_DESTINATIONS,
            active_route=self.active_route,
            on_route_change=self.navigate_to,
            on_toggle_collapsed=self.toggle_sidebar,
            collapsed=self.sidebar_collapsed,
        )
        self._header = AppHeader(
            palette=self.palette,
            title=destination.title if destination else "",
            subtitle=destination.subtitle if destination else "",
            is_dark_theme=self.host_page.theme_mode == ft.ThemeMode.DARK,
            on_toggle_theme=self.toggle_theme,
            on_toggle_correction=self._handle_correction_toggle,
            correction_active=self.correction_active,
        )
        self._content_switcher = ft.AnimatedSwitcher(
            content=self._views[self.active_route],
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=Duration.MODERATE,
            reverse_duration=Duration.BASE,
            switch_in_curve=Curve.DECELERATE,
            switch_out_curve=Curve.ACCELERATE,
            expand=True,
        )
        content_column = ft.Column(
            controls=[self._header, self._content_switcher],
            spacing=0,
            expand=True,
        )
        return ft.Row(
            controls=[self._sidebar, content_column],
            spacing=0,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    # Instancia una vista por ruta registrada con la paleta activa
    def _create_views(self) -> None:
        self._views = {}
        for view_class in VIEW_REGISTRY:
            self._views[view_class.route] = view_class(self.palette)

    # Localiza el descriptor de navegacion asociado a una ruta
    def _find_destination(self, route: str) -> Optional[NavigationDestination]:
        for destination in NAVIGATION_DESTINATIONS:
            if destination.route == route:
                return destination
        return None

    # Resuelve los atajos que requieren la tecla Control
    def _handle_control_shortcut(self, key: str) -> None:
        if key == "B":
            self.toggle_sidebar()
            return
        if key == "D":
            self.toggle_theme()
            return
        if key.isdigit():
            index = int(key) - 1
            if 0 <= index < len(NAVIGATION_DESTINATIONS):
                self.navigate_to(NAVIGATION_DESTINATIONS[index].route)

    # Guarda el estado de correccion emitido por la cabecera
    def _handle_correction_toggle(self, is_active: bool) -> None:
        self.correction_active = is_active
