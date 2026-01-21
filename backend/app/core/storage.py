import boto3
from botocore.exceptions import ClientError
from app.core.config import settings


class S3Client:
    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
        )
        self.bucket = settings.S3_BUCKET_NAME

    def upload_file(self, file_obj, object_name: str, content_type: str = None) -> bool:
        """Upload a file to an S3 bucket"""
        try:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type

            self.s3.upload_fileobj(
                file_obj, self.bucket, object_name, ExtraArgs=extra_args
            )
        except ClientError as e:
            print(f"S3 Upload Error: {e}")
            return False
        return True

    def generate_presigned_url(self, object_name: str, expiration=3600) -> str:
        """Generate a presigned URL to share an S3 object"""
        try:
            response = self.s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": object_name},
                ExpiresIn=expiration,
            )
        except ClientError as e:
            print(f"S3 Presign Error: {e}")
            return None
        return response

    def download_file(self, object_name: str, local_path: str) -> bool:
        """Download a file from S3 to local path"""
        try:
            self.s3.download_file(self.bucket, object_name, local_path)
        except ClientError as e:
            print(f"S3 Download Error: {e}")
            return False
        return True


s3_client = S3Client()
