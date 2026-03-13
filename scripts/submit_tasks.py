#!/usr/bin/env python3
"""
提交任务到 Mock Server
"""
import json
import os
import requests
import sys

def normalize_model_config(model_config):
    """确保模型配置格式兼容扩展选择器（duration 需为 '15s' 这种字符串）"""
    cfg = dict(model_config or {})

    duration = cfg.get("duration")
    if isinstance(duration, (int, float)):
        cfg["duration"] = f"{int(duration)}s"
    elif isinstance(duration, str):
        d = duration.strip()
        if d.isdigit():
            cfg["duration"] = f"{d}s"

    return cfg


def convert_task_to_api_format(task_json):
    """将任务 JSON 转换为 Mock Server API 格式（保留 modelConfig 等字段）"""
    task = task_json["tasks"][0]

    return {
        "taskCode": task["video_id"],
        "description": task["description"],
        "prompt": task["prompt"],
        "realSubmit": task_json.get("realSubmit", False),
        "referenceFiles": task.get("referenceFiles", []),
        "modelConfig": normalize_model_config(task.get("modelConfig", {})),
        "tags": task.get("tags", []),
        "priority": task.get("priority", 1),
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
        print("用法: python3 scripts/submit_tasks.py /path/to/project")
        sys.exit(1)

    project_dir = sys.argv[1]
    if not os.path.isdir(project_dir):
        print(f"❌ 错误: 项目目录不存在: {project_dir}")
        sys.exit(1)

    # 获取所有 seedance_tasks_V*.json 文件
    submitted_count = 0
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
            submitted_count += 1
        else:
            print(f"   ❌ Failed: {result}")

        print()

    if submitted_count == 0:
        print("⚠️ 未找到可提交任务文件：seedance_tasks_V*.json")
        sys.exit(1)

    print(f"✅ 提交完成：{submitted_count} 个任务文件")

if __name__ == "__main__":
    main()
