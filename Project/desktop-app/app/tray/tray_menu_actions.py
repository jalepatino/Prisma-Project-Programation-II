# Manejadores de las acciones del menu de bandeja del sistema
# Cada funcion recibe el icono de pystray como primer argumento

from datetime import datetime, timezone
from typing import Any

import numpy as np

from app.core import overlay_renderer
from app.profiles.profile_model import CURRENT_SCHEMA_VERSION, ColorVisionProfile

# Matriz recordada para poder reactivar la correccion sin volver a elegir un perfil
_current_matrix = np.eye(3, dtype=np.float64)


# Activa o pausa el bucle de superposicion con la ultima matriz conocida; devuelve el nuevo estado
def handle_toggle_correction(icon: Any, correction_active: bool, renderer: Any) -> bool:
    new_state = not correction_active
    if new_state:
        renderer.start_render_loop(_current_matrix)
    else:
        renderer.stop_render_loop()
    return new_state


# Construye la matriz del perfil elegido, la publica y activa la correccion si estaba en pausa
# (un solo clic en el submenu alcanza; antes requeria tambien marcar "Correccion de color")
def handle_switch_profile(
    icon: Any, deficiency_type: str, severity: float, engine: Any, renderer: Any
) -> bool:
    global _current_matrix
    profile = ColorVisionProfile(
        schema_version=CURRENT_SCHEMA_VERSION,
        deficiency_type=deficiency_type,
        severity=severity,
        source="manual",
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
    _current_matrix = engine.build_matrix_for_profile(profile, "correct")
    if renderer.is_render_loop_running():
        renderer.update_active_matrix(_current_matrix)
    else:
        renderer.start_render_loop(_current_matrix)
    return True


# Trae la ventana de Flet al frente, restaurandola si estaba oculta o minimizada
def handle_open_window(icon: Any, page: Any) -> None:
    page.run_task(_show_and_focus_window, page)


# Detiene la superposicion, cierra el icono de bandeja y destruye la ventana de Flet
def handle_exit(icon: Any, page: Any) -> None:
    overlay_renderer.stop_render_loop()
    icon.stop()
    page.run_task(_destroy_window, page)


# Corrutina que restaura visibilidad y foco; se agenda en el hilo de la pagina con run_task
async def _show_and_focus_window(page: Any) -> None:
    page.window.visible = True
    page.window.minimized = False
    await page.window.to_front()
    page.update()


# Corrutina que destruye la ventana nativa; se agenda en el hilo de la pagina con run_task
async def _destroy_window(page: Any) -> None:
    await page.window.destroy()
