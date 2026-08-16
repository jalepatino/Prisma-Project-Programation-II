# Bucle de renderizado de la superposicion de correccion en un hilo dedicado
# Dos colas sincronizan matriz y estado de filtros sin bloquear el hilo de UI de Flet
# El filtro de temperatura/brillo/contraste se apila DESPUES de la matriz de correccion CVD
#
# Presupuesto de rendimiento (medido, ver CHANGELOG Fase 6): a 1920x1080 el pipeline
# completo (captura + matriz + temperatura + brillo/contraste) cuesta ~300ms/frame en
# Python puro, muy por debajo del objetivo de 30 FPS. El calculo pesado se hace sobre
# una copia reducida del frame (RENDER_SCALE_FACTOR) y el resultado se reescala al
# tamano original antes de entregarlo; la captura de mss sigue siendo a resolucion
# completa porque mss no admite reescalar durante la captura

import queue
import threading
import time
from typing import Callable, Dict, Optional, Tuple

import cv2
import numpy as np

from app.config.constants import TARGET_OVERLAY_FPS
from app.core.color_matrix_engine import apply_color_matrix
from app.core.color_temperature import apply_temperature_shift
from app.core.screen_capture_service import capture_frame
from app.utils.logger import get_logger

_logger = get_logger(__name__)

# Callback invocado con cada frame ya corregido, en formato BGR y en resolucion completa
FrameSink = Callable[[np.ndarray], None]

# Callbacks invocados una vez por cada transicion real de arranque/parada del hilo
LifecycleCallback = Callable[[], None]

# Fraccion del tamano capturado usada para el calculo de color; 0.5 en un monitor
# 1920x1080 equivale a procesar a 960x540, reduciendo a un cuarto los pixeles por frame
RENDER_SCALE_FACTOR = 0.5

_render_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()
_matrix_queue: "queue.Queue[np.ndarray]" = queue.Queue()
_filter_state_queue: "queue.Queue[Dict[str, int]]" = queue.Queue()
_active_matrix: Optional[np.ndarray] = None
_active_filter_state: Optional[Dict[str, int]] = None

# Registro global: quien muestra los frames y quien reacciona a arranque/parada.
# Se registra una sola vez al iniciar la app (main.py); start_render_loop se
# invoca desde tres lugares distintos (bandeja, cabecera, programador) que no
# necesitan saber nada de la ventana ni de como se muestra el resultado
_frame_sink: Optional[FrameSink] = None
_on_start: Optional[LifecycleCallback] = None
_on_stop: Optional[LifecycleCallback] = None


# Registra el destino que recibe cada frame corregido; reemplaza cualquier registro previo
def set_frame_sink(frame_sink: Optional[FrameSink]) -> None:
    global _frame_sink
    _frame_sink = frame_sink


# Registra los callbacks de arranque/parada del hilo; reemplaza cualquier registro previo
def set_lifecycle_callbacks(
    on_start: Optional[LifecycleCallback], on_stop: Optional[LifecycleCallback]
) -> None:
    global _on_start, _on_stop
    _on_start = on_start
    _on_stop = on_stop


# Arranca el hilo de renderizado con la matriz inicial; notifica al callback de arranque
def start_render_loop(initial_matrix: np.ndarray) -> None:
    global _render_thread, _active_matrix
    if _render_thread is not None and _render_thread.is_alive():
        return
    _active_matrix = initial_matrix
    _stop_event.clear()
    _render_thread = threading.Thread(target=_run_render_loop, daemon=True)
    _render_thread.start()
    if _on_start is not None:
        _on_start()


# Senala el cierre limpio del hilo de renderizado, espera su finalizacion y notifica la parada
def stop_render_loop() -> None:
    global _render_thread
    was_running = _render_thread is not None and _render_thread.is_alive()
    _stop_event.set()
    if _render_thread is not None:
        _render_thread.join(timeout=2.0)
    _render_thread = None
    if was_running and _on_stop is not None:
        _on_stop()


# Publica una nueva matriz activa en la cola sin bloquear al emisor
def update_active_matrix(matrix: np.ndarray) -> None:
    _matrix_queue.put_nowait(matrix)


# Publica un nuevo estado de filtros (temperatura, techo de brillo, contraste) sin bloquear
def update_filter_state(state: Dict[str, int]) -> None:
    _filter_state_queue.put_nowait(state)


# Indica si el hilo de renderizado esta activo en este momento
def is_render_loop_running() -> bool:
    return _render_thread is not None and _render_thread.is_alive()


# Bucle interno del hilo dedicado: captura, reduce, corrige, filtra y reescala cada frame
def _run_render_loop() -> None:
    global _active_matrix, _active_filter_state
    frame_budget_seconds = 1.0 / TARGET_OVERLAY_FPS
    while not _stop_event.is_set():
        loop_started_at = time.perf_counter()
        try:
            _active_matrix = _drain_matrix_queue(_active_matrix)
            _active_filter_state = _drain_filter_state_queue(_active_filter_state)
            frame_bgr = capture_frame()
            original_size = (frame_bgr.shape[1], frame_bgr.shape[0])
            working_frame = _resize_to_scale(frame_bgr, RENDER_SCALE_FACTOR)
            working_frame = _apply_correction_matrix(working_frame, _active_matrix)
            working_frame = _apply_filter_layer(working_frame, _active_filter_state)
            final_frame = _resize_to(working_frame, original_size)
            if _frame_sink is not None:
                _frame_sink(final_frame)
        except Exception:
            _logger.exception("Fallo un frame del bucle de renderizado de la superposicion")
        _sleep_for_remaining_budget(loop_started_at, frame_budget_seconds)


# Reduce un frame BGR a una fraccion de su tamano, para abaratar el resto del pipeline
def _resize_to_scale(frame_bgr: np.ndarray, scale_factor: float) -> np.ndarray:
    height, width = frame_bgr.shape[:2]
    target_size = (max(1, int(width * scale_factor)), max(1, int(height * scale_factor)))
    return cv2.resize(frame_bgr, target_size, interpolation=cv2.INTER_LINEAR)


# Reescala un frame BGR al tamano exacto indicado (usado para volver a la resolucion original)
def _resize_to(frame_bgr: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
    return cv2.resize(frame_bgr, target_size, interpolation=cv2.INTER_LINEAR)


# Aplica la matriz de correccion activa convirtiendo temporalmente a espacio RGB
def _apply_correction_matrix(frame_bgr: np.ndarray, matrix: Optional[np.ndarray]) -> np.ndarray:
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
