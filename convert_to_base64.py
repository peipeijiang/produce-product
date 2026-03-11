#!/usr/bin/env python3
"""
将参考图片转换为 base64 格式并更新 JSON 任务文件
"""
import json
import os
import base64

def image_to_base64(image_path):
    """将图片转换为 base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def update_task_json(json_file_path, project_dir):
    """更新任务 JSON 文件，将 referenceFiles 转换为 base64 格式"""
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for task in data["tasks"]:
        new_reference_files = []
        for ref_file in task["referenceFiles"]:
            # 获取图片完整路径
            if ref_file.startswith("keyframes/"):
                image_path = os.path.join(project_dir, ref_file)
            else:
                image_path = ref_file

            # 转换为 base64
            if os.path.exists(image_path):
                b64_data = image_to_base64(image_path)
                file_name = os.path.basename(ref_file)
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
    project_dir = "/Users/shane/Downloads/Micro-Drama-Skills-main/projects/PV-002-戒指_product"

    # 获取所有 seedance_tasks_*.json 文件
    for filename in os.listdir(project_dir):
        if filename.startswith("seedance_tasks_") and filename.endswith(".json"):
            json_path = os.path.join(project_dir, filename)
            update_task_json(json_path, project_dir)

    print("\n✅ All task files updated with base64 images")

if __name__ == "__main__":
    main()
