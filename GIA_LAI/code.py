import os
import mimetypes
from pathlib import Path

import boto3
from dotenv import load_dotenv
from boto3.s3.transfer import TransferConfig


load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
BUCKET_NAME = os.getenv("AWS_BUCKET_NAME", "gia-lai-tourism-images")

# Vì terminal của bạn đang ở:
# C:\Users\nguye\Downloads\GIA_LAI-20260528T093821Z-3-001
# nên code sẽ lấy thư mục con GIA_LAI bên trong đó.
# Như vậy khi upload lên S3 sẽ KHÔNG có folder GIA_LAI.
LOCAL_ROOT_DIR = Path.cwd() / "GIA_LAI"

# Để rỗng để upload thẳng ra bucket
S3_PREFIX = ""


def get_content_type(file_path: Path):
    content_type, _ = mimetypes.guess_type(str(file_path))
    return content_type or "application/octet-stream"


class UploadProgress:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.total_size = file_path.stat().st_size
        self.uploaded = 0

    def __call__(self, bytes_amount):
        self.uploaded += bytes_amount
        percent = self.uploaded / self.total_size * 100
        print(f"\rĐang upload: {percent:.2f}%", end="")


def upload_all_place_folders():
    if not LOCAL_ROOT_DIR.exists():
        raise FileNotFoundError(f"Không tìm thấy thư mục: {LOCAL_ROOT_DIR}")

    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        raise ValueError("Thiếu AWS_ACCESS_KEY_ID hoặc AWS_SECRET_ACCESS_KEY trong file .env")

    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )

    config = TransferConfig(
        multipart_threshold=8 * 1024 * 1024,
        multipart_chunksize=8 * 1024 * 1024,
        max_concurrency=4,
        use_threads=True,
    )

    files = [p for p in LOCAL_ROOT_DIR.rglob("*") if p.is_file()]

    print(f"Thư mục gốc local: {LOCAL_ROOT_DIR}")
    print(f"Bucket S3: {BUCKET_NAME}")
    print(f"Tìm thấy {len(files)} file cần upload.")
    print("-" * 70)

    for index, file_path in enumerate(files, start=1):
        # Đây là phần quan trọng:
        # relative_to(LOCAL_ROOT_DIR) giúp bỏ folder GIA_LAI ra khỏi đường dẫn S3
        relative_path = file_path.relative_to(LOCAL_ROOT_DIR).as_posix()

        if S3_PREFIX:
            s3_key = f"{S3_PREFIX.strip('/')}/{relative_path}"
        else:
            s3_key = relative_path

        print(f"\n[{index}/{len(files)}]")
        print(f"Local: {file_path}")
        print(f"S3: s3://{BUCKET_NAME}/{s3_key}")

        s3.upload_file(
            Filename=str(file_path),
            Bucket=BUCKET_NAME,
            Key=s3_key,
            ExtraArgs={
                "ContentType": get_content_type(file_path)
            },
            Config=config,
            Callback=UploadProgress(file_path),
        )

        print("\nXong.")

    print("-" * 70)
    print("Upload toàn bộ dữ liệu xong!")


if __name__ == "__main__":
    upload_all_place_folders()  


    