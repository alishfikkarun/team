# bot/s3uploader.py
import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError

S3_BUCKET = os.getenv("S3_BUCKET")

def upload_fileobj(fileobj, key, content_type=None, public=True):
    """
    fileobj: file-like object opened in binary mode
    key: object key in bucket
    returns: public URL (assuming bucket public or appropriate policy)
    """
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION"),
    )
    extra = {}
    if content_type:
        extra['ContentType'] = content_type
    if public:
        extra['ACL'] = 'public-read'
    try:
        s3.upload_fileobj(fileobj, S3_BUCKET, key, ExtraArgs=extra)
    except (BotoCoreError, ClientError) as e:
        raise
    # Construct public URL (S3 virtual-hosted–style)
    region = os.getenv("AWS_REGION")
    if region == "us-east-1":
        return f"https://{S3_BUCKET}.s3.amazonaws.com/{key}"
    return f"https://{S3_BUCKET}.s3.{region}.amazonaws.com/{key}"
