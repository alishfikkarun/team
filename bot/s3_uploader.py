import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import logging
from config import Config
import io

logger = logging.getLogger(__name__)

class S3Uploader:
    def __init__(self):
        self.config = Config()
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=self.config.AWS_SECRET_ACCESS_KEY,
                region_name=self.config.AWS_REGION
            )
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
    
    async def upload_file(self, file_data: bytes, filename: str) -> str:
        """Upload file to S3 and return public URL"""
        try:
            # Upload file to S3
            file_obj = io.BytesIO(file_data)
            
            self.s3_client.upload_fileobj(
                file_obj,
                self.config.S3_BUCKET,
                filename,
                ExtraArgs={
                    'ContentType': 'image/webp',
                    'ACL': 'public-read'
                }
            )
            
            # Generate public URL
            public_url = f"https://{self.config.S3_BUCKET}.s3.{self.config.AWS_REGION}.amazonaws.com/{filename}"
            
            logger.info(f"File uploaded successfully: {public_url}")
            return public_url
            
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error uploading file: {e}")
            raise
    
    def delete_file(self, filename: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.config.S3_BUCKET,
                Key=filename
            )
            logger.info(f"File deleted successfully: {filename}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting file: {e}")
            return False
