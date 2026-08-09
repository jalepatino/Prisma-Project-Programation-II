# Barra de navegacion lateral del shell principal
# Gestiona seleccion de ruta, foco por teclado y modo compacto

from typing import Callable, Dict, Sequence

import flet as ft

from app.config.constants import (
    APP_NAME,
    APP_TAGLINE,
    APP_VERSION,
    NavigationDestination,
    SIDEBAR_COLLAPSED_WIDTH,
    SIDEBAR_EXPANDED_WIDTH,
)
from app.ui.components.navigation_item import NavigationItem
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


class NavigationSidebar(ft.Container):
    # Panel lateral persistente que actua como unico punto de cambio de ruta
    def __init__(
        self,
        palette: Palette,
        destinations: Sequence[NavigationDestination],
        active_route: str,
        on_route_change: Callable[[str], None],
        on_toggle_collapsed: Callable[[], None],
        collapsed: bool = False,
    ) -> None:
        super().__init__()
        self.palette = palette
        self.destinations = tuple(destinations)
        self.collapsed = collapsed
        self._on_route_change = on_route_change
        self._on_toggle_collapsed = on_toggle_collapsed
        self._items: Dict[str, NavigationItem] = {}
        self._focused_index = -1
        self.width = SIDEBAR_COLLAPSED_WIDTH if collapsed else SIDEBAR_EXPANDED_WIDTH
        self.bgcolor = palette.bg_secondary
        self.border = ft.Border.only(right=ft.BorderSide(1, palette.border))
        self.padding = ft.Padding.symmetric(
            horizontal=Spacing.SPACE_3, vertical=Spacing.SPACE_4
        )
        self.animate = ft.Animation(Duration.MODERATE, Curve.DECELERATE)
        self.content = self._build_content()
        self.select_route(active_route)

    # Marca visualmente la ruta activa y desmarca el resto de destinos
    def select_route(self, route: str) -> None:
        for item_route, item in self._items.items():
            item.set_selected(item_route == route)

    # Desplaza el anillo de foco entre destinos con las flechas del teclado
    def move_focus(self, step: int) -> None:
        total = len(self.destinations)
        if total == 0:
            return
        self._focused_index = (self._focused_index + step) % total
        for index, destination in enumerate(self.destinations):
            self._items[destination.route].set_focused(index == self._focused_index)

    # Activa el destino que tiene el foco de teclado
    def activate_focused_item(self) -> None:
        if 0 <= self._focused_index < len(self.destinations):
            self._on_route_change(self.destinations[self._focused_index].route)

    # Retira el anillo de foco de todos los destinos
    def clear_focus(self) -> None:
        self._focused_index = -1
        for item in self._items.values():
            item.set_focused(False)

    # Alterna entre el ancho expandido y el compacto de 72px
    def set_collapsed(self, value: bool) -> None:
        self.collapsed = value
        self.width = SIDEBAR_COLLAPSED_WIDTH if value else SIDEBAR_EXPANDED_WIDTH
        self._brand_labels.visible = not value
        self._section_label.visible = not value
        self._version_label.visible = not value
        self._collapse_button.icon = (
            ft.Icons.KEYBOARD_DOUBLE_ARROW_RIGHT
            if value
            else ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT
        )
        for item in self._items.values():
            item.set_collapsed(value)
        request_update(self)

    # Ensambla marca, lista de destinos y pie de la barra
    def _build_content(self) -> ft.Control:
        return ft.Column(
            controls=[
                self._build_brand(),
                ft.Container(height=Spacing.SPACE_6),
                self._build_destination_list(),
                self._build_footer(),
            ],
            spacing=Spacing.SPACE_2,
            expand=True,
        )

    # Bloque de identidad de producto en la cabecera de la barra
    def _build_brand(self) -> ft.Control:
        logo = ft.Container(
            width=32,
            height=32,
            border_radius=Radius.SM,
            bgcolor=self.palette.accent,
            alignment=ft.Alignment.CENTER,
            content=ft.Icon(
                icon=ft.Icons.VISIBILITY,
                size=18,
                color=self.palette.accent_contrast,
            ),
        )
        self._brand_labels = ft.Column(
            controls=[
                ft.Text(
                    APP_NAME,
                    size=FontSize.BODY,
                    weight=FontWeight.SEMIBOLD,
                    color=self.palette.text_primary,
                    no_wrap=True,
                ),
                ft.Text(
                    APP_TAGLINE,
                    size=FontSize.CAPTION,
                    weight=FontWeight.REGULAR,
                    color=self.palette.text_secondary,
                    no_wrap=True,
                ),
            ],
            spacing=0,
            tight=True,
            expand=True,
            visible=not self.collapsed,
        )
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=Spacing.SPACE_2),
            content=ft.Row(
                controls=[logo, self._brand_labels],
                spacing=Spacing.SPACE_3,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    # Lista vertical de destinos generada desde las constantes de navegacion
    def _build_destination_list(self) -> ft.Control:
        self._section_label = ft.Container(
            padding=ft.Padding.only(left=Spacing.SPACE_2, bottom=Spacing.SPACE_2),
            visible=not self.collapsed,
            content=ft.Text(
                "NAVEGACION",
                size=11,
                weight=FontWeight.SEMIBOLD,
                color=self.palette.text_secondary,
            ),
        )
        controls: list[ft.Control] = [self._section_label]
        for destination in self.destinations:
            item = NavigationItem(
                route=destination.route,
                label=destination.label,
                icon=destination.icon,
                selected_icon=destination.selected_icon,
                palette=self.palette,
                on_select=self._handle_item_selected,
                collapsed=self.collapsed,
            )
            self._items[destination.route] = item
            controls.append(item)
        return ft.Column(controls=controls, spacing=Spacing.SPACE_1, expand=True)

    # Pie con el control de colapso y la version instalada
    def _build_footer(self) -> ft.Control:
        self._collapse_button = ft.IconButton(
            icon=(
                ft.Icons.KEYBOARD_DOUBLE_ARROW_RIGHT
                if self.collapsed
                else ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT
            ),
            icon_size=18,
            icon_color=self.palette.text_secondary,
            tooltip="Contraer barra lateral (Ctrl+B)",
            on_click=lambda event: self._on_toggle_collapsed(),
        )
        self._version_label = ft.Text(
            "v" + APP_VERSION,
            size=FontSize.CAPTION,
            weight=FontWeight.REGULAR,
            color=self.palette.text_secondary,
            visible=not self.collapsed,
            expand=True,
        )
        return ft.Container(
            padding=ft.Padding.only(top=Spacing.SPACE_3),
            border=ft.Border.only(top=ft.BorderSide(1, self.palette.border)),
            content=ft.Row(
                controls=[self._version_label, self._collapse_button],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    # Propaga la seleccion al shell y sincroniza el indice de foco
    def _handle_item_selected(self, route: str) -> None:
        for index, destination in enumerate(self.destinations):
            if destination.route == route:
                self._focused_index = index
        self._on_route_change(route)
