#!/usr/bin/env python3
"""
移除任务 JSON 中的字幕要求（仅保留英文口播）
"""
import json
import os
import glob

def remove_subtitle_requirement(json_file):
    """移除字幕要求"""
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for task in data["tasks"]:
        # 移除字幕相关内容
        prompt = task["prompt"]

        # 移除 "Include matching English subtitles."
        if "Include matching English subtitles." in prompt:
            prompt = prompt.replace("Include matching English subtitles.", "")

        # 替换 "Include English subtitles matching all text overlays."
        if "Include English subtitles matching all text overlays." in prompt:
            prompt = prompt.replace("Include English subtitles matching all text overlays.", "")

        # 移除 "Include ENGLISH SUBTITLES matching all text overlays."
        if "Include ENGLISH SUBTITLES matching all text overlays." in prompt:
            prompt = prompt.replace("Include ENGLISH SUBTITLES matching all text overlays.", "")

        task["prompt"] = prompt.strip()

        # 移除 tags 中的 SUBTITLE
        if "SUBTITLE" in task["tags"]:
            task["tags"].remove("SUBTITLE")

    # 保存修改后的文件
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Updated: {os.path.basename(json_file)}")

def main():
    project_dir = "/Users/shane/Downloads/Micro-Drama-Skills-main/projects/PV-001_宠物窝_product"

    # 获取所有 seedance_tasks_V*.json 文件
    for json_file in sorted(glob.glob(os.path.join(project_dir, "seedance_tasks_V*.json"))):
        remove_subtitle_requirement(json_file)

    print(f"\n✅ All tasks updated - removed subtitle requirement")

if __name__ == "__main__":
    main()
