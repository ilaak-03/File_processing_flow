import json
import datetime
import os
import boto3

# Initialize clients
dynamodb = boto3.resource("dynamodb")
ses = boto3.client("ses")
 
METADATA_TABLE = os.environ["METADATA_TABLE"]
TABLE = dynamodb.Table(METADATA_TABLE)

def lambda_handler(event, context):
    """
    Marks items as FAILED in DynamoDB for S3 files processed from SQS messages.
    The failure reason is set as 'Notification validation or SES failure'.
    """
    for record in event.get("Records", []):

        body = json.loads(record.get("body", "{}"))

        for s3_record in body.get("Records", []):
            key = s3_record.get("s3", {}).get("object", {}).get("key")
            if not key:
                print("No S3 key found in record, skipping...")
                continue


            file_id = key.split("/")[-1].split("_")[0]

            try:
                TABLE.update_item(
                    Key={"fileId": file_id},
                    UpdateExpression="SET #s=:s, failedAt=:t",
                    ExpressionAttributeNames={"#s": "status"},
                    ExpressionAttributeValues={
                        ":s": "FAILED",
                        ":t": datetime.datetime.utcnow().isoformat()
                    }
                )
                print(f"Marked fileId {file_id} as FAILED")
            except Exception as e:
                print(f"Error updating DynamoDB for fileId {file_id}: {e}")

    return {"statusCode": 200, "body": json.dumps("Failure processing complete")}
