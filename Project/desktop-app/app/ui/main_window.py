# Shell raiz de la aplicacion: barra lateral, cabecera y area de contenido enrutada
# Unico punto que conoce el mapa de rutas y coordina los cambios de tema

from typing import Any, Dict, Optional

import flet as ft
import numpy as np

from app.config.app_config import load_config
from app.config.constants import (
    AppRoute,
    DEFAULT_ROUTE,
    NAVIGATION_DESTINATIONS,
    NavigationDestination,
    RESPONSIVE_COLLAPSE_WIDTH,
)
from app.core import overlay_renderer
from app.core.color_matrix_engine import build_matrix_for_profile
from app.profiles.profile_model import CURRENT_SCHEMA_VERSION, ColorVisionProfile
from app.profiles.profile_service import get_profile
from app.tray import tray_service
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
from app.ui.views.dashboard_view import (
    DEFAULT_DEFICIENCY_LABEL,
    DEFAULT_SEVERITY_LABEL,
    DashboardView,
)
from app.ui.views.filters_view import (
    BRIGHTNESS_DEFAULT,
    CONTRAST_DEFAULT,
    KELVIN_DEFAULT,
    FiltersView,
)
from app.ui.views.picker_view import PickerView
from app.ui.views.settings_view import SettingsView
from app.utils.control_sync import request_update

# Mapa de rutas a clases de vista; ampliar aqui al agregar nuevas pantallas
VIEW_REGISTRY = (DashboardView, PickerView, FiltersView, SettingsView)

# Traduccion de los tipos tecnicos de deficiencia a etiquetas legibles en espanol
_DEFICIENCY_LABELS = {
    "deuteranomaly": "Deuteranomalia",
    "deuteranopia": "Deuteranopia",
    "tritanomaly": "Tritanomalia",
    "tritanopia": "Tritanopia",
    "normal": "Vision normal",
}

# Perfil de respaldo cuando no hay un perfil activo configurado (sin correccion cromatica)
_DEFAULT_PROFILE = ColorVisionProfile(
    schema_version=CURRENT_SCHEMA_VERSION,
    deficiency_type="normal",
    severity=0.0,
    source="manual",
    generated_at="1970-01-01T00:00:00Z",
)


