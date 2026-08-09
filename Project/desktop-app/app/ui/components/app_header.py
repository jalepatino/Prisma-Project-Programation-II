# Cabecera superior del shell: contexto de la vista activa y acciones globales
# El estado de correccion se comunica con icono y texto, nunca solo con color

from typing import Callable

import flet as ft

from app.config.constants import (
    HEADER_HEIGHT,
    UI_TEXT_CORRECTION_OFF,
    UI_TEXT_CORRECTION_ON,
    UI_TEXT_THEME_DARK,
    UI_TEXT_THEME_LIGHT,
)
from app.ui.theme.design_tokens import (
    Curve,
    Duration,
    FontSize,
    FontWeight,
    Palette,
    Radius,
    Spacing,
)
from app.utils.control_sync import request_update


class AppHeader(ft.Container):
    # Barra fija de 64px con titulo contextual a la izquierda y controles a la derecha
    def __init__(
        self,
        palette: Palette,
        title: str,
        subtitle: str,
        is_dark_theme: bool,
        on_toggle_theme: Callable[[], None],
        on_toggle_correction: Callable[[bool], None],
        correction_active: bool = False,
    ) -> None:
        super().__init__()
        self.palette = palette
        self.correction_active = correction_active
        self._is_dark_theme = is_dark_theme
        self._on_toggle_theme = on_toggle_theme
        self._on_toggle_correction = on_toggle_correction
        self.height = HEADER_HEIGHT
        self.bgcolor = palette.bg_primary
        self.border = ft.Border.only(bottom=ft.BorderSide(1, palette.border))
        self.padding = ft.Padding.symmetric(horizontal=Spacing.SPACE_6)
        self.content = self._build_content(title, subtitle)
        self._apply_correction_state()

    # Actualiza el titulo y el subtitulo al cambiar de ruta
    def set_view_context(self, title: str, subtitle: str) -> None:
        self._title_text.value = title
        self._subtitle_text.value = subtitle
        request_update(self)

    # Sincroniza el indicador de correccion con el estado real del servicio
    def set_correction_active(self, value: bool) -> None:
        self.correction_active = value
        self._correction_switch.value = value
        self._apply_correction_state()

    # Ensambla el bloque de contexto y el bloque de acciones
    def _build_content(self, title: str, subtitle: str) -> ft.Control:
        self._title_text = ft.Text(
            title,
            size=FontSize.HEADING,
            weight=FontWeight.SEMIBOLD,
            color=self.palette.text_primary,
            no_wrap=True,
        )
        self._subtitle_text = ft.Text(
            subtitle,
            size=FontSize.CAPTION,
            weight=FontWeight.REGULAR,
            color=self.palette.text_secondary,
            no_wrap=True,
        )
        context_block = ft.Column(
            controls=[self._title_text, self._subtitle_text],
            spacing=0,
            tight=True,
            expand=True,
        )
        return ft.Row(
            controls=[context_block, self._build_actions()],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    # Grupo de acciones globales: correccion de color y cambio de tema
    def _build_actions(self) -> ft.Control:
        self._correction_icon = ft.Icon(icon=ft.Icons.REMOVE_RED_EYE_OUTLINED, size=16)
        self._correction_label = ft.Text(
            UI_TEXT_CORRECTION_OFF,
            size=FontSize.CAPTION,
            weight=FontWeight.MEDIUM,
            no_wrap=True,
        )
        self._correction_switch = ft.Switch(
            value=self.correction_active,
            active_color=self.palette.accent,
            on_change=self._handle_correction_change,
            tooltip="Activar o pausar la correccion de color",
        )
        self._correction_chip = ft.Container(
            padding=ft.Padding.only(
                left=Spacing.SPACE_3,
                right=Spacing.SPACE_1,
                top=Spacing.SPACE_1,
                bottom=Spacing.SPACE_1,
            ),
            border_radius=Radius.PILL,
            border=ft.Border.all(1, self.palette.border),
            animate=ft.Animation(Duration.FAST, Curve.STANDARD),
            content=ft.Row(
                controls=[
                    self._correction_icon,
                    self._correction_label,
                    self._correction_switch,
                ],
                spacing=Spacing.SPACE_2,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        self._theme_button = ft.IconButton(
            icon=ft.Icons.LIGHT_MODE_OUTLINED
            if self._is_dark_theme
            else ft.Icons.DARK_MODE_OUTLINED,
            icon_size=18,
            icon_color=self.palette.text_secondary,
            tooltip=(UI_TEXT_THEME_LIGHT if self._is_dark_theme else UI_TEXT_THEME_DARK)
            + " (Ctrl+D)",
            on_click=lambda event: self._on_toggle_theme(),
        )
        return ft.Row(
            controls=[self._correction_chip, self._theme_button],
            spacing=Spacing.SPACE_3,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    # Propaga el cambio del interruptor de correccion al shell
    def _handle_correction_change(self, event: ft.ControlEvent) -> None:
        self.correction_active = bool(self._correction_switch.value)
        self._apply_correction_state()
        self._on_toggle_correction(self.correction_active)

    # Refuerza el estado con icono, texto y borde ademas del color
    def _apply_correction_state(self) -> None:
        if self.correction_active:
            self._correction_icon.icon = ft.Icons.REMOVE_RED_EYE
            self._correction_icon.color = self.palette.accent
            self._correction_label.value = UI_TEXT_CORRECTION_ON
            self._correction_label.color = self.palette.text_primary
            self._correction_chip.border = ft.Border.all(1, self.palette.accent)
        else:
            self._correction_icon.icon = ft.Icons.REMOVE_RED_EYE_OUTLINED
            self._correction_icon.color = self.palette.text_secondary
            self._correction_label.value = UI_TEXT_CORRECTION_OFF
            self._correction_label.color = self.palette.text_secondary
            self._correction_chip.border = ft.Border.all(1, self.palette.border)
        request_update(self)
