# Vista del selector de color: superficie de lupa y lectura de la muestra actual
# El bucle en vivo lo provee color_picker_service; los callbacks llegan desde su hilo
# dedicado, por lo que toda actualizacion de UI se agenda con page.run_task

import flet as ft

from app.config.constants import AppRoute, TARGET_PICKER_FPS
from app.core.screen_capture_service import encode_frame_as_png_base64
from app.picker import color_picker_service
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

# Tamano de la region capturada alrededor del cursor y objetivo de FPS del bucle en vivo
PICKER_REGION_SIZE = 120


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

    # Arranca el bucle en vivo del picker al entrar en la ruta
    def activate(self) -> None:
        super().activate()
        self._status_label.value = "Muestreando a " + str(TARGET_PICKER_FPS) + " FPS"
        request_update(self)
        color_picker_service.start_picker_loop(
            self._on_picker_tick, region_size=PICKER_REGION_SIZE, fps=TARGET_PICKER_FPS
        )

    # Detiene el bucle del picker al abandonar la ruta y libera la vista previa
    def deactivate(self) -> None:
        super().deactivate()
        color_picker_service.stop_picker_loop()
        self._status_label.value = "Captura detenida"
        self._reset_loupe_to_placeholder()
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
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=self._build_loupe_placeholder(),
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
            on_click=self._handle_copy_click,
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

    # Icono neutro mostrado mientras no hay ninguna vista previa capturada
    def _build_loupe_placeholder(self) -> ft.Control:
        return ft.Icon(
            icon=ft.Icons.CENTER_FOCUS_WEAK,
            size=32,
            color=self.palette.text_secondary,
        )

    # Restaura el icono neutro centrado, deshaciendo el ajuste de alineacion de la imagen
    def _reset_loupe_to_placeholder(self) -> None:
        self._loupe_surface.alignment = ft.Alignment.CENTER
        self._loupe_surface.content = self._build_loupe_placeholder()

    # Callback del hilo dedicado del picker; nunca toca controles directamente desde ahi
    def _on_picker_tick(
        self, hex_value: str, rgb_value: str, color_name: str, frame_region
    ) -> None:
        if not self.is_active:
            return
        self.page.run_task(
            self._apply_picker_sample, hex_value, rgb_value, color_name, frame_region
        )

    # Corrutina agendada en el hilo de la pagina: aplica la muestra recibida sobre la UI
    async def _apply_picker_sample(
        self, hex_value: str, rgb_value: str, color_name: str, frame_region
    ) -> None:
        if not self.is_active:
            return
        self._set_loupe_frame(frame_region)
        self.update_sample(hex_value, rgb_value, color_name)

    # Codifica el frame BGR mas reciente y lo deja listo para el siguiente request_update
    def _set_loupe_frame(self, frame_region) -> None:
        try:
            preview_base64 = encode_frame_as_png_base64(frame_region)
        except Exception:
            return
        # Sin alignment, el contenedor pasa restricciones ajustadas y la imagen llena el area
        self._loupe_surface.alignment = None
        self._loupe_surface.content = ft.Image(src=preview_base64, fit=ft.BoxFit.COVER)

    # Congela la ultima posicion observada por el bucle en vivo y copia su HEX al portapapeles
    async def _handle_copy_click(self, event: ft.ControlEvent) -> None:
        cursor_x, cursor_y = color_picker_service.get_last_cursor_position()
        hex_value, rgb_value = color_picker_service.sample_pixel(cursor_x, cursor_y)
        self.update_sample(hex_value, rgb_value, self._color_name.value)
        await self.page.clipboard.set(hex_value)
