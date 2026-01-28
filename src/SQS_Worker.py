import json
import boto3
import datetime

dynamodb = boto3.resource("dynamodb")
ses = boto3.client("ses")

TABLE = dynamodb.Table("FileMetadata-140857882741")
SENDER = "ilaakmandya@gmail.com"

EMAIL_TEMPLATE = """Hello,

Your file {filename} has been processed.
Status: {status}

Thanks.
"""

def lambda_handler(event, context):
    for record in event["Records"]:
        body = json.loads(record["body"])
        file_id = body["fileId"]
        

        processed_at = datetime.datetime.utcnow().isoformat()
        status = "COMPLETED"

        response = TABLE.get_item(Key={"fileId": file_id})
        item = response.get("Item")

        if not item:
            raise Exception(f"DynamoDB item not found for fileId={file_id}")
            
        filename = item.get("filename")
        user_email = item.get("userEmail")

        TABLE.update_item(
            Key={"fileId": file_id},
            UpdateExpression="SET #s = :s, processedAt = :p",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": status, ":p": processed_at}
        )

        if user_email:
            try:
                response = ses.send_email(
                    Source=SENDER,
                    Destination={"ToAddresses": [user_email]},
                    Message={
                        "Subject": {"Data": "File Processed Successfully"},
                        "Body": {"Text": {"Data": EMAIL_TEMPLATE.format(filename=filename, status=status)}}
                    }
                )
            except Exception as e:
                raise Exception(f"SES failed for {file_id}: {str(e)}")

            TABLE.update_item(
                Key={"fileId": file_id},
                UpdateExpression="SET emailSent = :e, sesMessageId = :m",
                ExpressionAttributeValues={":e": True, ":m": response["MessageId"]}
            )
