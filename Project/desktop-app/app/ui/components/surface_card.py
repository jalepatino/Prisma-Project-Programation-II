# Tarjeta base reutilizable del sistema de diseno
# Expone inner_radius derivado para que los hijos redondeados no se desalineen

import flet as ft

from app.ui.theme.design_tokens import (
    Curve,
    Duration,
    FontSize,
    FontWeight,
    Palette,
    Radius,
    Spacing,
    derive_inner_radius,
)
from app.utils.control_sync import request_update


class SurfaceCard(ft.Container):
    # Contenedor elevado con encabezado opcional y estado hover cuando es interactivo
    def __init__(
        self,
        palette: Palette,
        body: ft.Control,
        title: str = "",
        subtitle: str = "",
        outer_radius: int = Radius.XL,
        inner_padding: int = Spacing.SPACE_4,
        interactive: bool = False,
        expand: bool = False,
    ) -> None:
        super().__init__(expand=expand)
        self.palette = palette
        self.interactive = interactive
        self.inner_radius = derive_inner_radius(outer_radius, inner_padding)
        self.padding = ft.Padding.all(inner_padding)
        self.border_radius = outer_radius
        self.bgcolor = palette.bg_elevated
        self.border = ft.Border.all(1, palette.border)
        self.animate = ft.Animation(Duration.BASE, Curve.STANDARD)
        self.animate_offset = ft.Animation(Duration.BASE, Curve.STANDARD)
        self.offset = ft.Offset(0, 0)
        self.content = self._build_content(title, subtitle, body)
        if interactive:
            self.on_hover = self._handle_hover
            self.ink = False

    # Reemplaza el cuerpo de la tarjeta conservando el encabezado configurado
    def set_body(self, body: ft.Control) -> None:
        self._body_slot.content = body
        request_update(self._body_slot)

    # Ensambla encabezado opcional y ranura de cuerpo
    def _build_content(self, title: str, subtitle: str, body: ft.Control) -> ft.Control:
        self._body_slot = ft.Container(content=body)
        blocks: list[ft.Control] = []
        if title:
            blocks.append(
                ft.Text(
                    title,
                    size=FontSize.SUBHEADING,
                    weight=FontWeight.SEMIBOLD,
                    color=self.palette.text_primary,
                )
            )
        if subtitle:
            blocks.append(
                ft.Text(
                    subtitle,
                    size=FontSize.CAPTION,
                    weight=FontWeight.REGULAR,
                    color=self.palette.text_secondary,
                )
            )
        blocks.append(self._body_slot)
        return ft.Column(controls=blocks, spacing=Spacing.SPACE_2, tight=True)

    # Elevacion sutil en hover: sombra y desplazamiento vertical minimo
    def _handle_hover(self, event: ft.HoverEvent) -> None:
        is_hovered = event.data == "true"
        self.offset = ft.Offset(0, -0.006) if is_hovered else ft.Offset(0, 0)
        self.border = ft.Border.all(
            1, self.palette.accent if is_hovered else self.palette.border
        )
        self.shadow = (
            ft.BoxShadow(
                blur_radius=24,
                spread_radius=0,
                offset=ft.Offset(0, 8),
                color=self.palette.shadow,
            )
            if is_hovered
            else None
        )
        request_update(self)
