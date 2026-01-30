# storage.py
import os
import uuid
import datetime
import boto3

UPLOAD_BUCKET = os.environ["UPLOAD_BUCKET"]
METADATA_TABLE = os.environ["METADATA_TABLE"]

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

table = dynamodb.Table(METADATA_TABLE)
def upload_to_s3(file_bytes, filename):
    file_id = str(uuid.uuid4())
    key = f"incoming/{file_id}_{filename}"

    s3.put_object(
        Bucket=UPLOAD_BUCKET,
        Key=key,
        Body=file_bytes
    )

    return file_id, key

def save_metadata(file_id, filename, user_email):
    table.put_item(Item={
        "fileId": file_id,
        "filename": filename,
        "userEmail": user_email,
        "status": "UPLOADED",
        "emailSent": False,
        "createdAt": datetime.datetime.utcnow().isoformat()
    })
