import json
import os
import boto3
import datetime

dynamodb = boto3.resource("dynamodb")
ses = boto3.client("ses")

METADATA_TABLE = os.environ["METADATA_TABLE"]
TABLE = dynamodb.Table(METADATA_TABLE)
SENDER = "ilaakmandya@gmail.com"

EMAIL_TEMPLATE = """Hello,

Your file {filename} has been processed.
Status: {status}

Thanks.
"""

def lambda_handler(event, context):
    for sqs_record in event["Records"]:
        body = json.loads(sqs_record["body"])

        for s3_record in body["Records"]:
            key = s3_record["s3"]["object"]["key"]
            filename = key.split("/")[-1]
            file_id = filename.split("_")[0]

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
                response = ses.send_email(
                    Source=SENDER,
                    Destination={"ToAddresses": [user_email]},
                    Message={
                        "Subject": {"Data": "File Processed Successfully"},
                        "Body": {"Text": {"Data": EMAIL_TEMPLATE.format(filename=filename, status=status)}}
                    }
                )

                TABLE.update_item(
                    Key={"fileId": file_id},
                    UpdateExpression="SET emailSent = :e, sesMessageId = :m",
                    ExpressionAttributeValues={":e": True, ":m": response["MessageId"]}
                )
