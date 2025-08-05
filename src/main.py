import flet as ft
from base64_utils import decode_base64_to_image
from overlay import show_overlay
import base64
import platform
import tempfile
import subprocess
import shutil
from PIL import Image
import io
import os
from utils.flet_style import style
from utils.image_to_base64 import image_file_to_base64
import pyperclipimg as pci


output_ico_path = os.path.join('assets', "icon.ico")


def copy_image_to_clipboard_cross_platform(image: Image.Image):
    system = platform.system()

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
        image.save(tmp_file, format="PNG")
        tmp_file_path = tmp_file.name

    try:
        if system == "Windows":
            import win32clipboard
            output = io.BytesIO()
            image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()

        elif system == "Darwin":
            subprocess.run([
                "osascript", "-e",
                f'set the clipboard to (read (POSIX file "{tmp_file_path}") as JPEG picture)'
            ], check=True)

        elif system == "Linux":
            if shutil.which("xclip") is None:
                raise RuntimeError("xclip não está instalado. Instale com: sudo apt install xclip")
            subprocess.run([
                "xclip", "-selection", "clipboard", "-t", "image/png", "-i", tmp_file_path
            ], check=True)

        else:
            raise NotImplementedError("Sistema operacional não suportado.")
    finally:
        os.remove(tmp_file_path)


def main(page: ft.Page):
    page = style(page)
    input_fields, image_fields = [], []
    zoom_factor, zoom_step, base_size = 1.0, 0.5, 200

    inputs_column = ft.Column(spacing=10, scroll="auto")

    def build_input_field_with_preview(index):
        base_size = 60
        image_preview = None
        text_field = ft.TextField(text_size=10, hint_text=f"Base64 {index}", expand=True)

        def update_preview(_):
            nonlocal image_preview
            preview_src = decode_base64_to_image(text_field.value)
            if preview_src:
                if not image_preview:
                    image_preview = ft.Image(
                        src=preview_src, width=base_size, height=base_size, fit=ft.ImageFit.CONTAIN)
                    row.controls.append(image_preview)
                else:
                    image_preview.src = preview_src
                page.update()

        def on_paste_image(e):
            try:
                img = pci.paste()
                if img:
                    buffered = io.BytesIO()
                    img.save(buffered, format="PNG")
                    b64 = base64.b64encode(buffered.getvalue()).decode()
                    text_field.value = b64
                    update_preview(None)
                    page.update()
            except Exception:
                pass

        text_field.on_change = update_preview
        text_field.on_paste = on_paste_image
        input_fields.append(text_field)

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

    def add_input_field_local():
        build_input_field_with_preview(len(input_fields) + 1)

    build_input_field_with_preview(len(input_fields) + 1)

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
        current_base64_values = [field.value for field in input_fields if field.value.strip()]
        num_images = len(current_base64_values)

        if num_images == 0:
            page.snack_bar = ft.SnackBar(ft.Text("Nenhuma imagem válida para copiar."))
            page.snack_bar.open = True
            page.update()
            return

        processed_images = []
        target_width = int(base_size * zoom_factor)
        max_heights = []

        # Processa todas as imagens
        for b64 in current_base64_values:
            try:
                img_data = base64.b64decode(b64)
                img = Image.open(io.BytesIO(img_data)).convert("RGB")
                original_width, original_height = img.size
                new_height = int(original_height * (target_width / original_width)) if original_width else 1
                resized_img = img.resize((target_width, new_height), Image.LANCZOS)
            except Exception:
                resized_img = Image.new("RGB", (target_width, 1), color="white")
            processed_images.append(resized_img)

        # Define grid (ex: 2 colunas até 4 imagens, 3 colunas até 9, etc)
        max_cols = min(4, max(2, int(num_images ** 0.5)))
        cols = max_cols
        rows = (num_images + cols - 1) // cols

        # Calcula larguras e alturas finais
        horizontal_spacing = 20
        vertical_spacing = 20
        cell_width = target_width
        cell_heights = []

        for r in range(rows):
            row_imgs = processed_images[r * cols:(r + 1) * cols]
            max_height = max(img.height for img in row_imgs)
            cell_heights.append(max_height)

        final_width = (cell_width + horizontal_spacing) * cols - horizontal_spacing
        final_height = sum(cell_heights) + vertical_spacing * (rows - 1)

        composed = Image.new("RGB", (final_width, final_height), color="black")

        # Coloca as imagens no grid
        for i, img in enumerate(processed_images):
            row = i // cols
            col = i % cols

            x = col * (cell_width + horizontal_spacing)
            y_offset = sum(cell_heights[:row]) + (row * vertical_spacing)
            y = y_offset + (cell_heights[row] - img.height) // 2  # Centraliza na célula

            composed.paste(img, (x, y))

        try:
            copy_image_to_clipboard_cross_platform(composed)
            page.snack_bar = ft.SnackBar(ft.Text(f"{num_images} imagem(ns) copiadas com sucesso! 🎉"))
        except Exception as err:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao copiar: {err} 😵‍💫"))

        page.snack_bar.open = True
        page.update()

    def reset(e=None):
        input_fields.clear()
        image_fields.clear()
        inputs_column.controls.clear()
        grid_view_container.content = build_grid_view()
        add_input_field_local()
        page.update()

    def on_key(e: ft.KeyboardEvent):
        if e.key in ("+", "="):
            zoom_in()
        elif e.key == "-":
            zoom_out()

    page.on_keyboard_event = on_key

    buttons_row = ft.Container(
        content=ft.Row([
            ft.ElevatedButton("PiP mode", on_click=toggle_top),
            ft.ElevatedButton("Copy", on_click=copy_image),
            ft.ElevatedButton("🔍+", on_click=zoom_in),
            ft.ElevatedButton("🔍-", on_click=zoom_out)
        ], alignment=ft.MainAxisAlignment.CENTER),
        padding=10,
        bgcolor=ft.Colors.SURFACE,
    )

    tabs = ft.Tabs(
        selected_index=0,
        on_change=on_tab_change,
        expand=True,
        tabs=[
            ft.Tab(
                text="Base64",
                content=ft.Column(controls=[
                    inputs_column,
                    ft.Row(controls=[
                        ft.ElevatedButton(text="+", on_click=lambda _: build_input_field_with_preview(len(input_fields) + 1)),
                        ft.ElevatedButton(text="↩️", on_click=reset)
                    ], alignment=ft.MainAxisAlignment.START)
                ], expand=True, scroll='auto')
            ),
            ft.Tab(
                text="Visualize",
                content=ft.Column([
                    ft.Container(content=grid_view_container, expand=True),
                    buttons_row
                ])
            )
        ]
    )

    grid_view_container.content = build_grid_view()
    page.add(tabs)


ft.app(target=main, assets_dir='assets')
