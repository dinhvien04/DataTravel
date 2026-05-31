from pathlib import Path
import re
import shutil


# =========================
# 1. ĐƯỜNG DẪN GỐC
# =========================

ROOT_PATH = r"C:\Users\nguye\Downloads\GIA_LAI-20260528T093821Z-3-001\GIA_LAI"

CREATE_BACKUP = True


# =========================
# 2. HÀM NHẬN DIỆN HEADING
# =========================

def get_heading_text(line):
    """
    Dòng dạng:
    1. overview.docx - Nhà thờ Đá Ghềnh Ráng
    2. Mục tiêu
    3. Tên gọi và định danh địa điểm
    """
    match = re.match(r"^\s*\d+\.\s+(.+?)\s*$", line.strip())
    if match:
        return match.group(1).strip()
    return None


def is_muc_tieu_heading(text):
    if not text:
        return False

    text = text.lower().strip()

    return (
        text == "mục tiêu"
        or text == "mục tiêu dữ liệu"
        or text.startswith("mục tiêu ")
    )


def is_fake_intro_heading(text):
    if not text:
        return False

    text_lower = text.lower().strip()

    fake_keywords = [
        ".docx",
        "dữ liệu trải nghiệm",
        "dữ liệu tổng quan",
        "dữ liệu vận chuyển",
        "dữ liệu vé",
        "dữ liệu dịch vụ",
        "dữ liệu xung quanh",
        "dữ liệu lưu ý",
        "faq cho chatbot",
        "chatbot rag",
        "lưu ý và review",
    ]

    for key in fake_keywords:
        if key in text_lower:
            return True

    return False


# =========================
# 3. SỬA 1 FILE TXT
# =========================

def fix_one_txt_file(txt_file):
    with open(txt_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    heading_indexes = []

    for i, line in enumerate(lines):
        heading = get_heading_text(line)
        if heading:
            heading_indexes.append(i)

    if not heading_indexes:
        return False

    sections = []

    for idx, start in enumerate(heading_indexes):
        end = heading_indexes[idx + 1] if idx + 1 < len(heading_indexes) else len(lines)
        heading = get_heading_text(lines[start])

        sections.append({
            "start": start,
            "end": end,
            "heading": heading
        })

    remove_ranges = []

    # Trường hợp:
    # 1. overview.docx - ...
    # 2. Mục tiêu
    # => xóa cả mục 1 và mục 2
    if len(sections) >= 2:
        first_heading = sections[0]["heading"]
        second_heading = sections[1]["heading"]

        if is_fake_intro_heading(first_heading) and is_muc_tieu_heading(second_heading):
            remove_ranges.append((sections[0]["start"], sections[0]["end"]))
            remove_ranges.append((sections[1]["start"], sections[1]["end"]))

    # Trường hợp còn sót:
    # 1. Mục tiêu
    # => xóa mục 1
    if len(sections) >= 1:
        first_heading = sections[0]["heading"]

        if is_muc_tieu_heading(first_heading):
            remove_ranges.append((sections[0]["start"], sections[0]["end"]))

    # Trường hợp:
    # 1. overview.docx - ...
    # nhưng không có mục tiêu phía sau
    # => xóa riêng mục 1
    if len(sections) >= 1:
        first_heading = sections[0]["heading"]

        if is_fake_intro_heading(first_heading):
            remove_ranges.append((sections[0]["start"], sections[0]["end"]))

    if not remove_ranges:
        return False

    remove_line_indexes = set()

    for start, end in remove_ranges:
        for i in range(start, end):
            remove_line_indexes.add(i)

    kept_lines = []

    for i, line in enumerate(lines):
        if i not in remove_line_indexes:
            kept_lines.append(line)

    # Xóa dòng trắng đầu file
    while kept_lines and kept_lines[0].strip() == "":
        kept_lines.pop(0)

    # Đánh lại số thứ tự
    fixed_lines = []
    section_number = 1

    for line in kept_lines:
        heading = get_heading_text(line)

        if heading:
            fixed_lines.append(f"{section_number}. {heading}\n")
            section_number += 1
        else:
            fixed_lines.append(line)

    # Xóa dòng trắng quá nhiều
    final_lines = []
    blank_count = 0

    for line in fixed_lines:
        if line.strip() == "":
            blank_count += 1
            if blank_count <= 1:
                final_lines.append("\n")
        else:
            blank_count = 0
            final_lines.append(line)

    with open(txt_file, "w", encoding="utf-8") as f:
        f.writelines(final_lines)

    return True


# =========================
# 4. SỬA TOÀN BỘ TXT
# =========================

def fix_all_txt_files(root_path):
    root_path = Path(root_path)

    if not root_path.exists():
        print("Đường dẫn không tồn tại.")
        return

    txt_files = list(root_path.rglob("*.txt"))

    txt_files = [
        f for f in txt_files
        if "_backup_txt_before_fix" not in str(f)
    ]

    if not txt_files:
        print("Không tìm thấy file .txt nào.")
        return

    backup_dir = root_path / "_backup_txt_before_fix"

    if CREATE_BACKUP:
        backup_dir.mkdir(exist_ok=True)

    fixed_count = 0
    skipped_count = 0
    error_count = 0

    print(f"Tìm thấy {len(txt_files)} file .txt")
    print("-" * 60)

    for txt_file in txt_files:
        try:
            if CREATE_BACKUP:
                relative_path = txt_file.relative_to(root_path)
                backup_file = backup_dir / relative_path
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(txt_file, backup_file)

            changed = fix_one_txt_file(txt_file)

            if changed:
                fixed_count += 1
                print(f"Đã sửa: {txt_file}")
            else:
                skipped_count += 1
                print(f"Bỏ qua: {txt_file}")

        except Exception as e:
            error_count += 1
            print(f"Lỗi file: {txt_file}")
            print(f"Chi tiết lỗi: {e}")

    print("-" * 60)
    print("HOÀN TẤT")
    print(f"Đã sửa: {fixed_count}")
    print(f"Bỏ qua: {skipped_count}")
    print(f"Lỗi: {error_count}")

    if CREATE_BACKUP:
        print(f"Backup nằm ở: {backup_dir}")


# =========================
# 5. CHẠY
# =========================

fix_all_txt_files(ROOT_PATH)