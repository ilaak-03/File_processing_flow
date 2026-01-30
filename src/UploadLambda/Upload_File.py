import json
from request_utils import parse_and_validate
from storage import upload_to_s3, save_metadata

def lambda_handler(event, context):
    try:
        file_bytes, filename, user_email = parse_and_validate(event)

        file_id, _ = upload_to_s3(file_bytes, filename)

        save_metadata(file_id, filename, user_email)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "fileId": file_id,
                "status": "UPLOADED"
            })
        }

    except ValueError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)})
        }

    except Exception:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
