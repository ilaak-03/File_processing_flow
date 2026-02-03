import json
import os
import boto3
from botocore.exceptions import ClientError
import datetime
import re
 
# Initialize clients
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
 

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")


def is_email_verified(email):
    """
    Check if the email is verified in SES
    """
    try:
        response = ses.get_identity_verification_attributes(Identities=[email])
        status = response["VerificationAttributes"].get(email, {}).get("VerificationStatus")
        return status == "Success"
    except ClientError as e:
        print(f"SES verification check failed for {email}: {e}")
        return False


def lambda_handler(event, context):
    for sqs_record in event.get("Records", []):
        body = json.loads(sqs_record["body"])

        for s3_record in body.get("Records", []):
            key = s3_record["s3"]["object"]["key"]
            filename = key.split("/")[-1]
            file_id = filename.split("_")[0]

            item = TABLE.get_item(Key={"fileId": file_id}).get("Item")
            if not item:
                raise Exception(f"Metadata not found for {file_id}")

            user_email = item.get("userEmail")

            if user_email:
                if not EMAIL_REGEX.match(user_email):
                    raise Exception(f"Invalid email format: {user_email}")

                if not is_email_verified(user_email):
                    raise Exception(f"Unverified email: {user_email}")

                try:
                    response = ses.send_email(
                        Source=SENDER,
                        Destination={"ToAddresses": [user_email]},
                        Message={
                            "Subject": {"Data": "File Processed Successfully"},
                            "Body": {"Text": {"Data": EMAIL_TEMPLATE.format(
                                filename=item["filename"],
                                status="COMPLETED"
                            )}}
                        }
                    )

                    TABLE.update_item(
                        Key={"fileId": file_id},
                        UpdateExpression="SET emailSent=:e, sesMessageId=:m",
                        ExpressionAttributeValues={
                            ":e": True,
                            ":m": response["MessageId"]
                        }
                    )
                except ClientError as e:
                    print(f"Failed to send email to {user_email}: {e}")
                    raise

            TABLE.update_item(
                Key={"fileId": file_id},
                UpdateExpression="SET #s=:s, processedAt=:p",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={
                    ":s": "COMPLETED",
                    ":p": datetime.datetime.utcnow().isoformat()
                }
            )

    return {"statusCode": 200, "body": json.dumps("Processing complete")}
