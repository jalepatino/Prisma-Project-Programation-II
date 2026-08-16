# Vista de filtros: capa independiente de temperatura, brillo y contraste
# Los controles publican su estado en overlay_renderer; la programacion corre en un hilo
# dedicado de filter_scheduler, por lo que sus callbacks se agendan con page.run_task

from datetime import datetime

import flet as ft

from app.config.constants import AppRoute
from app.core import filter_scheduler, overlay_renderer
from app.core.color_matrix_engine import IDENTITY_MATRIX
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

    # Aplica un estado de filtros previamente capturado (por ejemplo, antes de un cambio de tema)
    def set_filter_state(self, state: dict) -> None:
        self._kelvin_slider.value = state["kelvin"]
        self._brightness_slider.value = state["brightness_ceiling"]
        self._contrast_slider.value = state["contrast"]
        self._kelvin_value.value = str(state["kelvin"]) + " K"
        self._brightness_value.value = str(state["brightness_ceiling"]) + " %"
        self._contrast_value.value = str(state["contrast"]) + " %"
        # Solo refleja el valor visual; el hilo del programador sigue su propio ciclo de vida
        self._schedule_switch.value = state["schedule_enabled"]
        request_update(self)

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
            on_change=self._handle_schedule_change,
            tooltip="Activar los filtros automaticamente al anochecer",
        )
        self._schedule_status_label = ft.Text(
            "",
            size=FontSize.CAPTION,
            weight=FontWeight.MEDIUM,
            color=self.palette.text_secondary,
        )
        toggle_row = ft.Row(
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
        body = ft.Column(
            controls=[toggle_row, self._schedule_status_label],
            spacing=Spacing.SPACE_2,
            tight=True,
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

    # Sincroniza la etiqueta de temperatura y publica el nuevo estado en la superposicion
    def _handle_kelvin_change(self, event: ft.ControlEvent) -> None:
        self._kelvin_value.value = str(int(self._kelvin_slider.value)) + " K"
        request_update(self._kelvin_value)
        overlay_renderer.update_filter_state(self.get_filter_state())

    # Sincroniza la etiqueta de brillo y publica el nuevo estado en la superposicion
    def _handle_brightness_change(self, event: ft.ControlEvent) -> None:
        self._brightness_value.value = str(int(self._brightness_slider.value)) + " %"
        request_update(self._brightness_value)
        overlay_renderer.update_filter_state(self.get_filter_state())

    # Sincroniza la etiqueta de contraste y publica el nuevo estado en la superposicion
    def _handle_contrast_change(self, event: ft.ControlEvent) -> None:
        self._contrast_value.value = str(int(self._contrast_slider.value)) + " %"
        request_update(self._contrast_value)
        overlay_renderer.update_filter_state(self.get_filter_state())

    # Arranca o detiene el programador segun el nuevo estado del interruptor
    def _handle_schedule_change(self, event: ft.ControlEvent) -> None:
        if self._schedule_switch.value:
            self._schedule_status_label.value = "Calculando horario..."
            request_update(self._schedule_status_label)
            filter_scheduler.start_schedule_loop(
                self._handle_schedule_activate, self._handle_schedule_deactivate
            )
        else:
            filter_scheduler.stop_schedule_loop()
            self._schedule_status_label.value = ""
            request_update(self._schedule_status_label)

    # Notificado por el programador (hilo dedicado) cuando corresponde activar los filtros
    def _handle_schedule_activate(self) -> None:
        self.page.run_task(self._apply_schedule_active_state)

    # Notificado por el programador (hilo dedicado) cuando corresponde apagar los filtros
    def _handle_schedule_deactivate(self) -> None:
        self.page.run_task(self._apply_schedule_waiting_state)

    # Corrutina agendada en el hilo de la pagina: enciende la capa de filtros y actualiza el estado
    async def _apply_schedule_active_state(self) -> None:
        if not overlay_renderer.is_render_loop_running():
            overlay_renderer.start_render_loop(IDENTITY_MATRIX)
        overlay_renderer.update_filter_state(self.get_filter_state())
        self._schedule_status_label.value = "Activo - filtros encendidos"
        request_update(self._schedule_status_label)

    # Corrutina agendada en el hilo de la pagina: repone valores neutros y muestra la proxima hora
    async def _apply_schedule_waiting_state(self) -> None:
        overlay_renderer.update_filter_state(self._neutral_filter_state())
        self._schedule_status_label.value = "En espera - proxima activacion " + (
            self._describe_next_activation()
        )
        request_update(self._schedule_status_label)

    # Estado de filtros neutro (sin efecto visible) usado al desactivar la programacion
    def _neutral_filter_state(self) -> dict:
        return {
            "kelvin": KELVIN_DEFAULT,
            "brightness_ceiling": BRIGHTNESS_DEFAULT,
            "contrast": CONTRAST_DEFAULT,
            "schedule_enabled": bool(self._schedule_switch.value),
        }

    # Calcula la hora local del proximo ocaso a partir de las coordenadas configuradas
    def _describe_next_activation(self) -> str:
        latitude, longitude = filter_scheduler.get_local_coordinates()
        today = datetime.now().date()
        _, sunset = filter_scheduler.get_sunrise_sunset(latitude, longitude, today)
        return sunset.strftime("%H:%M")
