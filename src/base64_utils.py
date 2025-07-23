import base64
import tempfile

def decode_base64_to_image(b64_string: str) -> str | None:
    try:
        content = base64.b64decode(b64_string.strip())
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
            f.write(content)
            return f.name
    except Exception:
        return None
