import tkinter as tk
from PIL import Image, ImageTk
import base64
import io
import os


class ImageOverlayApp:
    def __init__(self, root, base64_list):
        self.root = root
        self.original_pil_images = [self.decode_base64_image(b64) for b64 in base64_list]
        self.photo_images = []
        self.image_labels = []

        self.zoom_factor = 1.0
        self.zoom_step = 0.2
        self.base_image_size = 200
        self.layout_mode = tk.StringVar(value="grid")

        self.setup_window()
        self.create_widgets()
        self.setup_bindings()
        self.apply_layout()

    def decode_base64_image(self, b64_string):
        image_data = base64.b64decode(b64_string)
        return Image.open(io.BytesIO(image_data)).convert("RGB")

    def setup_window(self):
        self.root.title("PiP Mode")
        self.root.geometry("800x600")
        self.root.configure(bg="black")
        self.root.attributes("-topmost", True)

        icon_path = "assets/icon.png"
        if os.path.exists(icon_path):
            icon_image = ImageTk.PhotoImage(file=icon_path)
            self.root.iconphoto(True, icon_image)

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def create_widgets(self):
        self.image_display_frame = tk.Frame(self.root, bg="black")
        self.image_display_frame.grid(row=0, column=0, sticky="nsew")

        controls_frame = tk.Frame(self.root, bg="#333333")
        controls_frame.grid(row=1, column=0, sticky="ew")
        controls_frame.grid_columnconfigure(0, weight=1)
        controls_frame.grid_columnconfigure(1, weight=1)

        for _ in range(len(self.original_pil_images)):
            lbl = tk.Label(self.image_display_frame, bg="black")
            self.image_labels.append(lbl)

        zoom_btn_frame = tk.Frame(controls_frame, bg="#333333")
        zoom_btn_frame.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        tk.Button(zoom_btn_frame, text="🔍+", command=self.zoom_in, font=("Arial", 12)).pack(side=tk.LEFT)
        tk.Button(zoom_btn_frame, text="🔍-", command=self.zoom_out, font=("Arial", 12)).pack(side=tk.LEFT, padx=5)

        layout_mode_frame = tk.Frame(controls_frame, bg="#333333")
        layout_mode_frame.grid(row=0, column=1, sticky="e", padx=10, pady=5)

        layouts = [("Grid", "grid"), ("Horizontal", "horizontal"), ("Vertical", "vertical")]
        for text, value in layouts:
            rb = tk.Radiobutton(layout_mode_frame, text=text, variable=self.layout_mode, value=value,
                                command=self.apply_layout, bg="#333333", fg="white",
                                selectcolor="#555555", indicatoron=0, font=("Arial", 10),
                                borderwidth=0, relief="flat", padx=10, pady=5)
            rb.pack(side=tk.LEFT)

    def apply_layout(self):
        for widget in self.image_display_frame.winfo_children():
            widget.grid_forget()

        mode = self.layout_mode.get()
        num_images = len(self.image_labels)

        if num_images == 0:
            return

        if mode == "grid":
            cols = 2 if num_images > 1 else 1
            rows = (num_images + cols - 1) // cols
        elif mode == "horizontal":
            cols = num_images
            rows = 1
        else:
            cols = 1
            rows = num_images

        for r in range(rows):
            self.image_display_frame.grid_rowconfigure(r, weight=1)
        for c in range(cols):
            self.image_display_frame.grid_columnconfigure(c, weight=1)

        for i, lbl in enumerate(self.image_labels):
            row = i // cols if mode != "vertical" else i
            col = i % cols if mode != "vertical" else 0
            lbl.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)

        self.update_image_content()

    def update_image_content(self):
        self.photo_images.clear()
        target_size = int(self.base_image_size * self.zoom_factor)

        if target_size <= 0: return

        for i, original_img in enumerate(self.original_pil_images):
            if original_img:
                img_copy = original_img.copy()
                img_copy.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)

                tk_img = ImageTk.PhotoImage(img_copy)
                self.photo_images.append(tk_img)

                label = self.image_labels[i]
                label.config(image=tk_img)
                label.image = tk_img

        self.root.update_idletasks()

    def zoom_in(self): ## todo: adicionar no utils64.py, e ajeitar pra funcionar no modo PiP e main.
        self.zoom_factor = min(3.0, self.zoom_factor + self.zoom_step)
        self.update_image_content()

    def zoom_out(self): ## todo: adicionar no utils64.py, e ajeitar pra funcionar no modo PiP e main.
        self.zoom_factor = max(0.1, self.zoom_factor - self.zoom_step)
        self.update_image_content()

    def setup_bindings(self):
        self.root.bind("<Control-plus>", self.zoom_in)
        self.root.bind("<Control-equal>", self.zoom_in)
        self.root.bind("<Control-minus>", self.zoom_out)
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.image_display_frame.bind("<Configure>", self.update_image_content)


def show_overlay(base64_list):
    root = tk.Tk()
    app = ImageOverlayApp(root, base64_list)
    root.mainloop()
