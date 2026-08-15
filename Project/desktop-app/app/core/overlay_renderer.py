# Bucle de renderizado de la superposicion de correccion en un hilo dedicado
# Dos colas sincronizan matriz y estado de filtros sin bloquear el hilo de UI de Flet
# El filtro de temperatura/brillo/contraste se apila DESPUES de la matriz de correccion CVD

import queue
import threading
import time
from typing import Callable, Dict, Optional

import cv2
import numpy as np

from app.config.constants import TARGET_OVERLAY_FPS
from app.core.color_matrix_engine import apply_color_matrix
from app.core.color_temperature import apply_temperature_shift
from app.core.screen_capture_service import capture_frame

# Callback invocado con cada frame ya corregido, en formato BGR
FrameSink = Callable[[np.ndarray], None]

_render_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()
_matrix_queue: "queue.Queue[np.ndarray]" = queue.Queue()
_filter_state_queue: "queue.Queue[Dict[str, int]]" = queue.Queue()
_active_matrix: Optional[np.ndarray] = None
_active_filter_state: Optional[Dict[str, int]] = None


# Arranca el hilo de renderizado con la matriz inicial y un destino de frame opcional
def start_render_loop(
    initial_matrix: np.ndarray, frame_sink: Optional[FrameSink] = None
) -> None:
    global _render_thread, _active_matrix
    if _render_thread is not None and _render_thread.is_alive():
        return
    _active_matrix = initial_matrix
    _stop_event.clear()
    _render_thread = threading.Thread(
        target=_run_render_loop, args=(frame_sink,), daemon=True
    )
    _render_thread.start()


# Senala el cierre limpio del hilo de renderizado y espera su finalizacion
def stop_render_loop() -> None:
    global _render_thread
    _stop_event.set()
    if _render_thread is not None:
        _render_thread.join(timeout=2.0)
    _render_thread = None


# Publica una nueva matriz activa en la cola sin bloquear al emisor
def update_active_matrix(matrix: np.ndarray) -> None:
    _matrix_queue.put_nowait(matrix)


# Publica un nuevo estado de filtros (temperatura, techo de brillo, contraste) sin bloquear
def update_filter_state(state: Dict[str, int]) -> None:
    _filter_state_queue.put_nowait(state)


# Indica si el hilo de renderizado esta activo en este momento
def is_render_loop_running() -> bool:
    return _render_thread is not None and _render_thread.is_alive()


# Bucle interno del hilo dedicado: captura, corrige, aplica filtros y entrega cada frame
def _run_render_loop(frame_sink: Optional[FrameSink]) -> None:
    global _active_matrix, _active_filter_state
    frame_budget_seconds = 1.0 / TARGET_OVERLAY_FPS
    while not _stop_event.is_set():
        loop_started_at = time.perf_counter()
        _active_matrix = _drain_matrix_queue(_active_matrix)
        _active_filter_state = _drain_filter_state_queue(_active_filter_state)
        corrected_frame = _capture_and_correct(_active_matrix)
        corrected_frame = _apply_filter_layer(corrected_frame, _active_filter_state)
        if frame_sink is not None:
            frame_sink(corrected_frame)
        _sleep_for_remaining_budget(loop_started_at, frame_budget_seconds)


# Captura un frame BGR y aplica la matriz activa convirtiendo temporalmente a espacio RGB
def _capture_and_correct(matrix: Optional[np.ndarray]) -> np.ndarray:
    frame_bgr = capture_frame()
    if matrix is None:
        return frame_bgr
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    corrected_rgb = apply_color_matrix(frame_rgb, matrix)
    return cv2.cvtColor(corrected_rgb, cv2.COLOR_RGB2BGR)


# Vacia la cola de matrices pendientes y devuelve la mas reciente disponible
def _drain_matrix_queue(current_matrix: Optional[np.ndarray]) -> Optional[np.ndarray]:
    latest = current_matrix
    while True:
        try:
            latest = _matrix_queue.get_nowait()
        except queue.Empty:
            break
    return latest


# Vacia la cola de estados de filtro pendientes y devuelve el mas reciente disponible
def _drain_filter_state_queue(
    current_state: Optional[Dict[str, int]],
) -> Optional[Dict[str, int]]:
    latest = current_state
    while True:
        try:
            latest = _filter_state_queue.get_nowait()
        except queue.Empty:
            break
    return latest


# Aplica temperatura, techo de brillo y contraste como capa apilable tras la correccion CVD
def _apply_filter_layer(frame_bgr: np.ndarray, filter_state: Optional[Dict[str, int]]) -> np.ndarray:
    if filter_state is None:
        return frame_bgr
    warmed = apply_temperature_shift(frame_bgr, filter_state["kelvin"])
    return _apply_brightness_contrast(
        warmed, filter_state["brightness_ceiling"], filter_state["contrast"]
    )


# Escala el brillo maximo y ajusta el contraste alrededor del punto medio, con recorte 0-255
def _apply_brightness_contrast(
    frame: np.ndarray, brightness_ceiling: int, contrast: int
) -> np.ndarray:
    working = frame.astype(np.float64) * (brightness_ceiling / 100.0)
    contrast_factor = contrast / 100.0
    working = (working - 127.5) * contrast_factor + 127.5
    clipped = np.clip(working, 0, 255)
    return clipped.astype(frame.dtype)


# Duerme el tiempo restante del presupuesto de frame para respetar el FPS objetivo
def _sleep_for_remaining_budget(loop_started_at: float, frame_budget_seconds: float) -> None:
    elapsed = time.perf_counter() - loop_started_at
    remaining = frame_budget_seconds - elapsed
    if remaining > 0:
        time.sleep(remaining)
