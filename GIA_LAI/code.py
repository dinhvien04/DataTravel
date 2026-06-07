import os
import mimetypes
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from boto3.s3.transfer import TransferConfig


# =========================
# Load biến môi trường
# =========================
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
BUCKET_NAME = os.getenv("AWS_BUCKET_NAME", "gia-lai-tourism-images")


# =========================
# Cấu hình thư mục local
# =========================
# Terminal của bạn đang đứng ở:
# C:\Users\nguye\Downloads\GIA_LAI-20260528T093821Z-3-001
#
# Bên trong đó có thư mục:
# GIA_LAI
#
# Code này sẽ upload nội dung BÊN TRONG GIA_LAI,
# không upload folder GIA_LAI lên S3.
LOCAL_ROOT_DIR = Path.cwd() / "GIA_LAI"


# Để rỗng thì upload thẳng ra bucket
# Ví dụ:
# S3_PREFIX = ""
# Kết quả: BIEN_HO/image/a.jpg
#
# Nếu đặt:
# S3_PREFIX = "dataset"
# Kết quả: dataset/BIEN_HO/image/a.jpg
S3_PREFIX = ""


# Nếu True: file đã tồn tại trên S3 và cùng dung lượng thì bỏ qua
SKIP_EXISTING_SAME_SIZE = True


# =========================
# Hàm lấy Content-Type
# =========================
def get_content_type(file_path: Path):
    content_type, _ = mimetypes.guess_type(str(file_path))
    return content_type or "application/octet-stream"


# =========================
# Hàm kiểm tra file đã có trên S3 chưa
# =========================
def s3_file_exists_same_size(s3, bucket_name: str, s3_key: str, local_file: Path) -> bool:
    """
    Trả về True nếu:
    - File đã tồn tại trên S3
    - Dung lượng file trên S3 bằng dung lượng file local

    Nếu file chưa tồn tại thì trả về False.
    """

    try:
        response = s3.head_object(
            Bucket=bucket_name,
            Key=s3_key
        )

        s3_size = response["ContentLength"]
        local_size = local_file.stat().st_size

        return s3_size == local_size

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")

        # File chưa tồn tại trên S3
        if error_code in ["404", "NoSuchKey", "NotFound"]:
            return False

        # Lỗi khác thì báo ra luôn
        raise


# =========================
# Hiển thị tiến trình upload
# =========================
class UploadProgress:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.total_size = file_path.stat().st_size
        self.uploaded = 0

    def __call__(self, bytes_amount):
        self.uploaded += bytes_amount

        if self.total_size == 0:
            percent = 100
        else:
            percent = self.uploaded / self.total_size * 100

        print(f"\rĐang upload: {percent:.2f}%", end="")


# =========================
# Tạo S3 key
# =========================
def build_s3_key(file_path: Path) -> str:
    """
    Chuyển đường dẫn local thành đường dẫn trên S3.

    Ví dụ:
    Local:
    GIA_LAI/BIEN_HO/image/a.jpg

    S3:
    BIEN_HO/image/a.jpg
    """

    relative_path = file_path.relative_to(LOCAL_ROOT_DIR).as_posix()

    if S3_PREFIX.strip():
        return f"{S3_PREFIX.strip('/')}/{relative_path}"

    return relative_path


# =========================
# Lấy danh sách file cần upload
# =========================
def get_all_files():
    files = []

    for path in LOCAL_ROOT_DIR.rglob("*"):
        if path.is_file():
            files.append(path)

    return files


# =========================
# Upload toàn bộ thư mục
# =========================
def upload_all_place_folders():
    if not LOCAL_ROOT_DIR.exists():
        raise FileNotFoundError(f"Không tìm thấy thư mục: {LOCAL_ROOT_DIR}")

    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        raise ValueError("Thiếu AWS_ACCESS_KEY_ID hoặc AWS_SECRET_ACCESS_KEY trong file .env")

    if not BUCKET_NAME:
        raise ValueError("Thiếu AWS_BUCKET_NAME trong file .env")

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

    files = get_all_files()

    total_files = len(files)
    uploaded_count = 0
    skipped_count = 0
    error_count = 0

    print("=" * 70)
    print(f"Thư mục gốc local: {LOCAL_ROOT_DIR}")
    print(f"Bucket S3: {BUCKET_NAME}")
    print(f"Region: {AWS_REGION}")
    print(f"S3 Prefix: {S3_PREFIX if S3_PREFIX else '(không có)'}")
    print(f"Tìm thấy {total_files} file cần xử lý.")
    print("=" * 70)

    for index, file_path in enumerate(files, start=1):
        s3_key = build_s3_key(file_path)

        print(f"\n[{index}/{total_files}]")
        print(f"Local: {file_path}")
        print(f"S3: s3://{BUCKET_NAME}/{s3_key}")

        try:
            # Kiểm tra file đã có trên S3 chưa
            if SKIP_EXISTING_SAME_SIZE:
                if s3_file_exists_same_size(s3, BUCKET_NAME, s3_key, file_path):
                    print("Bỏ qua: file đã có trên S3 và cùng dung lượng.")
                    skipped_count += 1
                    continue

            # Upload file
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

            print("\nUpload xong.")
            uploaded_count += 1

        except Exception as e:
            print(f"\nLỗi khi upload file này: {e}")
            error_count += 1

    print("\n" + "=" * 70)
    print("HOÀN TẤT")
    print(f"Tổng file xử lý: {total_files}")
    print(f"Đã upload: {uploaded_count}")
    print(f"Đã bỏ qua: {skipped_count}")
    print(f"Bị lỗi: {error_count}")
    print("=" * 70)


if __name__ == "__main__":
    upload_all_place_folders()