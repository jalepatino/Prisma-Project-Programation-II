# Vista de filtros: capa independiente de temperatura, brillo y contraste
# Los valores se envian a color_temperature.py cuando exista el bucle de render

import flet as ft

from app.config.constants import AppRoute
from app.ui.components.surface_card import SurfaceCard
from app.ui.theme.design_tokens import (
    FontSize,
    FontWeight,
    Spacing,
)
from app.ui.views.base_view import BaseView
from app.utils.control_sync import request_update

# Rangos y valores neutros iniciales de cada control deslizante
KELVIN_MIN = 2000
KELVIN_MAX = 6500
KELVIN_DEFAULT = 6500
BRIGHTNESS_MIN = 40
BRIGHTNESS_MAX = 100
BRIGHTNESS_DEFAULT = 100
CONTRAST_MIN = 80
CONTRAST_MAX = 130
CONTRAST_DEFAULT = 100


class FiltersView(BaseView):
    route = AppRoute.FILTERS
    title = "Filtros"
    subtitle = "Temperatura de color, brillo y contraste para fotofobia"

    # Compone la tarjeta de ajustes continuos y la tarjeta de programacion
    def build_body(self) -> list:
        return [self._build_sliders_card(), self._build_schedule_card()]

    # Devuelve el estado actual de los filtros para el servicio de superposicion
    def get_filter_state(self) -> dict:
        return {
            "kelvin": int(self._kelvin_slider.value),
            "brightness_ceiling": int(self._brightness_slider.value),
            "contrast": int(self._contrast_slider.value),
            "schedule_enabled": bool(self._schedule_switch.value),
        }

    # Restaura todos los controles a su valor neutro
    def reset_filters(self) -> None:
        self._kelvin_slider.value = KELVIN_DEFAULT
        self._brightness_slider.value = BRIGHTNESS_DEFAULT
        self._contrast_slider.value = CONTRAST_DEFAULT
        self._kelvin_value.value = str(KELVIN_DEFAULT) + " K"
        self._brightness_value.value = str(BRIGHTNESS_DEFAULT) + " %"
        self._contrast_value.value = str(CONTRAST_DEFAULT) + " %"
        request_update(self)

    # Tarjeta con los tres controles deslizantes principales
    def _build_sliders_card(self) -> ft.Control:
        self._kelvin_value = self._build_value_label(str(KELVIN_DEFAULT) + " K")
        self._brightness_value = self._build_value_label(str(BRIGHTNESS_DEFAULT) + " %")
        self._contrast_value = self._build_value_label(str(CONTRAST_DEFAULT) + " %")
        self._kelvin_slider = self._build_slider(
            KELVIN_MIN, KELVIN_MAX, KELVIN_DEFAULT, 45, self._handle_kelvin_change
        )
        self._brightness_slider = self._build_slider(
            BRIGHTNESS_MIN,
            BRIGHTNESS_MAX,
            BRIGHTNESS_DEFAULT,
            60,
            self._handle_brightness_change,
        )
        self._contrast_slider = self._build_slider(
            CONTRAST_MIN, CONTRAST_MAX, CONTRAST_DEFAULT, 50, self._handle_contrast_change
        )
        body = ft.Column(
            controls=[
                self._build_slider_block(
                    "Temperatura de color",
                    "Desplaza la imagen hacia tonos calidos para reducir luz azul",
                    self._kelvin_value,
                    self._kelvin_slider,
                ),
                self._build_slider_block(
                    "Techo de brillo",
                    "Limita el brillo maximo para reducir el deslumbramiento",
                    self._brightness_value,
                    self._brightness_slider,
                ),
                self._build_slider_block(
                    "Contraste global",
                    "Ajusta la separacion entre tonos claros y oscuros",
                    self._contrast_value,
                    self._contrast_slider,
                ),
            ],
            spacing=Spacing.SPACE_6,
            tight=True,
        )
        return SurfaceCard(
            palette=self.palette,
            body=body,
            title="Ajustes continuos",
            subtitle="Capa apilable sobre la matriz de correccion",
        )

    # Tarjeta de programacion automatica basada en calculo local de ocaso
    def _build_schedule_card(self) -> ft.Control:
        self._schedule_switch = ft.Switch(
            value=False,
            active_color=self.palette.accent,
            tooltip="Activar los filtros automaticamente al anochecer",
        )
        body = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(
                            "Activar despues del ocaso",
                            size=FontSize.BODY,
                            weight=FontWeight.MEDIUM,
                            color=self.palette.text_primary,
                        ),
                        ft.Text(
                            "El horario se calcula en local, sin conexion externa",
                            size=FontSize.CAPTION,
                            color=self.palette.text_secondary,
                        ),
                    ],
                    spacing=0,
                    tight=True,
                    expand=True,
                ),
                self._schedule_switch,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=Spacing.SPACE_4,
        )
        return SurfaceCard(
            palette=self.palette,
            body=body,
            title="Programacion",
            subtitle="Automatiza los filtros segun la hora del dia",
        )

    # Etiqueta numerica que acompana a cada control deslizante
    def _build_value_label(self, value: str) -> ft.Text:
        return ft.Text(
            value,
            size=FontSize.CAPTION,
            weight=FontWeight.SEMIBOLD,
            color=self.palette.accent,
            font_family="Consolas",
        )

    # Control deslizante con el color de acento de la paleta activa
    def _build_slider(
        self, minimum: int, maximum: int, value: int, divisions: int, handler
    ) -> ft.Slider:
        return ft.Slider(
            min=minimum,
            max=maximum,
            value=value,
            divisions=divisions,
            active_color=self.palette.accent,
            inactive_color=self.palette.border,
            on_change=handler,
        )

    # Bloque compuesto por titulo, descripcion, valor y control
    def _build_slider_block(
        self, label: str, description: str, value_label: ft.Text, slider: ft.Slider
    ) -> ft.Control:
        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(
                            label,
                            size=FontSize.BODY,
                            weight=FontWeight.MEDIUM,
                            color=self.palette.text_primary,
                            expand=True,
                        ),
                        value_label,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text(
                    description,
                    size=FontSize.CAPTION,
                    color=self.palette.text_secondary,
                ),
                slider,
            ],
            spacing=Spacing.SPACE_1,
            tight=True,
        )

    # Sincroniza la etiqueta de temperatura con la posicion del control
    def _handle_kelvin_change(self, event: ft.ControlEvent) -> None:
        self._kelvin_value.value = str(int(self._kelvin_slider.value)) + " K"
        request_update(self._kelvin_value)

    # Sincroniza la etiqueta de brillo con la posicion del control
    def _handle_brightness_change(self, event: ft.ControlEvent) -> None:
        self._brightness_value.value = str(int(self._brightness_slider.value)) + " %"
        request_update(self._brightness_value)

    # Sincroniza la etiqueta de contraste con la posicion del control
    def _handle_contrast_change(self, event: ft.ControlEvent) -> None:
        self._contrast_value.value = str(int(self._contrast_slider.value)) + " %"
        request_update(self._contrast_value)
