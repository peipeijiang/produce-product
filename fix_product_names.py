#!/usr/bin/env python3
"""
修复任务 JSON 中的产品名称为英文
"""
import json
import os
import glob

def fix_product_name(json_file):
    """修复产品名称为英文"""
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 简单的产品名翻译
    cn_to_en = {
        "Lesure 宠物床": "Lesure Pet Bed",
        "宠物床": "Pet Bed",
        "智能戒指": "Smart Ring",
        "智能手环": "Smart Band",
        "智能手表": "Smart Watch"
    }

    for task in data["tasks"]:
        prompt = task["prompt"]

        # 替换产品名称
        for cn_name, en_name in cn_to_en.items():
            prompt = prompt.replace(cn_name, en_name)

        task["prompt"] = prompt

    # 保存修改后的文件
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Fixed: {os.path.basename(json_file)}")

def main():
    project_dir = "/Users/shane/Downloads/Micro-Drama-Skills-main/projects/PV-001_宠物窝_product"

    # 获取所有 seedance_tasks_V*.json 文件
    for json_file in sorted(glob.glob(os.path.join(project_dir, "seedance_tasks_V*.json"))):
        fix_product_name(json_file)

    print(f"\n✅ All tasks updated - fixed product names to English")

if __name__ == "__main__":
    main()
