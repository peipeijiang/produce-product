#!/usr/bin/env python3
"""
将参考图片转换为 base64 格式并更新 JSON 任务文件

使用方法：
    python3 convert_to_base64_fixed.py /path/to/project
"""
import json
import os
import sys
import base64

def image_to_base64(image_path):
    """将图片转换为 base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def update_task_json(json_file_path, project_dir):
    """更新任务 JSON 文件，将 referenceFiles 转换为 base64 格式

    支持 raw/ 和 keyframes/ 两个文件夹：
    - raw/: 实拍图片路径（如 "raw/image.jpg"）
    - keyframes/: 参考图片路径（如 "keyframes/image.jpg"）
    """
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for task in data["tasks"]:
        new_reference_files = []
        for ref_file in task["referenceFiles"]:
            # ref_file 可能是字符串或字典
            if isinstance(ref_file, dict):
                file_name = ref_file.get("fileName", "")
                # 如果没有 base64，则计算
                if not ref_file.get("base64"):
                    # 获取图片完整路径（支持 temp_raw/、raw/ 和 keyframes/）
                    if file_name.startswith("temp_raw/"):
                        image_path = os.path.join(project_dir, file_name)
                    elif file_name.startswith("raw/"):
                        image_path = os.path.join(project_dir, file_name)
                    elif file_name.startswith("keyframes/"):
                        image_path = os.path.join(project_dir, file_name)
                    else:
                        # 默认从 keyframes/ 加载
                        image_path = os.path.join(project_dir, "keyframes", file_name)

                    # 转换为 base64
                    if os.path.exists(image_path):
                        b64_data = image_to_base64(image_path)
                        new_reference_files.append({
                            "fileName": file_name,
                            "base64": b64_data
                        })
                    else:
                        print(f"⚠️  Warning: Image not found: {image_path}")
                else:
                    # 已经有 base64，直接使用
                    new_reference_files.append(ref_file)
            else:
                # 如果是字符串，尝试作为相对路径处理
                if ref_file.startswith("temp_raw/"):
                    image_path = os.path.join(project_dir, ref_file)
                elif ref_file.startswith("raw/"):
                    image_path = os.path.join(project_dir, ref_file)
                elif ref_file.startswith("keyframes/"):
                    image_path = os.path.join(project_dir, ref_file)
                else:
                    # 默认从 keyframes/ 加载
                    image_path = os.path.join(project_dir, "keyframes", ref_file)

                # 获取文件名（保留路径前缀）
                file_name = ref_file

                # 转换为 base64
                if os.path.exists(image_path):
                    b64_data = image_to_base64(image_path)
                    new_reference_files.append({
                        "fileName": file_name,
                        "base64": b64_data
                    })
                else:
                    print(f"⚠️  Warning: Image not found: {image_path}")

        task["referenceFiles"] = new_reference_files

    # 保存更新后的 JSON
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Updated: {os.path.basename(json_file_path)}")

def main():
    project_dir = sys.argv[1] if len(sys.argv) > 1 else "/Users/shane/Downloads/Micro-Drama-Skills-main/projects/PV-002-戒指_product"

    # 获取所有 seedance_tasks_*.json 文件
    for filename in os.listdir(project_dir):
        if filename.startswith("seedance_tasks_") and filename.endswith(".json"):
            json_path = os.path.join(project_dir, filename)
            update_task_json(json_path, project_dir)

    print("\n✅ All task files updated with base64 images")

if __name__ == "__main__":
    main()
