#!/usr/bin/env python3
"""
提交指定项目的任务到 Mock Server
"""
import json
import os
import requests
import glob
import sys

def convert_task_to_api_format(task_json):
    """将任务 JSON 转换为 Mock Server API 格式"""
    task = task_json["tasks"][0]

    return {
        "taskCode": task["video_id"],
        "description": task["description"],
        "prompt": task["prompt"],
        "realSubmit": task_json.get("realSubmit", False),
        "referenceFiles": task["referenceFiles"],
        "modelConfig": task.get("modelConfig", {})
    }

def submit_to_mock_server(api_data):
    """提交到 Mock Server"""
    url = "http://localhost:3456/api/tasks/push"

    try:
        response = requests.post(url, json=api_data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            return True, result
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 submit_project_tasks.py /path/to/project")
        sys.exit(1)

    project_dir = sys.argv[1]

    # 只提交新格式的 V 文件（V1_Premium, V2_Smart 等）
    new_format_patterns = [
        "V1_Premium_Luxury",
        "V2_Smart_Features",
        "V3_Lifestyle_Daily",
        "V4_Performance_Quality",
        "V5_Best_Value"
    ]

    # 获取所有 seedance_tasks_V*.json 文件
    for json_file in sorted(glob.glob(os.path.join(project_dir, "seedance_tasks_V*.json"))):
        filename = os.path.basename(json_file)

        # 只提交新格式的文件
        if not any(pattern in filename for pattern in new_format_patterns):
            continue

        with open(json_file, "r", encoding="utf-8") as f:
            task_json = json.load(f)

        # 转换格式
        api_data = convert_task_to_api_format(task_json)

        print(f"📤 Submitting: {filename}")
        print(f"   Task Code: {api_data['taskCode']}")
        print(f"   Description: {api_data['description'][:50]}...")

        # 提交
        success, result = submit_to_mock_server(api_data)

        if success:
            print(f"   ✅ Success: {result}")
        else:
            print(f"   ❌ Failed: {result}")

        print()

if __name__ == "__main__":
    main()
