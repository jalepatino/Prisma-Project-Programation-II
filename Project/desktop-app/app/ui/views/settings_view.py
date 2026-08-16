# Vista de ajustes: preferencias de la aplicacion y gestion del perfil de vision
# Las preferencias se persisten en cada cambio via app_config; el perfil se
# importa/exporta como JSON siguiendo el esquema compartido de la Seccion 6.1

import dataclasses
import json
from typing import Callable, Optional

import flet as ft

from app.config.app_config import load_config, save_config
from app.config.constants import APP_NAME, APP_VERSION, AppRoute
from app.profiles.profile_importer import import_profile_from_json
from app.profiles.profile_model import ColorVisionProfile
from app.profiles.profile_service import create_profile, get_profile
from app.ui.components.surface_card import SurfaceCard
from app.ui.theme.design_tokens import (
    FontSize,
    FontWeight,
    Palette,
    Radius,
    Spacing,
)
from app.ui.views.base_view import BaseView
from app.utils.control_sync import request_update

# Opciones fijas del selector de arranque de la aplicacion
STARTUP_OPTIONS = ("Ventana principal", "Solo bandeja del sistema")

# Identificador fijo bajo el cual se persiste el unico perfil activo del escritorio
ACTIVE_PROFILE_ID = "active"


class SettingsView(BaseView):
    route = AppRoute.SETTINGS
    title = "Ajustes"
    subtitle = "Preferencias de la aplicacion y gestion de perfiles"

    # Inicializa el callback de perfil antes de que build_body construya los controles
    def __init__(self, palette: Palette) -> None:
        self._on_profile_changed: Optional[Callable[[ColorVisionProfile], None]] = None
        super().__init__(palette)

    # Compone las tarjetas de comportamiento, perfil e informacion
    def build_body(self) -> list:
        return [
            self._build_behavior_card(),
            self._build_profile_card(),
            self._build_about_card(),
        ]

    # Devuelve las preferencias actuales para persistirlas en el archivo local
    def get_preferences(self) -> dict:
        return {
            "start_minimized": bool(self._tray_switch.value),
            "launch_on_startup": bool(self._autostart_switch.value),
            "startup_target": self._startup_dropdown.value,
        }

    # Aplica preferencias previamente capturadas (por ejemplo, antes de un cambio de tema)
    def set_preferences(self, preferences: dict) -> None:
        self._tray_switch.value = bool(preferences.get("start_minimized", True))
        self._autostart_switch.value = bool(preferences.get("launch_on_startup", False))
        self._startup_dropdown.value = preferences.get("startup_target", STARTUP_OPTIONS[0])
        request_update(self)

    # Vincula el callback que MainWindow usa para reaccionar a un perfil recien importado
    def set_profile_changed_callback(self, callback: Callable[[ColorVisionProfile], None]) -> None:
        self._on_profile_changed = callback

    # Restaura las preferencias guardadas cada vez que se entra en la ruta de ajustes
    def activate(self) -> None:
        super().activate()
        config = load_config()
        self._tray_switch.value = bool(config.get("start_minimized", True))
        self._autostart_switch.value = bool(config.get("launch_on_startup", False))
        self._startup_dropdown.value = config.get("startup_target", STARTUP_OPTIONS[0])
        request_update(self)

    # Tarjeta de comportamiento de arranque y persistencia en bandeja
    def _build_behavior_card(self) -> ft.Control:
        self._tray_switch = ft.Switch(
            value=True, active_color=self.palette.accent, on_change=self._handle_preference_change
        )
        self._autostart_switch = ft.Switch(
            value=False, active_color=self.palette.accent, on_change=self._handle_preference_change
        )
        self._startup_dropdown = ft.Dropdown(
            value=STARTUP_OPTIONS[0],
            options=[ft.dropdown.Option(option) for option in STARTUP_OPTIONS],
            width=240,
            border_color=self.palette.border,
            focused_border_color=self.palette.accent,
            text_size=FontSize.BODY,
            on_select=self._handle_preference_change,
        )
        body = ft.Column(
            controls=[
                self._build_setting_row(
                    "Mantener en bandeja al cerrar",
                    "La correccion sigue activa aunque se cierre la ventana",
                    self._tray_switch,
                ),
                self._build_setting_row(
                    "Iniciar con el sistema",
                    "Registra la aplicacion en el arranque de Windows",
                    self._autostart_switch,
                ),
                self._build_setting_row(
                    "Vista al iniciar",
                    "Define que se muestra al abrir la aplicacion",
                    self._startup_dropdown,
                ),
            ],
            spacing=Spacing.SPACE_5,
            tight=True,
        )
        return SurfaceCard(
            palette=self.palette,
            body=body,
            title="Comportamiento",
            subtitle="Arranque y persistencia en segundo plano",
        )

    # Tarjeta de importacion y exportacion del perfil de vision compartido
    def _build_profile_card(self) -> ft.Control:
        self._file_picker = ft.FilePicker()
        body = ft.Column(
            controls=[
                ft.Text(
                    "El perfil generado en la plataforma web se importa aqui como "
                    "archivo JSON y define la matriz de correccion aplicada.",
                    size=FontSize.BODY,
                    color=self.palette.text_secondary,
                ),
                ft.Row(
                    controls=[
                        ft.FilledButton(
                            content="Importar perfil",
                            icon=ft.Icons.FILE_DOWNLOAD_OUTLINED,
                            on_click=self._handle_import_click,
                            style=ft.ButtonStyle(
                                bgcolor=self.palette.accent,
                                color=self.palette.accent_contrast,
                                shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                            ),
                        ),
                        ft.OutlinedButton(
                            content="Exportar perfil",
                            icon=ft.Icons.FILE_UPLOAD_OUTLINED,
                            on_click=self._handle_export_click,
                            style=ft.ButtonStyle(
                                color=self.palette.text_primary,
                                shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                            ),
                        ),
                    ],
                    spacing=Spacing.SPACE_3,
                ),
            ],
            spacing=Spacing.SPACE_4,
            tight=True,
        )
        return SurfaceCard(
            palette=self.palette,
            body=body,
            title="Perfil de vision",
            subtitle="Interoperabilidad con la plataforma web",
        )

    # Tarjeta informativa con version y alcance del producto
    def _build_about_card(self) -> ft.Control:
        body = ft.Column(
            controls=[
                ft.Text(
                    APP_NAME + " " + APP_VERSION,
                    size=FontSize.BODY,
                    weight=FontWeight.MEDIUM,
                    color=self.palette.text_primary,
                ),
                ft.Text(
                    "Correccion de color para deuteranopia y tritanopia, mas filtros "
                    "de temperatura y contraste para fotofobia.",
                    size=FontSize.CAPTION,
                    color=self.palette.text_secondary,
                ),
            ],
            spacing=Spacing.SPACE_1,
            tight=True,
        )
        return SurfaceCard(palette=self.palette, body=body, title="Acerca de")

    # Fila estandar de ajuste con etiqueta, descripcion y control a la derecha
    def _build_setting_row(
        self, label: str, description: str, control: ft.Control
    ) -> ft.Control:
        return ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(
                            label,
                            size=FontSize.BODY,
                            weight=FontWeight.MEDIUM,
                            color=self.palette.text_primary,
                        ),
                        ft.Text(
                            description,
                            size=FontSize.CAPTION,
                            color=self.palette.text_secondary,
                        ),
                    ],
                    spacing=0,
                    tight=True,
                    expand=True,
                ),
                control,
            ],
            spacing=Spacing.SPACE_4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    # Persiste las preferencias vigentes cada vez que cambia un interruptor o el desplegable
    def _handle_preference_change(self, event: ft.ControlEvent) -> None:
        config = load_config()
        config.update(self.get_preferences())
        save_config(config)

    # Abre el dialogo de seleccion, importa el JSON elegido y notifica el cambio de perfil
    async def _handle_import_click(self, event: ft.ControlEvent) -> None:
        files = await self._file_picker.pick_files(
            dialog_title="Importar perfil de vision",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["json"],
        )
        if not files:
            return
        try:
            profile = import_profile_from_json(files[0].path)
        except Exception as error:
            self._show_toast("No se pudo importar el perfil: " + str(error), is_error=True)
            return
        create_profile(ACTIVE_PROFILE_ID, profile)
        config = load_config()
        config["active_profile_id"] = ACTIVE_PROFILE_ID
        save_config(config)
        if self._on_profile_changed is not None:
            self._on_profile_changed(profile)
        self._show_toast("Perfil importado correctamente", is_error=False)

    # Serializa el perfil activo segun el esquema de la Seccion 6.1 y lo escribe en disco
    async def _handle_export_click(self, event: ft.ControlEvent) -> None:
        config = load_config()
        profile_id = config.get("active_profile_id")
        profile = get_profile(profile_id) if profile_id else None
        if profile is None:
            self._show_toast("No hay un perfil activo para exportar", is_error=True)
            return
        export_bytes = json.dumps(dataclasses.asdict(profile), indent=2).encode("ascii")
        saved_path = await self._file_picker.save_file(
            dialog_title="Exportar perfil de vision",
            file_name="chromatic_vision_profile.json",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["json"],
            src_bytes=export_bytes,
        )
        if saved_path is None:
            return
        self._show_toast("Perfil exportado a " + saved_path, is_error=False)

    # Muestra una notificacion no bloqueante reforzada con icono y color, nunca solo color
    def _show_toast(self, message: str, is_error: bool) -> None:
        icon_name = ft.Icons.ERROR_OUTLINE if is_error else ft.Icons.CHECK_CIRCLE_OUTLINE
        icon_color = self.palette.error if is_error else self.palette.success
        self.page.show_dialog(
            ft.SnackBar(
                content=ft.Row(
                    controls=[
                        ft.Icon(icon=icon_name, color=icon_color, size=18),
                        ft.Text(message, color=self.palette.text_primary, expand=True),
                    ],
                    spacing=Spacing.SPACE_2,
                ),
                bgcolor=self.palette.bg_elevated,
            )
        )
