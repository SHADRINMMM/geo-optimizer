import boto3
from botocore.config import Config
from app.core.config import get_settings

settings = get_settings()

s3_client = boto3.client(
    "s3",
    endpoint_url=settings.S3_ENDPOINT_URL,
    aws_access_key_id=settings.S3_ACCESS_KEY_ID,
    aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4"),
    region_name="auto",
)


def upload_file(key: str, content: str | bytes, content_type: str = "text/plain") -> str:
    """Upload file to R2, return public URL."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    s3_client.put_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=key,
        Body=content,
        ContentType=content_type,
    )
    return f"{settings.PUBLIC_R2_PUBLIC_BASE_URL}/{key}"


def download_file(key: str) -> bytes:
    response = s3_client.get_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
    return response["Body"].read()


def delete_file(key: str) -> None:
    s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=key)


def get_public_url(key: str) -> str:
    return f"{settings.PUBLIC_R2_PUBLIC_BASE_URL}/{key}"
