import flet as ft
from base64_utils import decode_base64_to_image
from overlay import show_overlay
import base64
import win32clipboard
from PIL import Image
import io
import os
from utils.flet_style import style
from utils.image_to_base64 import image_file_to_base64


output_ico_path = os.path.join('assets', "icon.ico")


def main(page: ft.Page):
    page = style(page)
    input_fields, image_fields = [], []
    zoom_factor, zoom_step, base_size = 1.0, 0.5, 200

    inputs_column = ft.Column(spacing=10, scroll="auto")

    def build_input_field_with_preview(index, input_fields, inputs_column, page):
        base_size = 60
        text_field = ft.TextField(text_size=10, hint_text=f"Base64 {index}", expand=True)
        input_fields.append(text_field)

        image_preview = None  # só cria se necessário

        def update_preview(_):
            nonlocal image_preview
            from base64_utils import decode_base64_to_image
            preview_src = decode_base64_to_image(text_field.value)

            if preview_src:
                if not image_preview:
                    image_preview = ft.Image(
                        src=preview_src,
                        width=base_size,
                        height=base_size,
                        fit=ft.ImageFit.CONTAIN
                    )
                    row.controls.append(image_preview)
                else:
                    image_preview.src = preview_src
                page.update()

        text_field.on_change = update_preview

        def pick_file_result(e: ft.FilePickerResultEvent):
            if e.files:
                b64 = image_file_to_base64(e.files[0].path)
                text_field.value = b64
                update_preview(None)

        file_picker = ft.FilePicker(on_result=pick_file_result)
        page.overlay.append(file_picker)

        pick_button = ft.IconButton(icon=ft.Icons.FOLDER_OPEN, on_click=lambda _: file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["jpg", "jpeg", "png"]
        ))

        row = ft.Row([text_field, pick_button], alignment=ft.MainAxisAlignment.START)
        inputs_column.controls.append(row)
        page.update()

    def add_input_field_local(input_fields, inputs_column, page):
        index = len(input_fields) + 1
        text_field = ft.TextField(text_size=10, hint_text=f"Base64 {index}", expand=True)
        input_fields.append(text_field)

        def pick_file_result(e: ft.FilePickerResultEvent):
            if e.files:
                from utils.image_to_base64 import image_file_to_base64
                b64 = image_file_to_base64(e.files[0].path)
                text_field.value = b64
                page.update()

        file_picker = ft.FilePicker(on_result=pick_file_result)
        page.overlay.append(file_picker)

        pick_button = ft.IconButton(icon=ft.Icons.FOLDER_OPEN, on_click=lambda _: file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["jpg", "jpeg", "png"]
        ))

        row = ft.Row([text_field, pick_button], alignment=ft.MainAxisAlignment.START)
        inputs_column.controls.append(row)
        page.update()

    build_input_field_with_preview(len(input_fields) + 1, input_fields, inputs_column, page)

    image_fields = [ft.Image(src="", fit=ft.ImageFit.CONTAIN, width=base_size, height=base_size)
                    for _ in range(len(input_fields))]

    grid_view_container = ft.Container()

    def build_grid_view():
        max_size = int(base_size * zoom_factor)
        while len(image_fields) < len(input_fields):
            image_fields.append(ft.Image(src="", fit=ft.ImageFit.CONTAIN, width=base_size, height=base_size))
        for img_field in image_fields:
            img_field.width = max_size
            img_field.height = max_size
        return ft.GridView(
            controls=image_fields[:len(input_fields)],
            max_extent=max_size,
            child_aspect_ratio=1,
            spacing=10,
            run_spacing=10
        )

    def update_images():
        while len(image_fields) < len(input_fields):
            image_fields.append(ft.Image(src="", fit=ft.ImageFit.CONTAIN, width=base_size, height=base_size))

        for i in range(len(input_fields)):
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

    def reset(e=None):
        input_fields.clear()
        image_fields.clear()
        inputs_column.controls.clear()
        grid_view_container.content = build_grid_view()
        add_input_field_local(input_fields, inputs_column, page)
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
                content=ft.Column(controls=[inputs_column,
                                            ft.Row(controls=[
                                                ft.ElevatedButton(text="+", on_click=lambda
                                                e: build_input_field_with_preview(len(
                                                input_fields) + 1, input_fields, inputs_column, page)),
                                                ft.ElevatedButton(text="↩️", on_click=reset)],
                                                alignment=ft.MainAxisAlignment.START)], expand=True, scroll='auto')),
            ft.Tab(
                text="Visualize",
                content=ft.Container(expand=True, content=ft.Column(expand=True, scroll="auto",
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


ft.app(target=main, assets_dir='assets')
