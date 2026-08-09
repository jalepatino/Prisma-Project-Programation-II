# Contrato comun de todas las vistas enrutadas del shell principal
# Define el ciclo de vida activate/deactivate que consumiran los servicios de captura

import flet as ft

from app.ui.theme.design_tokens import Palette, Spacing


class BaseView(ft.Container):
    # Atributos de clase sobrescritos por cada vista concreta
    route = ""
    title = ""
    subtitle = ""

    # Construye el contenedor desplazable comun y delega el cuerpo en la subclase
    def __init__(self, palette: Palette) -> None:
        super().__init__(expand=True)
        self.palette = palette
        self.is_active = False
        self.padding = ft.Padding.symmetric(
            horizontal=Spacing.SPACE_8, vertical=Spacing.SPACE_6
        )
        self.content = ft.Column(
            controls=self.build_body(),
            spacing=Spacing.SPACE_6,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # Cada vista concreta devuelve la lista de bloques que componen su cuerpo
    def build_body(self) -> list:
        raise NotImplementedError("Cada vista debe implementar build_body")

    # Se invoca al entrar en la ruta; las vistas con hilos los arrancan aqui
    def activate(self) -> None:
        self.is_active = True

    # Se invoca al salir de la ruta; libera recursos activos de la vista
    def deactivate(self) -> None:
        self.is_active = False
