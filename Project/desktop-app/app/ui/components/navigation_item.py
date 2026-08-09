# Item individual de la barra de navegacion lateral
# Implementa los seis estados obligatorios: default, hover, active, focused, disabled y loading

from typing import Callable, Optional

import flet as ft

from app.ui.theme.design_tokens import (
    Curve,
    Duration,
    FontSize,
    FontWeight,
    Interaction,
    Palette,
    Radius,
    Spacing,
)
from app.utils.control_sync import request_update


class NavigationItem(ft.GestureDetector):
    # Destino navegable con indicador de forma, no solo de color, para usuarios con CVD
    def __init__(
        self,
        route: str,
        label: str,
        icon: str,
        selected_icon: str,
        palette: Palette,
        on_select: Callable[[str], None],
        collapsed: bool = False,
        disabled: bool = False,
    ) -> None:
        super().__init__(
            mouse_cursor=ft.MouseCursor.CLICK,
            on_tap=self._handle_tap,
            on_tap_down=self._handle_tap_down,
            on_tap_up=self._handle_tap_up,
            on_enter=self._handle_enter,
            on_exit=self._handle_exit,
        )
        self.route = route
        self.item_label = label
        self.palette = palette
        self.disabled = disabled
        self._icon_name = icon
        self._selected_icon_name = selected_icon
        self._on_select = on_select
        self._selected = False
        self._hovered = False
        self._pressed = False
        self._focused = False
        self._loading = False
        self._collapsed = collapsed
        self.content = self._build_surface()
        self._apply_visual_state()

    # Marca el item como destino activo del router
    def set_selected(self, value: bool) -> None:
        self._selected = value
        self._apply_visual_state()

    # Muestra el anillo de foco cuando el item recibe navegacion por teclado
    def set_focused(self, value: bool) -> None:
        self._focused = value
        self._apply_visual_state()

    # Bloquea el item y muestra un indicador de progreso en linea
    def set_loading(self, value: bool) -> None:
        self._loading = value
        self._apply_visual_state()

    # Alterna el modo compacto ocultando la etiqueta y activando el tooltip
    def set_collapsed(self, value: bool) -> None:
        self._collapsed = value
        self._label_text.visible = not value
        self.tooltip = self.item_label if value else None
        self._apply_visual_state()

    # Construye la superficie visual del item una sola vez
    def _build_surface(self) -> ft.Container:
        self._indicator = ft.Container(
            width=3,
            height=18,
            border_radius=Radius.PILL,
            bgcolor=ft.Colors.TRANSPARENT,
            animate=ft.Animation(Duration.FAST, Curve.STANDARD),
        )
        self._icon = ft.Icon(icon=self._icon_name, size=20)
        self._label_text = ft.Text(
            self.item_label,
            size=FontSize.BODY,
            weight=FontWeight.MEDIUM,
            no_wrap=True,
            expand=True,
            visible=not self._collapsed,
        )
        self._progress = ft.ProgressRing(
            width=14,
            height=14,
            stroke_width=2,
            color=self.palette.accent,
            visible=False,
        )
        return ft.Container(
            content=ft.Row(
                controls=[self._indicator, self._icon, self._label_text, self._progress],
                spacing=Spacing.SPACE_3,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            height=Interaction.MIN_TARGET_HEIGHT_DESKTOP,
            padding=ft.Padding.symmetric(horizontal=Spacing.SPACE_2),
            border_radius=Radius.MD,
            bgcolor=ft.Colors.TRANSPARENT,
            border=ft.Border.all(Interaction.FOCUS_RING_WIDTH, ft.Colors.TRANSPARENT),
            scale=1.0,
            animate=ft.Animation(Duration.FAST, Curve.STANDARD),
            animate_scale=ft.Animation(Duration.FAST, Curve.SPRING),
        )

    # Notifica la seleccion al contenedor padre si el item esta operativo
    def _handle_tap(self, event: ft.TapEvent) -> None:
        if self.disabled or self._loading:
            return
        self._on_select(self.route)

    # Retroalimentacion tactil de presion mediante reduccion de escala
    def _handle_tap_down(self, event: ft.TapEvent) -> None:
        self._pressed = True
        self._apply_visual_state()

    # Restaura la escala al soltar la pulsacion
    def _handle_tap_up(self, event: ft.TapEvent) -> None:
        self._pressed = False
        self._apply_visual_state()

    # Activa el estado hover al entrar el cursor
    def _handle_enter(self, event: ft.HoverEvent) -> None:
        self._hovered = True
        self._apply_visual_state()

    # Limpia hover y presion al salir el cursor del area
    def _handle_exit(self, event: ft.HoverEvent) -> None:
        self._hovered = False
        self._pressed = False
        self._apply_visual_state()

    # Resuelve todos los estados visuales en un unico punto y sincroniza la UI
    def _apply_visual_state(self) -> None:
        surface: ft.Container = self.content
        is_emphasized = self._selected or self._hovered
        content_color = self._resolve_content_color()
        self._indicator.bgcolor = (
            self.palette.accent if self._selected else ft.Colors.TRANSPARENT
        )
        self._icon.icon = (
            self._selected_icon_name if self._selected else self._icon_name
        )
        self._icon.color = content_color
        self._label_text.color = content_color
        self._label_text.weight = (
            FontWeight.SEMIBOLD if self._selected else FontWeight.MEDIUM
        )
        self._progress.visible = self._loading
        surface.bgcolor = self._resolve_background_color()
        surface.border = ft.Border.all(
            Interaction.FOCUS_RING_WIDTH,
            self.palette.accent if self._focused else ft.Colors.TRANSPARENT,
        )
        surface.scale = (
            Interaction.PRESSED_SCALE if self._pressed and not self.disabled else 1.0
        )
        surface.opacity = (
            Interaction.DISABLED_OPACITY if self.disabled or self._loading else 1.0
        )
        self.mouse_cursor = (
            ft.MouseCursor.FORBIDDEN if self.disabled else ft.MouseCursor.CLICK
        )
        if is_emphasized:
            self.tooltip = self.item_label if self._collapsed else None
        request_update(self)

    # Color de icono y etiqueta segun jerarquia de enfasis
    def _resolve_content_color(self) -> str:
        if self._selected:
            return self.palette.accent
        if self._hovered:
            return self.palette.text_primary
        return self.palette.text_secondary

    # Fondo del item: tinte de acento cuando esta activo, tinte neutro en hover
    def _resolve_background_color(self) -> Optional[str]:
        if self._selected:
            return ft.Colors.with_opacity(
                Interaction.ACTIVE_TINT_OPACITY, self.palette.accent
            )
        if self._hovered and not self.disabled:
            return ft.Colors.with_opacity(
                Interaction.HOVER_TINT_OPACITY, self.palette.text_primary
            )
        return ft.Colors.TRANSPARENT
