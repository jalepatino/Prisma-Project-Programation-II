# Vista de panel: resumen del perfil de vision activo y estado de los filtros
# Los valores por defecto se sustituyen con profile_service en la fase de integracion

import flet as ft

from app.config.constants import AppRoute, TARGET_OVERLAY_FPS
from app.ui.components.surface_card import SurfaceCard
from app.ui.theme.design_tokens import (
    FontSize,
    FontWeight,
    Spacing,
)
from app.ui.views.base_view import BaseView
from app.utils.control_sync import request_update

# Estado inicial mostrado antes de cargar un perfil desde disco
DEFAULT_DEFICIENCY_LABEL = "Sin perfil cargado"
DEFAULT_SEVERITY_LABEL = "0%"
DEFAULT_FILTERS_LABEL = "0 activos"


class DashboardView(BaseView):
    route = AppRoute.DASHBOARD
    title = "Panel"
    subtitle = "Estado del perfil de vision y de los filtros activos"

    # Compone la fila de metricas, el estado del motor y los accesos rapidos
    def build_body(self) -> list:
        return [
            self._build_metrics_row(),
            self._build_engine_card(),
            self._build_shortcuts_card(),
        ]

    # Actualiza las metricas cuando el servicio de perfiles emite datos nuevos
    def update_summary(
        self, deficiency_label: str, severity_label: str, filters_label: str
    ) -> None:
        self._deficiency_value.value = deficiency_label
        self._severity_value.value = severity_label
        self._filters_value.value = filters_label
        request_update(self)

    # Tres tarjetas de metrica con igual peso visual
    def _build_metrics_row(self) -> ft.Control:
        self._deficiency_value = self._build_metric_value(DEFAULT_DEFICIENCY_LABEL)
        self._severity_value = self._build_metric_value(DEFAULT_SEVERITY_LABEL)
        self._filters_value = self._build_metric_value(DEFAULT_FILTERS_LABEL)
        return ft.Row(
            controls=[
                self._build_metric_card(
                    "Tipo de deficiencia", self._deficiency_value, ft.Icons.BIOTECH
                ),
                self._build_metric_card(
                    "Severidad estimada", self._severity_value, ft.Icons.SPEED
                ),
                self._build_metric_card(
                    "Filtros aplicados", self._filters_value, ft.Icons.LAYERS
                ),
            ],
            spacing=Spacing.SPACE_4,
        )

    # Tarjeta de estado del motor de correccion con objetivo de rendimiento
    def _build_engine_card(self) -> ft.Control:
        body = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(
                            icon=ft.Icons.PAUSE_CIRCLE_OUTLINE,
                            size=18,
                            color=self.palette.text_secondary,
                        ),
                        ft.Text(
                            "El motor de correccion esta en pausa",
                            size=FontSize.BODY,
                            weight=FontWeight.MEDIUM,
                            color=self.palette.text_primary,
                        ),
                    ],
                    spacing=Spacing.SPACE_2,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text(
                    "Activa la correccion desde la cabecera para aplicar la matriz "
                    "sobre la pantalla. El objetivo de rendimiento es de "
                    + str(TARGET_OVERLAY_FPS)
                    + " FPS sostenidos.",
                    size=FontSize.BODY,
                    color=self.palette.text_secondary,
                ),
            ],
            spacing=Spacing.SPACE_2,
            tight=True,
        )
        return SurfaceCard(
            palette=self.palette,
            body=body,
            title="Motor de correccion",
            subtitle="Servicio de superposicion en tiempo real",
        )

    # Accesos rapidos a las rutas mas usadas del shell
    def _build_shortcuts_card(self) -> ft.Control:
        body = ft.Row(
            controls=[
                ft.Text(
                    "Ctrl+1 Panel   Ctrl+2 Selector   Ctrl+3 Filtros   Ctrl+4 Ajustes",
                    size=FontSize.CAPTION,
                    color=self.palette.text_secondary,
                    expand=True,
                ),
                ft.Text(
                    "Ctrl+B contrae la barra   Ctrl+D cambia el tema",
                    size=FontSize.CAPTION,
                    color=self.palette.text_secondary,
                ),
            ],
            spacing=Spacing.SPACE_4,
        )
        return SurfaceCard(
            palette=self.palette,
            body=body,
            title="Atajos de teclado",
            subtitle="Navegacion sin raton para accesibilidad",
        )

    # Texto grande reutilizado por las tres metricas del panel
    def _build_metric_value(self, value: str) -> ft.Text:
        return ft.Text(
            value,
            size=FontSize.HEADING,
            weight=FontWeight.BOLD,
            color=self.palette.text_primary,
            no_wrap=True,
        )

    # Tarjeta de metrica con icono contenido y radio interno derivado
    def _build_metric_card(
        self, label: str, value_text: ft.Text, icon_name: str
    ) -> ft.Control:
        card = SurfaceCard(
            palette=self.palette,
            body=ft.Column(spacing=Spacing.SPACE_3, tight=True),
            expand=True,
        )
        icon_box = ft.Container(
            width=32,
            height=32,
            border_radius=card.inner_radius,
            bgcolor=self.palette.bg_secondary,
            alignment=ft.Alignment.CENTER,
            content=ft.Icon(icon=icon_name, size=16, color=self.palette.accent),
        )
        card.set_body(
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            icon_box,
                            ft.Text(
                                label,
                                size=FontSize.CAPTION,
                                weight=FontWeight.MEDIUM,
                                color=self.palette.text_secondary,
                                expand=True,
                            ),
                        ],
                        spacing=Spacing.SPACE_3,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    value_text,
                ],
                spacing=Spacing.SPACE_3,
                tight=True,
            )
        )
        return card
