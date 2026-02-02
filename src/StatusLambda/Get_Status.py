import json, boto3
import os

dynamodb = boto3.resource("dynamodb")
METADATA_TABLE = os.environ["METADATA_TABLE"]
TABLE = dynamodb.Table(METADATA_TABLE)

def lambda_handler(event, context):
    file_id = event.get("pathParameters", {}).get("fileId")
    if not file_id:
        return {"statusCode": 400, "body": json.dumps({"error": "fileId is required"})}

    response = TABLE.get_item(Key={"fileId": file_id})
    item = response.get("Item")

    if not item:
        return {"statusCode": 404, "body": json.dumps({"error": "File not found"})}

    return {
        "statusCode": 200,
        "body": json.dumps({
            "fileId": item["fileId"],
            "filename": item["filename"],
            "status": item["status"],
            "emailSent": item.get("emailSent", False),
            "createdAt": item["createdAt"],
            "processedAt": item.get("processedAt")
        })
    }
