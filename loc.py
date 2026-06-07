import os
import shutil


def flatten_duplicate_folders(root_dir):
    print(f"🚀 Bắt đầu quét và tối ưu cấu trúc tại: {root_dir}\n")

    # Đi từ dưới lên (topdown=False) để xử lý thư mục con trước, tránh lỗi khi di chuyển
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        for dirname in dirnames:
            current_folder_path = os.path.join(dirpath, dirname)

            # Lấy tên của thư mục cha trực tiếp
            parent_folder_name = os.path.basename(dirpath)

            # Nếu tên thư mục con TRÙNG với tên thư mục cha
            if dirname == parent_folder_name:
                print(f"📁 Phát hiện thư mục lồng nhau: {current_folder_path}")

                # 1. Di chuyển toàn bộ nội dung bên trong thư mục con ra thư mục cha tạm thời
                # Để tránh xung đột, ta chuyển tạm ra một thư mục temp ngoài root_dir rồi đưa về lại thư mục cha
                temp_parent = os.path.dirname(dirpath)
                temp_dir = os.path.join(temp_parent, f"_temp_{dirname}")

                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)

                # Di chuyển nội dung của thư mục con trùng tên vào temp
                for item in os.listdir(current_folder_path):
                    shutil.move(os.path.join(current_folder_path, item), temp_dir)

                # 2. Xóa thư mục con giờ đã rỗng và cả thư mục cha cũ đi
                shutil.rmtree(dirpath)

                # 3. Đổi tên thư mục temp thành tên thư mục cha ban đầu
                os.rename(temp_dir, dirpath)
                print(f"✅ Đã gộp và sửa xong: {dirpath}\n")


if __name__ == "__main__":
    # Thay đường dẫn này bằng đường dẫn đến thư mục chứa dữ liệu của bạn
    # Ví dụ dựa trên ảnh của bạn:
    TARGET_DIR = r"C:\Users\nguye\Downloads\GIA_LAI-20260528T093821Z-3-001"

    if os.path.exists(TARGET_DIR):
        flatten_duplicate_folders(TARGET_DIR)
        print("🎉 Hoàn thành! Kiểm tra lại cấu trúc thư mục trong VS Code nhé.")
    else:
        print("❌ Đường dẫn không tồn tại. Vui lòng kiểm tra lại!")