class MainWindow(ft.Container):
    # Construye el layout completo, carga el perfil activo y deja la ruta por defecto activa
    def __init__(self, page: ft.Page) -> None:
        super().__init__(expand=True)
        self.host_page = page
        self.palette = get_palette(page.theme_mode)
        self.active_route = DEFAULT_ROUTE
        self.sidebar_collapsed = False
        self.correction_active = False
        self._auto_collapsed = False
        self._views: Dict[str, BaseView] = {}
        self._active_profile = _load_active_profile()
        self._tray_icon: Optional[Any] = None
        self.bgcolor = self.palette.bg_primary
        self.content = self._build_shell()
        if self._active_profile is not None:
            self.on_profile_changed(self._active_profile)
        else:
            self._refresh_dashboard_summary()

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

    # Alterna el modo de tema, reconstruye el shell con la nueva paleta y preserva el estado
    def toggle_theme(self) -> None:
        filters_state = self._views[AppRoute.FILTERS].get_filter_state()
        settings_state = self._views[AppRoute.SETTINGS].get_preferences()
        self.host_page.theme_mode = get_opposite_theme_mode(self.host_page.theme_mode)
        self.palette = get_palette(self.host_page.theme_mode)
        self.host_page.theme = build_theme(self.palette)
        self.host_page.bgcolor = self.palette.bg_primary
        self.bgcolor = self.palette.bg_primary
        self.content = self._build_shell()
        self._views[AppRoute.FILTERS].set_filter_state(filters_state)
        self._views[AppRoute.SETTINGS].set_preferences(settings_state)
        self._refresh_dashboard_summary()
        self.host_page.update()

    # Alterna el ancho de la barra lateral entre expandido y compacto
    def toggle_sidebar(self) -> None:
        self.sidebar_collapsed = not self.sidebar_collapsed
        self._auto_collapsed = False
        self._sidebar.set_collapsed(self.sidebar_collapsed)

    # Vincula el icono de bandeja creado en main.py para mantenerlo sincronizado
    def set_tray_icon(self, icon: Any) -> None:
        self._tray_icon = icon

    # Aplica un perfil nuevo o recien importado: panel, matriz activa y menu de bandeja
    def on_profile_changed(self, profile: ColorVisionProfile) -> None:
        self._active_profile = profile
        self._refresh_dashboard_summary()
        overlay_renderer.update_active_matrix(build_matrix_for_profile(profile, "correct"))
        if self._tray_icon is not None:
            tray_service.update_tray_menu(
                self._tray_icon, self.correction_active, _describe_deficiency(self._active_profile)
            )

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
        self._views[AppRoute.SETTINGS].set_profile_changed_callback(self.on_profile_changed)

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

    # Arranca o detiene el bucle de superposicion y sincroniza el menu de bandeja
    def _handle_correction_toggle(self, is_active: bool) -> None:
        self.correction_active = is_active
        if is_active:
            overlay_renderer.start_render_loop(self._build_active_correction_matrix())
            overlay_renderer.update_filter_state(self._views[AppRoute.FILTERS].get_filter_state())
        else:
            overlay_renderer.stop_render_loop()
        if self._tray_icon is not None:
            tray_service.update_tray_menu(
                self._tray_icon, self.correction_active, _describe_deficiency(self._active_profile)
            )

    # Matriz de correccion CVD del perfil activo; la capa de temperatura/brillo/contraste
    # se apila por separado en el hilo de render via overlay_renderer.update_filter_state
    def _build_active_correction_matrix(self) -> np.ndarray:
        profile = self._active_profile if self._active_profile is not None else _DEFAULT_PROFILE
        return build_matrix_for_profile(profile, "correct")

    # Recalcula las etiquetas del panel a partir del perfil activo y el estado de filtros
    def _refresh_dashboard_summary(self) -> None:
        dashboard = self._views.get(AppRoute.DASHBOARD)
        if dashboard is None:
            return
        dashboard.update_summary(
            _describe_deficiency(self._active_profile),
            _describe_severity(self._active_profile),
            _describe_active_filters(self._views[AppRoute.FILTERS]),
        )


# Carga el perfil activo declarado en la configuracion local; None si no hay ninguno
def _load_active_profile() -> Optional[ColorVisionProfile]:
    config = load_config()
    profile_id = config.get("active_profile_id")
    if not profile_id:
        return None
    return get_profile(profile_id)


# Etiqueta de deficiencia legible en espanol a partir del tipo tecnico del perfil
def _describe_deficiency(profile: Optional[ColorVisionProfile]) -> str:
    if profile is None:
        return DEFAULT_DEFICIENCY_LABEL
    return _DEFICIENCY_LABELS.get(profile.deficiency_type, profile.deficiency_type)


# Etiqueta de severidad como porcentaje legible
def _describe_severity(profile: Optional[ColorVisionProfile]) -> str:
    if profile is None:
        return DEFAULT_SEVERITY_LABEL
    return str(round(profile.severity * 100)) + "%"


# Cuenta los filtros que se apartan de su valor neutro para la tarjeta de resumen
def _describe_active_filters(filters_view: FiltersView) -> str:
    state = filters_view.get_filter_state()
    active_count = 0
    if state["kelvin"] != KELVIN_DEFAULT:
        active_count += 1
    if state["brightness_ceiling"] != BRIGHTNESS_DEFAULT:
        active_count += 1
    if state["contrast"] != CONTRAST_DEFAULT:
        active_count += 1
    if state["schedule_enabled"]:
        active_count += 1
    return str(active_count) + " activos"
