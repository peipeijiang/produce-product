#!/usr/bin/env python3
"""
提交任务到 Mock Server
"""
import json
import os
import requests
import base64
from datetime import datetime

def generate_task_code():
    """生成任务代码"""
    now = datetime.now()
    return f"SD-{now.strftime('%Y%m%d')}-bi10-{now.strftime('%H%M%S')}"

def convert_task_to_api_format(task_json):
    """将任务 JSON 转换为 Mock Server API 格式"""
    task = task_json["tasks"][0]

    return {
        "taskCode": task["video_id"],
        "description": task["description"],
        "prompt": task["prompt"],
        "realSubmit": task_json.get("realSubmit", False),
        "referenceFiles": task["referenceFiles"]
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
    project_dir = "/Users/shane/Downloads/Micro-Drama-Skills-main/projects/PV-002-戒指_product"

    # 获取所有 seedance_tasks_V*.json 文件
    for filename in sorted(os.listdir(project_dir)):
        if not (filename.startswith("seedance_tasks_V") and filename.endswith(".json")):
            continue

        json_path = os.path.join(project_dir, filename)

        with open(json_path, "r", encoding="utf-8") as f:
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
