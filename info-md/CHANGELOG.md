# CHANGELOG — ChromaticVision Desktop

---

## Fase 3 — Selector de color y lupa en vivo — 2026-08-15

### Archivos creados
- `app/picker/__init__.py` — paquete del modulo picker
- `app/picker/color_name_resolver.py` — resolucion de nombre de color por vecino mas cercano en espacio RGB
- `app/picker/color_picker_service.py` — bucle de captura de cursor a 60 FPS en hilo dedicado
- `app/picker/data/color_names.json` — 161 entradas HEX->nombre unicas (CSS/X11 extendido + curado)

### Archivos modificados
- `app/ui/views/picker_view.py` — reescrito para usar el bucle en vivo via `run_task`

### Dependencias agregadas
- ninguna nueva (mss ya instalado desde Fase 1)

### Decisiones arquitectonicas
- El callback del picker nunca toca la UI directamente: agenda `_apply_picker_sample` via `page.run_task()` para respetar el loop de eventos de Flet (mismo patron que la bandeja en Fase 2)
- Se agrego `get_last_cursor_position()` para implementar correctamente el "congelar y copiar" — al hacer clic en el boton el cursor ya se movio, por lo que se usa la ultima posicion observada por el bucle, no la posicion actual
- Posicion del cursor via `ctypes.windll.user32.GetCursorPos` (stdlib puro, sin dependencia nueva), consistente con el enfoque Windows-only del proyecto
- `page.clipboard.set()` en vez de `page.set_clipboard()` — API correcta en Flet 0.86.5
- `ft.Image.src` en vez de `src_base64` — ya corregido desde Fase 1, mantenido

### Limitaciones conocidas
- La lupa muestra la region ampliada sin correccion de color aplicada — la integracion con el motor de correccion queda para la Fase 5 cuando el perfil activo este completamente cableado

---

## Fase 2 — Bandeja del sistema — 2026-08-15

### Archivos creados
- `app/tray/__init__.py` — paquete del modulo tray
- `app/tray/tray_service.py` — ciclo de vida del icono de bandeja con pystray
- `app/tray/tray_menu_actions.py` — manejadores de cada item del menu

### Archivos modificados
- `main.py` — arranque del icono de bandeja en hilo daemon + cierre a bandeja en vez de salir
- `app/ui/main_window.py` — `set_tray_icon()` + sincronizacion del checkmark en `_handle_correction_toggle`

### Dependencias agregadas
- `pystray==0.19.5` — icono y menu de bandeja del sistema en Windows
- `pillow==12.3.0` — generacion programatica del icono de bandeja

### Decisiones arquitectonicas
- `page.window.on_close` no existe en Flet 0.86.x; se usa `page.window.on_event` con `event.type == ft.WindowEventType.CLOSE` y `page.window.prevent_close = True`
- Los clics del menu de pystray llegan en hilo sincrono ajeno al loop de Flet; se usa `page.run_task()` como unico puente thread-safe confirmado
- `handle_exit` llama `icon.stop()` directamente para evitar import circular entre `tray_service` y `tray_menu_actions`
- La ultima matriz de correccion se recuerda en `_current_matrix` dentro de `tray_menu_actions` para reutilizarla al reactivar la correccion desde la bandeja
- El submenu de cambio rapido aplica severidad 1.0 (dicromacia total); el ajuste fino queda en la ventana principal

### Limitaciones conocidas
- Ninguna bloqueante para fases siguientes

---

## Fase 1 — Motor de nucleo — 2026-08-15

### Archivos creados
- `shared-color-science/color_matrix_reference.json` — coeficientes Machado 2009, variantes simulate y correct para los 4 tipos de deficiencia
- `app/core/__init__.py`
- `app/core/color_matrix_engine.py` — construccion, interpolacion y aplicacion de matrices de correccion CVD
- `app/core/screen_capture_service.py` — captura de pantalla completa y region via mss
- `app/core/overlay_renderer.py` — bucle de render en hilo dedicado con queue thread-safe
- `app/core/color_temperature.py` — curva Kelvin (algoritmo Tanner Helland) y shift de temperatura
- `app/profiles/__init__.py`
- `app/profiles/profile_model.py` — dataclass ColorVisionProfile (espejo del esquema JSON Seccion 6.1)
- `app/profiles/profile_service.py` — CRUD de perfiles persistidos como JSON
- `app/profiles/profile_importer.py` — importacion y validacion de esquema con ValueError explicito
- `app/config/app_config.py` — carga y escritura atomica de configuracion local

### Archivos modificados
- `app/ui/main_window.py` — wiring minimo: resumen del panel + arranque/parada del overlay
- `app/ui/views/picker_view.py` — captura estatica en activate() (reemplazada en Fase 3)
- `requirements.txt` — creado con numpy, opencv-python, mss, flet

### Dependencias agregadas
- `numpy` — operaciones matriciales vectorizadas
- `opencv-python` — procesamiento de frames BGR
- `mss` — captura de pantalla de alta velocidad

### Decisiones arquitectonicas
- `apply_color_matrix()` es agnostico de orden de canal; `overlay_renderer` hace la conversion BGR<->RGB
- Matrices de correccion derivadas matematicamente via daltonizacion lineal (Fidaner), no solo literatura
- deuteranomaly/deuteranopia comparten matriz base; la severidad los distingue (interpolacion 0.0-1.0)
- Temperatura de color se combina como matriz diagonal antes de arrancar el hilo de overlay
- Brillo/contraste NO implementados aun — no son operaciones 3x3 puras (pendiente Fase 4/6)
- `ColorVisionProfile` sin campo `id` — el `profile_id` lo gestiona `profile_service` como nombre de archivo

### Limitaciones conocidas
- El overlay sostiene ~10 FPS a 1920x1080 en Python puro, por debajo del objetivo de 30 FPS de la Seccion 4.4. Se abordara en Fase 6 con captura a resolucion reducida tras el build de PyInstaller

---
