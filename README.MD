# 🖼️ B64V – Base64 Visualizer

**B64V** (Base64 Visualizer) is a lightweight cross-platform desktop app to **decode, visualize, and manipulate multiple Base64 images simultaneously**.

Developed with [Flet](https://flet.dev) and Python, the app provides a clean and interactive interface for previewing Base64-encoded images, zooming, copying, and even overlaying them on screen like YouTube's PiP mode.

---

## 🚀 Features

- 🔢 **Support for up to 4 Base64 inputs simultaneously**
- 🖼️ **Responsive visual grid layout**
- 🧭 **Zoom in / Zoom out** control for image scaling
- 📋 **Copy** all 4 images as a composed collage directly to clipboard *(Windows only)*
- 📌 **PiP Mode** (always-on-top floating overlay to visualize final layout)
- 🪟 Custom window dimensions and icon handling
- 🧠 Intelligent auto-resize of images to fit within consistent bounds
- ⚠️ Graceful fallback when copy is attempted on unsupported platforms (Linux/macOS)

---

## 💡 How It Works

Just paste your Base64 strings into the inputs under the **"Base64"** tab and switch to the **"Visualize"** tab to see them rendered in a responsive grid.

Use the **Copy** button to send all images as a single composition to the clipboard (Windows only), or open **PiP Mode** to keep the visualization floating above other windows.

---

## 🧩 Requirements

- Python 3.8+
- Dependencies:
  - `flet`
  - `Pillow`
  - `win32clipboard` *(only on Windows)*
  - `tkinter` (optional fallback for clipboard in other OS)

Install dependencies via:

```bash
pip install -r requirements.txt
