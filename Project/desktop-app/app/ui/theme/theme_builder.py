# Traduce los tokens de diseno a objetos nativos de Flet (Theme y TextStyle)
# Ningun componente debe construir un ft.Theme por su cuenta

import flet as ft

from app.ui.theme.design_tokens import (
    FontSize,
    FontWeight,
    LetterSpacing,
    LineHeight,
    Palette,
)

# Familia tipografica principal para la distribucion Windows
FONT_FAMILY_PRIMARY = "Segoe UI"


# Construye el tema global a partir de la paleta activa
def build_theme(palette: Palette) -> ft.Theme:
    return ft.Theme(
        font_family=FONT_FAMILY_PRIMARY,
        color_scheme=_build_color_scheme(palette),
        visual_density=ft.VisualDensity.COMFORTABLE,
        use_material3=True,
    )


# Estilo de titulo destacado; el peso bold se reserva para displays y metricas
def build_display_style(color: str) -> ft.TextStyle:
    return ft.TextStyle(
        size=FontSize.DISPLAY,
        weight=FontWeight.BOLD,
        height=LineHeight.DISPLAY,
        letter_spacing=LetterSpacing.TIGHT,
        color=color,
    )


# Estilo de encabezado de seccion
def build_heading_style(color: str) -> ft.TextStyle:
    return ft.TextStyle(
        size=FontSize.HEADING,
        weight=FontWeight.SEMIBOLD,
        height=LineHeight.HEADING,
        letter_spacing=LetterSpacing.SUBTLE,
        color=color,
    )


# Estilo de cuerpo de texto para bloques de lectura
def build_body_style(color: str) -> ft.TextStyle:
    return ft.TextStyle(
        size=FontSize.BODY,
        weight=FontWeight.REGULAR,
        height=LineHeight.BODY,
        letter_spacing=LetterSpacing.NONE,
        color=color,
    )


# Estilo de texto secundario y captions; sin letter_spacing negativo
def build_caption_style(color: str) -> ft.TextStyle:
    return ft.TextStyle(
        size=FontSize.CAPTION,
        weight=FontWeight.MEDIUM,
        height=LineHeight.CAPTION,
        letter_spacing=LetterSpacing.NONE,
        color=color,
    )


# Mapea la paleta del proyecto al esquema de color que espera Material 3
def _build_color_scheme(palette: Palette) -> ft.ColorScheme:
    return ft.ColorScheme(
        primary=palette.accent,
        on_primary=palette.accent_contrast,
        secondary=palette.accent_hover,
        surface=palette.bg_primary,
        on_surface=palette.text_primary,
        outline=palette.border,
        error=palette.error,
        on_error=palette.accent_contrast,
    )
