import json
import uuid
import boto3
import datetime
from io import BytesIO
import cgi
from base64 import b64decode

# AWS clients
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

# Config
BUCKET = "file-upload-s3-bucket-140857882741"
TABLE = dynamodb.Table("FileMetadata-140857882741")
MAX_SIZE_MB = 5
ALLOWED_EXTENSIONS = ["pdf", "doc", "txt"]

def lambda_handler(event, context):
    try:
        headers = event.get("headers") or {}
        content_type = headers.get("Content-Type") or headers.get("content-type", "")
        body = event.get("body", "")
        is_base64 = event.get("isBase64Encoded", False)

        file_bytes = None
        filename = None
        user_email = None

        # --- 1️⃣ Multipart/form-data (browser uploads) ---
        if "multipart/form-data" in content_type:
            # Decode if base64 (API Gateway might still send it encoded)
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
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "file field is required in form-data"})
                }

            fileitem = form["file"]
            file_bytes = fileitem.file.read()
            filename = fileitem.filename
            user_email = form.getfirst("userEmail")

        # --- 2️⃣ Raw binary uploads (application/pdf, octet-stream, etc.) ---
        else:
            if is_base64:
                file_bytes = b64decode(body)
            else:
                file_bytes = body.encode() if isinstance(body, str) else body

            # filename must come from header or query param
            filename = (
                headers.get("Filename")
                or headers.get("filename")
                or (event.get("queryStringParameters") or {}).get("filename")
            )

            user_email = (
                headers.get("userEmail")
                or (event.get("queryStringParameters") or {}).get("userEmail")
            )

        # --- 3️⃣ Validate filename ---
        if not filename:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "filename is required"})
            }

        # --- 4️⃣ Validate extension ---
        ext = filename.split(".")[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": f"Invalid file type: {ext}"})
            }

        # --- 5️⃣ Validate size ---
        size_bytes = len(file_bytes)
        if size_bytes > MAX_SIZE_MB * 1024 * 1024:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": f"File too large: {size_bytes} bytes"})
            }

        # --- 6️⃣ Upload to S3 ---
        file_id = str(uuid.uuid4())
        s3_key = f"incoming/{file_id}_{filename}"

        s3.put_object(
            Bucket=BUCKET,
            Key=s3_key,
            Body=file_bytes
        )

        # --- 7️⃣ Save metadata in DynamoDB ---
        TABLE.put_item(Item={
            "fileId": file_id,
            "filename": filename,
            "userEmail": user_email,
            "status": "UPLOADED",
            "emailSent": False,
            "createdAt": datetime.datetime.utcnow().isoformat()
        })

        # --- 8️⃣ Return success ---
        return {
            "statusCode": 200,
            "body": json.dumps({
                "fileId": file_id,
                "status": "UPLOADED"
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
