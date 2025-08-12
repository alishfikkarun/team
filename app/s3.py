import boto3
from botocore.config import Config as BotoConfig
from .config import cfg


def get_s3_client():
    return boto3.client(
        "s3",
        region_name=cfg.AWS_REGION,
        aws_access_key_id=cfg.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=cfg.AWS_SECRET_ACCESS_KEY,
        config=BotoConfig(signature_version="s3v4"),
    )


def s3_public_url(bucket: str, region: str, key: str) -> str:
    # us-east-1 uses s3.amazonaws.com
    if region == "us-east-1":
        return f"https://{bucket}.s3.amazonaws.com/{key}"
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"


def upload_bytes_public(data: bytes, key: str, content_type: str = "application/octet-stream") -> str:
    s3 = get_s3_client()
    extra_args = {"ContentType": content_type}
    # If bucket allows ACLs, we can set public-read; otherwise rely on bucket policy
    try:
        s3.put_object(Bucket=cfg.S3_BUCKET, Key=key, Body=data, ACL="public-read", **extra_args)
    except Exception:
        # Retry without ACL for buckets with ACLs disabled
        s3.put_object(Bucket=cfg.S3_BUCKET, Key=key, Body=data, **extra_args)
    return s3_public_url(cfg.S3_BUCKET, cfg.AWS_REGION, key)
