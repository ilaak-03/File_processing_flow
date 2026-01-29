import json, boto3

dynamodb = boto3.resource("dynamodb")
TABLE = dynamodb.Table("FileMetadata-140857882741")

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
