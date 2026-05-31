import os
from collections import defaultdict

import boto3
from dotenv import load_dotenv


load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")


def get_s3_client():
    if not AWS_ACCESS_KEY_ID:
        raise ValueError("Thiếu AWS_ACCESS_KEY_ID trong file .env")

    if not AWS_SECRET_ACCESS_KEY:
        raise ValueError("Thiếu AWS_SECRET_ACCESS_KEY trong file .env")

    if not BUCKET_NAME:
        raise ValueError("Thiếu AWS_BUCKET_NAME trong file .env")

    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )


def list_all_s3_keys(s3):
    keys = []

    paginator = s3.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=BUCKET_NAME):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])

    return keys


def build_folder_tree(keys):
    tree = defaultdict(set)

    for key in keys:
        parts = key.split("/")

        # Bỏ qua file nằm ngay ngoài bucket
        if len(parts) <= 1:
            continue

        for i in range(len(parts) - 1):
            parent = "/".join(parts[:i])
            folder = parts[i]
            tree[parent].add(folder)

    return tree


def print_tree(tree, parent="", level=0):
    folders = sorted(tree.get(parent, []))

    for folder in folders:
        indent = "    " * level
        print(f"{indent}📁 {folder}/")

        if parent:
            child_parent = f"{parent}/{folder}"
        else:
            child_parent = folder

        print_tree(tree, child_parent, level + 1)


def main():
    s3 = get_s3_client()

    print(f"Bucket: {BUCKET_NAME}")
    print(f"Region: {AWS_REGION}")
    print("-" * 60)

    keys = list_all_s3_keys(s3)

    if not keys:
        print("Bucket đang trống, chưa có file nào.")
        return

    tree = build_folder_tree(keys)

    print("Danh sách thư mục trong S3:")
    print("-" * 60)
    print_tree(tree)

    print("-" * 60)
    print(f"Tổng số file/object: {len(keys)}")


if __name__ == "__main__":
    main()