# Transforma la ventana principal en la superposicion de pantalla completa
# Se registra como los tres callbacks de overlay_renderer (frame_sink, on_start, on_stop),
# sin importar si la notificacion llega del hilo de bandeja, del hilo de Flet o del hilo
# dedicado de render; todo lo que toca page/page.window se agenda con page.run_task

from typing import Any, Dict, Optional

import flet as ft
import numpy as np

from app.core.screen_capture_service import encode_frame_as_jpeg_base64, get_primary_monitor_size
from app.utils.control_sync import request_update

# Propiedades de ventana que se guardan antes de entrar en modo superposicion y se restauran
_WINDOW_STATE_KEYS = (
    "width",
    "height",
    "left",
    "top",
    "frameless",
    "always_on_top",
    "ignore_mouse_events",
    "skip_task_bar",
)


class OverlayWindowController:
    # Guarda la pagina y el contenido original del shell, todavia sin transformar
    def __init__(self, page: ft.Page, original_content: ft.Control) -> None:
        self.page = page
        self._original_content = original_content
        self._overlay_image: Optional[ft.Image] = None
        self._saved_window_state: Optional[Dict[str, Any]] = None

    # Wrapper sincrono registrable como on_start de overlay_renderer
    def handle_render_start(self) -> None:
        self.page.run_task(self._enter_overlay_mode)

    # Wrapper sincrono registrable como on_stop de overlay_renderer
    def handle_render_stop(self) -> None:
        self.page.run_task(self._exit_overlay_mode)

    # Wrapper sincrono registrable como frame_sink de overlay_renderer
    def handle_frame(self, frame_bgr: np.ndarray) -> None:
        self.page.run_task(self._update_overlay_frame, frame_bgr)

    # Transforma la ventana en una superposicion de pantalla completa, sin bordes y click-through
    async def _enter_overlay_mode(self) -> None:
        window = self.page.window
        self._saved_window_state = {key: getattr(window, key) for key in _WINDOW_STATE_KEYS}
        monitor_width, monitor_height = get_primary_monitor_size()
        window.frameless = True
        window.always_on_top = True
        window.ignore_mouse_events = True
        window.skip_task_bar = True
        window.left = 0
        window.top = 0
        window.width = monitor_width
        window.height = monitor_height
        self._overlay_image = ft.Image(
            src=_build_black_placeholder(monitor_width, monitor_height),
            width=monitor_width,
            height=monitor_height,
            fit=ft.BoxFit.COVER,
            expand=True,
            gapless_playback=True,
        )
        self.page.controls = [self._overlay_image]
        self.page.update()

    # Restaura la ventana a su estado normal, mostrando de nuevo el shell de la aplicacion
    async def _exit_overlay_mode(self) -> None:
        if self._saved_window_state is None:
            return
        window = self.page.window
        for key, value in self._saved_window_state.items():
            setattr(window, key, value)
        self._saved_window_state = None
        self._overlay_image = None
        self.page.controls = [self._original_content]
        self.page.update()

    # Codifica el frame recibido y lo aplica al Image de pantalla completa
    async def _update_overlay_frame(self, frame_bgr: np.ndarray) -> None:
        if self._overlay_image is None:
            return
        try:
            preview_base64 = encode_frame_as_jpeg_base64(frame_bgr)
        except Exception:
            return
        self._overlay_image.src = preview_base64
        request_update(self._overlay_image)


# Genera un placeholder negro del tamano de pantalla para el instante antes del primer frame real
def _build_black_placeholder(width: int, height: int) -> str:
    placeholder = np.zeros((height, width, 3), dtype=np.uint8)
    return encode_frame_as_jpeg_base64(placeholder)
