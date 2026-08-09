# Tokens de diseno derivados de UI_UX_DESIGN_GUIDELINES.md
# Fuente unica de verdad para espaciado, radios, tipografia, movimiento y color

from dataclasses import dataclass

import flet as ft


# Escala de espaciado base de 4px; prohibido usar valores fuera de esta escala
class Spacing:
    SPACE_1 = 4
    SPACE_2 = 8
    SPACE_3 = 12
    SPACE_4 = 16
    SPACE_5 = 20
    SPACE_6 = 24
    SPACE_8 = 32
    SPACE_10 = 40
    SPACE_12 = 48
    SPACE_16 = 64


# Radios externos permitidos; los radios internos se derivan con derive_inner_radius
class Radius:
    MIN = 2
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    PILL = 999


# Pesos tipograficos; maximo tres pesos distintos por vista
class FontWeight:
    REGULAR = ft.FontWeight.W_400
    MEDIUM = ft.FontWeight.W_500
    SEMIBOLD = ft.FontWeight.W_600
    BOLD = ft.FontWeight.W_700


# Tamanos de fuente segun la tabla de legibilidad de la guia
class FontSize:
    DISPLAY = 32
    HEADING = 20
    SUBHEADING = 17
    BODY = 15
    CAPTION = 13


# Multiplicadores de altura de linea aplicados sobre el tamano de fuente
class LineHeight:
    DISPLAY = 1.15
    HEADING = 1.30
    BODY = 1.55
    CAPTION = 1.45


# Flet expresa letter_spacing en pixeles logicos, no en em
class LetterSpacing:
    TIGHT = -0.6
    SUBTLE = -0.2
    NONE = 0.0


# Duraciones en milisegundos; ventana util de microinteraccion entre 150ms y 300ms
class Duration:
    INSTANT = 100
    FAST = 150
    BASE = 200
    MODERATE = 250
    SLOW = 300


# Curvas organicas; prohibido usar curvas lineales en animaciones perceptibles
class Curve:
    STANDARD = ft.AnimationCurve.EASE_IN_OUT
    DECELERATE = ft.AnimationCurve.EASE_OUT_CUBIC
    ACCELERATE = ft.AnimationCurve.EASE_IN_CUBIC
    SPRING = ft.AnimationCurve.EASE_OUT_BACK


# Valores compartidos de interaccion y accesibilidad de todos los componentes
class Interaction:
    PRESSED_SCALE = 0.96
    DISABLED_OPACITY = 0.45
    FOCUS_RING_WIDTH = 2
    FOCUS_RING_OFFSET = 2
    MIN_TARGET_HEIGHT_DESKTOP = 40
    MIN_TARGET_HEIGHT_TOUCH = 44
    HOVER_TINT_OPACITY = 0.08
    ACTIVE_TINT_OPACITY = 0.14


# Contrato de color consumido por todos los componentes de interfaz
@dataclass(frozen=True)
class Palette:
    name: str
    bg_primary: str
    bg_secondary: str
    bg_elevated: str
    text_primary: str
    text_secondary: str
    border: str
    accent: str
    accent_hover: str
    accent_contrast: str
    error: str
    success: str
    warning: str
    shadow: str


# Paleta clara de referencia de la Seccion 2.3 de la guia de diseno
LIGHT_PALETTE = Palette(
    name="light",
    bg_primary="#FFFFFF",
    bg_secondary="#F5F5F7",
    bg_elevated="#FFFFFF",
    text_primary="#1D1D1F",
    text_secondary="#6E6E73",
    border="#D2D2D7",
    accent="#0071E3",
    accent_hover="#0058B0",
    accent_contrast="#FFFFFF",
    error="#B00020",
    success="#1B7A3D",
    warning="#8A5300",
    shadow="#1F000000",
)

# Paleta oscura de referencia de la Seccion 2.3 de la guia de diseno
DARK_PALETTE = Palette(
    name="dark",
    bg_primary="#000000",
    bg_secondary="#1C1C1E",
    bg_elevated="#141416",
    text_primary="#F5F5F7",
    text_secondary="#98989D",
    border="#38383A",
    accent="#2997FF",
    accent_hover="#5AB0FF",
    accent_contrast="#001A33",
    error="#FF453A",
    success="#30D158",
    warning="#FF9F0A",
    shadow="#66000000",
)


# Resuelve la paleta activa a partir del modo de tema de la pagina
def get_palette(theme_mode: ft.ThemeMode) -> Palette:
    if theme_mode == ft.ThemeMode.DARK:
        return DARK_PALETTE
    return LIGHT_PALETTE


# Devuelve el modo de tema opuesto al actual
def get_opposite_theme_mode(theme_mode: ft.ThemeMode) -> ft.ThemeMode:
    if theme_mode == ft.ThemeMode.DARK:
        return ft.ThemeMode.LIGHT
    return ft.ThemeMode.DARK


# Aplica la formula obligatoria inner_radius = outer_radius - padding
def derive_inner_radius(outer_radius: int, padding: int) -> int:
    derived = outer_radius - padding
    if derived <= 0:
        return Radius.MIN
    return derived
