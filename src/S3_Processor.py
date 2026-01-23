import json, boto3, os

sqs = boto3.client("sqs")

QUEUE_URL = os.environ["QUEUE_URL"]

def lambda_handler(event, context):
    for record in event["Records"]:
        key = record["s3"]["object"]["key"]
        filename = key.split("/")[-1]
        file_id = filename.split("_")[0]

        # ✅ Send message to SQS for further processing
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps({
                "fileId": file_id,
                "s3Key": key,
                "filename": filename
            })
        )
