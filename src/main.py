import flet as ft
from base64_utils import decode_base64_to_image
from overlay import show_overlay
import base64
import win32clipboard
from PIL import Image
import io
import os

assets_dir = "assets"
output_ico_path = os.path.join(assets_dir, "icon.ico")
os.makedirs(assets_dir, exist_ok=True)

def main(page: ft.Page):
    page.title = "Base64 Visualizer"
    page.window.width = 420
    page.window.height = 550

    if output_ico_path and os.path.exists(output_ico_path):
        page.window_icon = output_ico_path

    base64_inputs = [""] * 4
    zoom_factor = 1.0
    zoom_step = 0.5
    base_size = 200

    input_fields = [ft.TextField(text_size=10, hint_text=f"Base64 {i + 1}") for i in range(4)]
    image_fields = [ft.Image(src="", fit=ft.ImageFit.CONTAIN, width=base_size, height=base_size) for _ in range(4)]

    grid_view_container = ft.Container()

    def build_grid_view():
        max_size = int(base_size * zoom_factor)
        for img_field in image_fields:
            img_field.width = max_size
            img_field.height = max_size
        return ft.GridView(
            controls=image_fields,
            max_extent=max_size,
            child_aspect_ratio=1,
            spacing=10,
            run_spacing=10
        )

    def update_images():
        for i in range(4):
            img_src = decode_base64_to_image(input_fields[i].value)
            image_fields[i].src = img_src or ""
        grid_view_container.content = build_grid_view()
        page.update()

    def on_tab_change(e):
        if e.control.selected_index == 1:
            update_images()

    def toggle_top(e):
        show_overlay([field.value for field in input_fields])

    def zoom_in(e=None):
        nonlocal zoom_factor
        zoom_factor += zoom_step
        update_images()

    def zoom_out(e=None):
        nonlocal zoom_factor
        zoom_factor = max(0.1, zoom_factor - zoom_step)
        update_images()

    def copy_image(e):
        current_base64_values = [field.value for field in input_fields]

        processed_images = []
        max_height_row1 = 0
        max_height_row2 = 0

        target_width_for_copy = int(base_size * zoom_factor)

        for i, b64 in enumerate(current_base64_values):
            if b64:
                try:
                    img_data = base64.b64decode(b64)
                    img = Image.open(io.BytesIO(img_data)).convert("RGB")

                    original_width, original_height = img.size

                    if original_width == 0:
                        new_width, new_height = 0, 0
                    else:
                        new_width = target_width_for_copy
                        new_height = int(original_height * (new_width / original_width))

                    if new_width == 0 or new_height == 0:
                        resized_img = Image.new("RGB", (1, 1), color="white")
                    else:
                        resized_img = img.resize((new_width, new_height), Image.LANCZOS)

                    processed_images.append(resized_img)

                    if i < 2:
                        max_height_row1 = max(max_height_row1, resized_img.height)
                    else:
                        max_height_row2 = max(max_height_row2, resized_img.height)

                except Exception as ex:
                    processed_images.append(Image.new("RGB", (target_width_for_copy, 1), color="white"))
                    if i < 2:
                        max_height_row1 = max(max_height_row1, 1)
                    else:
                        max_height_row2 = max(max_height_row2, 1)

            else:
                processed_images.append(Image.new("RGB", (target_width_for_copy, 1), color="white"))
                if i < 2:
                    max_height_row1 = max(max_height_row1, 1)
                else:
                    max_height_row2 = max(max_height_row2, 1)

        while len(processed_images) < 4:
            processed_images.append(Image.new("RGB", (target_width_for_copy, 1), color="white"))

        horizontal_spacing = 20
        vertical_spacing = 20

        composed_width = (target_width_for_copy * 2) + horizontal_spacing
        composed_height = max_height_row1 + max_height_row2 + vertical_spacing

        composed = Image.new("RGB", (composed_width, composed_height), color="black")

        final_positions = [
            (0, 0),
            (target_width_for_copy + horizontal_spacing, 0),
            (0, max_height_row1 + vertical_spacing),
            (target_width_for_copy + horizontal_spacing, max_height_row1 + vertical_spacing)
        ]

        for i, img_data in enumerate(processed_images):
            if img_data:
                base_x, base_y = final_positions[i]
                center_x_offset = (target_width_for_copy - img_data.width) // 2
                current_row_max_height = max_height_row1 if i < 2 else max_height_row2
                center_y_offset = max(0, (current_row_max_height - img_data.height) // 2)
                composed.paste(img_data, (base_x + center_x_offset, base_y + center_y_offset))

        output = io.BytesIO()
        composed.save(output, "BMP")
        data = output.getvalue()[14:]

        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            page.snack_bar = ft.SnackBar(ft.Text("Imagem copiada para a área de transferência!"))
        except Exception as e:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao copiar: {e}"))

        page.snack_bar.open = True
        page.update()

    def on_key(e: ft.KeyboardEvent):
        if e.key in ("+", "="):
            zoom_in()
        elif e.key == "-":
            zoom_out()

    page.on_keyboard_event = on_key

    tabs = ft.Tabs(
        selected_index=0,
        on_change=on_tab_change,
        expand=True,
        tabs=[
            ft.Tab(
                text="Base64",
                content=ft.Column(
                    controls=[ft.Column(controls=input_fields, spacing=10, scroll="auto")],
                    expand=True
                )
            ),
            ft.Tab(
                text="Visualize",
                content=ft.Container(
                    expand=True,
                    content=ft.Column(
                        expand=True,
                        scroll="auto",
                        controls=[
                            grid_view_container,
                            ft.Row([
                                ft.ElevatedButton("PiP mode", on_click=toggle_top),
                                ft.ElevatedButton("Copy", on_click=copy_image),
                                ft.ElevatedButton("🔍+", on_click=zoom_in),
                                ft.ElevatedButton("🔍-", on_click=zoom_out)
                            ], alignment=ft.MainAxisAlignment.CENTER)
                        ]
                    )
                )
            )
        ]
    )

    grid_view_container.content = build_grid_view()
    page.add(tabs)

ft.app(target=main, assets_dir=assets_dir)
