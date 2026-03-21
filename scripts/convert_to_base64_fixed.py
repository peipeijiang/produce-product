#!/usr/bin/env python3
"""
将参考图片转换为 base64 格式并更新 JSON 任务文件
"""
import json
import os
import base64
import sys

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
            # ref_file 可能是字符串或字典
            if isinstance(ref_file, dict):
                file_name = ref_file.get("fileName", "")
                # 如果没有 base64，则计算
                if not ref_file.get("base64"):
                    # 获取图片完整路径
                    if file_name.startswith("keyframes/"):
                        image_path = os.path.join(project_dir, file_name)
                    elif file_name.startswith("raw/"):
                        image_path = os.path.join(project_dir, file_name)
                    else:
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
                if ref_file.startswith("keyframes/"):
                    image_path = os.path.join(project_dir, ref_file)
                elif ref_file.startswith("raw/"):
                    image_path = os.path.join(project_dir, ref_file)
                else:
                    image_path = os.path.join(project_dir, "keyframes", ref_file)

                # 获取文件名
                file_name = os.path.basename(ref_file)

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
    if len(sys.argv) < 2:
        print("用法: python3 scripts/convert_to_base64_fixed.py /path/to/project")
        sys.exit(1)

    project_dir = sys.argv[1]
    if not os.path.isdir(project_dir):
        print(f"❌ 错误: 项目目录不存在: {project_dir}")
        sys.exit(1)

    # 获取所有 seedance_tasks_*.json 文件
    updated_count = 0
    for filename in os.listdir(project_dir):
        if filename.startswith("seedance_tasks_") and filename.endswith(".json"):
            json_path = os.path.join(project_dir, filename)
            update_task_json(json_path, project_dir)
            updated_count += 1

    if updated_count == 0:
        print("\n⚠️ 未找到 seedance_tasks_*.json 文件")
        sys.exit(1)

    print(f"\n✅ 已更新 {updated_count} 个任务文件（referenceFiles -> base64）")

if __name__ == "__main__":
    main()
