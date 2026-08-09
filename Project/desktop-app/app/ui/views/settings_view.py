# Vista de ajustes: preferencias de la aplicacion y gestion del perfil de vision
# La persistencia se delegara en app_config.py durante la fase de integracion

import flet as ft

from app.config.constants import APP_NAME, APP_VERSION, AppRoute
from app.ui.components.surface_card import SurfaceCard
from app.ui.theme.design_tokens import (
    FontSize,
    FontWeight,
    Radius,
    Spacing,
)
from app.ui.views.base_view import BaseView

# Opciones fijas del selector de arranque de la aplicacion
STARTUP_OPTIONS = ("Ventana principal", "Solo bandeja del sistema")


class SettingsView(BaseView):
    route = AppRoute.SETTINGS
    title = "Ajustes"
    subtitle = "Preferencias de la aplicacion y gestion de perfiles"

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

    # Tarjeta de comportamiento de arranque y persistencia en bandeja
    def _build_behavior_card(self) -> ft.Control:
        self._tray_switch = ft.Switch(value=True, active_color=self.palette.accent)
        self._autostart_switch = ft.Switch(value=False, active_color=self.palette.accent)
        self._startup_dropdown = ft.Dropdown(
            value=STARTUP_OPTIONS[0],
            options=[ft.dropdown.Option(option) for option in STARTUP_OPTIONS],
            width=240,
            border_color=self.palette.border,
            focused_border_color=self.palette.accent,
            text_size=FontSize.BODY,
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
                            style=ft.ButtonStyle(
                                bgcolor=self.palette.accent,
                                color=self.palette.accent_contrast,
                                shape=ft.RoundedRectangleBorder(radius=Radius.SM),
                            ),
                        ),
                        ft.OutlinedButton(
                            content="Exportar perfil",
                            icon=ft.Icons.FILE_UPLOAD_OUTLINED,
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
