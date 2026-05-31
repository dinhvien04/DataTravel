import os
from pathlib import Path

import boto3
from dotenv import load_dotenv


load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
BUCKET_NAME = os.getenv("AWS_BUCKET_NAME", "gia-lai-tourism-images")

# Terminal của bạn đang ở:
# C:\Users\nguye\Downloads\GIA_LAI-20260528T093821Z-3-001
# Nên code sẽ tải vào thư mục GIA_LAI bên trong đó
LOCAL_ROOT_DIR = Path.cwd() / "GIA_LAI"

# Chỉ tải 5 folder này
FOLDERS_TO_DOWNLOAD = [
    "BIEN_HO",
    "DAM_THI_NAI",
    "KON_CHU_RANG",
    "THAP_BINH_LAM",
    "THAP_DUONG_LONG",
]

# False = nếu file đã có trên máy thì bỏ qua
# True = tải lại và ghi đè file cũ
OVERWRITE = False


def get_s3_client():
    if not AWS_ACCESS_KEY_ID:
        raise ValueError("Thiếu AWS_ACCESS_KEY_ID trong file .env")

    if not AWS_SECRET_ACCESS_KEY:
        raise ValueError("Thiếu AWS_SECRET_ACCESS_KEY trong file .env")

    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )


def list_files_in_s3_folder(s3, folder_name):
    prefix = folder_name.rstrip("/") + "/"
    keys = []

    paginator = s3.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]

            # Bỏ qua object dạng folder rỗng
            if key.endswith("/"):
                continue

            keys.append(key)

    return keys


def download_file(s3, key):
    local_file_path = LOCAL_ROOT_DIR / Path(key)

    local_file_path.parent.mkdir(parents=True, exist_ok=True)

    if local_file_path.exists() and not OVERWRITE:
        print(f"Đã có, bỏ qua: {local_file_path}")
        return

    print(f"Tải: s3://{BUCKET_NAME}/{key}")
    print(f"Lưu: {local_file_path}")

    s3.download_file(
        Bucket=BUCKET_NAME,
        Key=key,
        Filename=str(local_file_path)
    )

    print("Xong.\n")


def main():
    s3 = get_s3_client()

    LOCAL_ROOT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Bucket: {BUCKET_NAME}")
    print(f"Region: {AWS_REGION}")
    print(f"Thư mục lưu local: {LOCAL_ROOT_DIR}")
    print("-" * 70)

    total_downloaded_keys = 0

    for folder in FOLDERS_TO_DOWNLOAD:
        print(f"\nĐang kiểm tra folder: {folder}/")

        keys = list_files_in_s3_folder(s3, folder)

        if not keys:
            print(f"Không thấy file nào trong S3 folder: {folder}/")
            continue

        print(f"Tìm thấy {len(keys)} file trong {folder}/")

        for key in keys:
            download_file(s3, key)
            total_downloaded_keys += 1

    print("-" * 70)
    print(f"Hoàn tất. Đã xử lý {total_downloaded_keys} file.")


if __name__ == "__main__":
    main()