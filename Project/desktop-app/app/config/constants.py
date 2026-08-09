# Constantes fijas de la aplicacion desktop: identidad, ventana, rutas y navegacion
# Este modulo no debe importar logica de negocio ni componentes de UI

from dataclasses import dataclass

import flet as ft

# Identidad de la aplicacion mostrada en la ventana nativa y en la barra lateral
APP_NAME = "ChromaticVision"
APP_TAGLINE = "Suite de accesibilidad visual"
APP_VERSION = "1.0.0"

# Geometria de la ventana nativa en pixeles logicos
WINDOW_DEFAULT_WIDTH = 1240
WINDOW_DEFAULT_HEIGHT = 820
WINDOW_MIN_WIDTH = 960
WINDOW_MIN_HEIGHT = 640

# Dimensiones del shell de navegacion alineadas al grid base de 8px
SIDEBAR_EXPANDED_WIDTH = 248
SIDEBAR_COLLAPSED_WIDTH = 72
HEADER_HEIGHT = 64
RESPONSIVE_COLLAPSE_WIDTH = 1080

# Presupuesto de rendimiento heredado de la especificacion tecnica
TARGET_OVERLAY_FPS = 30
TARGET_PICKER_FPS = 60


# Identificadores de ruta usados por el router interno del shell
class AppRoute:
    DASHBOARD = "dashboard"
    PICKER = "picker"
    FILTERS = "filters"
    SETTINGS = "settings"


# Descriptor inmutable de un destino de navegacion
@dataclass(frozen=True)
class NavigationDestination:
    route: str
    label: str
    icon: str
    selected_icon: str
    title: str
    subtitle: str


# Destinos en orden de aparicion; el orden define tambien los atajos Ctrl+1..Ctrl+4
NAVIGATION_DESTINATIONS = (
    NavigationDestination(
        route=AppRoute.DASHBOARD,
        label="Panel",
        icon=ft.Icons.SPACE_DASHBOARD_OUTLINED,
        selected_icon=ft.Icons.SPACE_DASHBOARD,
        title="Panel",
        subtitle="Estado del perfil de vision y de los filtros activos",
    ),
    NavigationDestination(
        route=AppRoute.PICKER,
        label="Selector de color",
        icon=ft.Icons.COLORIZE_OUTLINED,
        selected_icon=ft.Icons.COLORIZE,
        title="Selector de color",
        subtitle="Lupa de pantalla con lectura HEX, RGB y nombre de color",
    ),
    NavigationDestination(
        route=AppRoute.FILTERS,
        label="Filtros",
        icon=ft.Icons.TUNE,
        selected_icon=ft.Icons.TUNE,
        title="Filtros",
        subtitle="Temperatura de color, brillo y contraste para fotofobia",
    ),
    NavigationDestination(
        route=AppRoute.SETTINGS,
        label="Ajustes",
        icon=ft.Icons.SETTINGS_OUTLINED,
        selected_icon=ft.Icons.SETTINGS,
        title="Ajustes",
        subtitle="Preferencias de la aplicacion y gestion de perfiles",
    ),
)

# Ruta inicial al abrir la ventana principal
DEFAULT_ROUTE = AppRoute.DASHBOARD

# Textos de interfaz mantenidos en ASCII para cumplir la regla 3.4 del proyecto
# Cuando se agregue i18n, estos literales se moveran a locales/es.json
UI_TEXT_CORRECTION_ON = "Correccion activa"
UI_TEXT_CORRECTION_OFF = "Correccion en pausa"
UI_TEXT_THEME_LIGHT = "Tema claro"
UI_TEXT_THEME_DARK = "Tema oscuro"
