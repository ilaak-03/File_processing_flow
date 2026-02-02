import json
import os
import boto3
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

# Regex to validate basic email format
EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

def is_email_verified(email):
    """
    Check if SES has verified the email address.
    """
    try:
        response = ses.get_identity_verification_attributes(
            Identities=[email]
        )
        attrs = response.get("VerificationAttributes", {})
        return attrs.get(email, {}).get("VerificationStatus") == "Success"
    except Exception as e:
        print(f"Error checking SES verification for {email}: {e}")
        return False

def lambda_handler(event, context):
    """
    Process SQS messages:
    1. Update DynamoDB with processing status.
    2. Only send email if userEmail exists, is valid, and SES verified.
    3. Skip invalid/unverified emails without failing the Lambda, so DLQ is never triggered.
    """
    for sqs_record in event.get("Records", []):
        try:
            body = json.loads(sqs_record["body"])
        except Exception as e:
            print(f"Skipping message: invalid JSON. Error: {e}")
            continue  # Skip invalid messages silently

        for s3_record in body.get("Records", []):
            key = s3_record["s3"]["object"]["key"]
            filename = key.split("/")[-1]
            file_id = filename.split("_")[0]

            processed_at = datetime.datetime.utcnow().isoformat()
            status = "COMPLETED"

            # Fetch item from DynamoDB
            response = TABLE.get_item(Key={"fileId": file_id})
            item = response.get("Item")

            if not item:
                print(f"Skipping: DynamoDB item not found for fileId={file_id}")
                continue  # Skip missing DB items silently

            filename = item.get("filename")
            user_email = item.get("userEmail")  # Optional

            # Update DynamoDB status
            TABLE.update_item(
                Key={"fileId": file_id},
                UpdateExpression="SET #s = :s, processedAt = :p",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={":s": status, ":p": processed_at}
            )

            # Send email only if user_email exists, is valid format, and SES verified
            if user_email:
                if EMAIL_REGEX.match(user_email) and is_email_verified(user_email):
                    try:
                        response = ses.send_email(
                            Source=SENDER,
                            Destination={"ToAddresses": [user_email]},
                            Message={
                                "Subject": {"Data": "File Processed Successfully"},
                                "Body": {"Text": {"Data": EMAIL_TEMPLATE.format(filename=filename, status=status)}}
                            }
                        )

                        # Update DynamoDB with email info
                        TABLE.update_item(
                            Key={"fileId": file_id},
                            UpdateExpression="SET emailSent = :e, sesMessageId = :m",
                            ExpressionAttributeValues={":e": True, ":m": response["MessageId"]}
                        )

                        print(f"Email sent successfully to {user_email}")

                    except Exception as e:
                        print(f"Skipping sending email for {user_email}. Error: {e}")
                        # Do NOT raise exception — prevents DLQ
                        continue
                else:
                    print(f"Skipping invalid/unverified email: {user_email}")
            else:
                print(f"No userEmail provided for fileId={file_id}, skipping email")
