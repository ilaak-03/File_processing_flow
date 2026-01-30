# request_utils.py
import os
from io import BytesIO
from base64 import b64decode
import cgi

MAX_SIZE_MB = int(os.environ.get("MAX_SIZE_MB", "5"))
ALLOWED_EXTENSIONS = {
    ext.strip().lower()
    for ext in os.environ.get("ALLOWED_EXTENSIONS", "").split(",")
    if ext.strip()
}

def parse_and_validate(event):
    headers = event.get("headers") or {}
    content_type = headers.get("Content-Type") or headers.get("content-type", "")
    body = event.get("body", "")
    is_base64 = event.get("isBase64Encoded", False)

    # --- Parse request ---
    if "multipart/form-data" in content_type:
        if is_base64:
            body = b64decode(body)
        else:
            body = body.encode() if isinstance(body, str) else body

        fp = BytesIO(body)
        env = {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": content_type,
        }

        form = cgi.FieldStorage(fp=fp, environ=env)
        if "file" not in form:
            raise ValueError("file field is required in form-data")

        fileitem = form["file"]
        file_bytes = fileitem.file.read()
        filename = fileitem.filename
        user_email = form.getfirst("userEmail")

    else:
        file_bytes = b64decode(body) if is_base64 else body.encode()
        filename = (
            headers.get("Filename")
            or headers.get("filename")
            or (event.get("queryStringParameters") or {}).get("filename")
        )
        user_email = (
            headers.get("userEmail")
            or (event.get("queryStringParameters") or {}).get("userEmail")
        )

    # --- Validate ---
    if not filename:
        raise ValueError("filename is required")

    if "." not in filename:
        raise ValueError("filename must have an extension")

    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Invalid file type: {ext}")

    size = len(file_bytes)
    if size > MAX_SIZE_MB * 1024 * 1024:
        raise ValueError(f"File too large: {size} bytes")

    return file_bytes, filename, user_email
