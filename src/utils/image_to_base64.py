import base64
from PIL import Image
import io
import os

def image_file_to_base64(file_path: str) -> str:
    if not os.path.exists(file_path):
        return ""
    try:
        with Image.open(file_path) as img:
            buffered = io.BytesIO()
            img.save(buffered, format=img.format or "PNG")
            img_bytes = buffered.getvalue()
            return base64.b64encode(img_bytes).decode("utf-8")
    except Exception as e:
        print(f"Erro ao converter imagem para base64: {e}")
        return ""
