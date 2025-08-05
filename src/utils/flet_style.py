import flet as ft
from flet.core.page import Page


def style(page: Page) -> ft.Page:
    page.title = "Base64 Visualizer"
    page.window.width = 420
    page.window.height = 550

    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary="#ffffff",
            primary_container="#333333",
            secondary="#cccccc",
            background="#121212",
            surface="#1e1e1e",
            on_primary="#000000",
            on_background="#ffffff",
            on_surface="#ffffff",
        )
    )

    return page

