# Vista del selector de color: superficie de lupa y lectura de la muestra actual
# El muestreo real lo proveera color_picker_service en la fase 3

import flet as ft

from app.config.constants import AppRoute, TARGET_PICKER_FPS
from app.ui.components.surface_card import SurfaceCard
from app.ui.theme.design_tokens import (
    FontSize,
    FontWeight,
    Radius,
    Spacing,
)
from app.ui.views.base_view import BaseView
from app.utils.control_sync import request_update

# Muestra neutra usada mientras el bucle de captura permanece detenido
IDLE_HEX_VALUE = "#000000"
IDLE_RGB_VALUE = "rgb(0, 0, 0)"
IDLE_COLOR_NAME = "Sin muestra"


class PickerView(BaseView):
    route = AppRoute.PICKER
    title = "Selector de color"
    subtitle = "Lupa de pantalla con lectura HEX, RGB y nombre de color"

    # Compone la superficie de lupa junto al panel de lectura de la muestra
    def build_body(self) -> list:
        return [
            ft.Row(
                controls=[self._build_loupe_card(), self._build_readout_card()],
                spacing=Spacing.SPACE_4,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
        ]

    # Vuelca en la interfaz la muestra entregada por el servicio de captura
    def update_sample(self, hex_value: str, rgb_value: str, color_name: str) -> None:
        self._sample_swatch.bgcolor = hex_value
        self._hex_value.value = hex_value
        self._rgb_value.value = rgb_value
        self._color_name.value = color_name
        self._copy_button.disabled = False
        request_update(self)

    # Reactiva el estado de captura al entrar en la ruta
    def activate(self) -> None:
        super().activate()
        self._status_label.value = "Captura lista a " + str(TARGET_PICKER_FPS) + " FPS"
        request_update(self)

    # Detiene el bucle del picker al abandonar la ruta para liberar CPU
    def deactivate(self) -> None:
        super().deactivate()
        self._status_label.value = "Captura detenida"
        request_update(self)

    # Superficie cuadrada que alojara el render de la lupa
    def _build_loupe_card(self) -> ft.Control:
        card = SurfaceCard(
            palette=self.palette,
            body=ft.Column(tight=True),
            title="Lupa de pantalla",
            subtitle="Region ampliada alrededor del cursor",
            expand=True,
        )
        self._loupe_surface = ft.Container(
            height=280,
            border_radius=card.inner_radius,
            bgcolor=self.palette.bg_secondary,
            border=ft.Border.all(1, self.palette.border),
            alignment=ft.Alignment.CENTER,
            content=ft.Icon(
                icon=ft.Icons.CENTER_FOCUS_WEAK,
                size=32,
                color=self.palette.text_secondary,
            ),
        )
        self._status_label = ft.Text(
            "Captura detenida",
            size=FontSize.CAPTION,
            weight=FontWeight.MEDIUM,
            color=self.palette.text_secondary,
        )
        card.set_body(
            ft.Column(
                controls=[self._loupe_surface, self._status_label],
                spacing=Spacing.SPACE_3,
                tight=True,
            )
        )
        return card

    # Panel lateral con muestra, valores numericos y accion de copiado
    def _build_readout_card(self) -> ft.Control:
        card = SurfaceCard(
            palette=self.palette,
            body=ft.Column(tight=True),
            title="Muestra actual",
            subtitle="Valores del pixel bajo el cursor",
            expand=True,
        )
        self._sample_swatch = ft.Container(
            height=72,
            border_radius=card.inner_radius,
            bgcolor=IDLE_HEX_VALUE,
            border=ft.Border.all(1, self.palette.border),
        )
        self._hex_value = self._build_value_row_text(IDLE_HEX_VALUE)
        self._rgb_value = self._build_value_row_text(IDLE_RGB_VALUE)
        self._color_name = self._build_value_row_text(IDLE_COLOR_NAME)
        self._copy_button = ft.FilledButton(
            content="Copiar HEX",
            icon=ft.Icons.CONTENT_COPY,
            disabled=True,
            style=ft.ButtonStyle(
                bgcolor=self.palette.accent,
                color=self.palette.accent_contrast,
                shape=ft.RoundedRectangleBorder(radius=Radius.SM),
            ),
        )
        card.set_body(
            ft.Column(
                controls=[
                    self._sample_swatch,
                    self._build_value_row("HEX", self._hex_value),
                    self._build_value_row("RGB", self._rgb_value),
                    self._build_value_row("Nombre", self._color_name),
                    self._copy_button,
                ],
                spacing=Spacing.SPACE_3,
                tight=True,
            )
        )
        return card

    # Texto monoespaciado de valor para las lecturas del pixel
    def _build_value_row_text(self, value: str) -> ft.Text:
        return ft.Text(
            value,
            size=FontSize.BODY,
            weight=FontWeight.MEDIUM,
            color=self.palette.text_primary,
            font_family="Consolas",
            no_wrap=True,
        )

    # Fila etiqueta-valor alineada a los extremos de la tarjeta
    def _build_value_row(self, label: str, value_text: ft.Text) -> ft.Control:
        return ft.Row(
            controls=[
                ft.Text(
                    label,
                    size=FontSize.CAPTION,
                    weight=FontWeight.MEDIUM,
                    color=self.palette.text_secondary,
                    expand=True,
                ),
                value_text,
            ],
            spacing=Spacing.SPACE_3,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
