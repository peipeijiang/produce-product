#!/usr/bin/env python3
"""
推送任务到 Mock Server

读取 seedance_tasks_*.json，展开参考图为 base64，推送到 Mock Server
"""
import json
import base64
import mimetypes
import requests
import sys
import os
from pathlib import Path

API_BASE = "http://localhost:3456/api/tasks/push"


def expand_refs(refs, proj_dir):
    """将相对路径展开为 base64 对象"""
    result = []
    for r in refs:
        path = os.path.join(proj_dir, r)
        if not os.path.exists(path):
            print(f"  ⚠️ 文件不存在: {path}")
            continue

        filename = os.path.basename(r)
        with open(path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode()

        mime = mimetypes.guess_type(path)[0] or 'image/png'
        result.append({
            "fileName": filename,
            "base64": f"data:{mime};base64,{b64}",
            "fileType": mime,
            "mediaType": "image"
        })
    return result


def push_task(task_json_path):
    """推送单个任务"""
    proj_dir = os.path.dirname(task_json_path)

    with open(task_json_path) as f:
        task_data = json.load(f)

    # 展开 reference files
    task = task_data['tasks'][0]
    task['referenceFiles'] = expand_refs(task.get('referenceFiles', []), proj_dir)

    # 推送
    resp = requests.post(API_BASE, json=task, timeout=60)
    result = resp.json()

    if result.get("success"):
        task_codes = result.get("taskCodes", [])
        print(f"  ✅ 成功: {task_codes}")
        return task_codes
    else:
        print(f"  ❌ 失败: {result}")
        return []


def push_all_tasks(project_dir, pattern="seedance_tasks_*.json"):
    """推送所有匹配的任务文件"""
    import glob

    project_path = Path(project_dir)
    task_files = list(project_path.glob(pattern))

    if not task_files:
        print(f"❌ 未找到任务文件: {pattern}")
        return []

    print(f"📤 找到 {len(task_files)} 个任务文件")
    print("=" * 50)

    all_codes = []
    for tf in task_files:
        print(f"\n📄 {tf.name}")
        codes = push_task(str(tf))
        all_codes.extend(codes)

    print("\n" + "=" * 50)
    print(f"✅ 推送完成！共 {len(all_codes)} 个任务")

    for code in all_codes:
        print(f"   - {code}")

    return all_codes


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 push_tasks.py /path/to/project           # 推送所有")
        print("  python3 push_tasks.py /path/to/project V1       # 只推送 V1")
        sys.exit(1)

    project_dir = sys.argv[1]

    if len(sys.argv) >= 3:
        version = sys.argv[2]
        pattern = f"seedance_tasks_{version}*.json"
    else:
        pattern = "seedance_tasks_*.json"

    print("=" * 50)
    print(f"📁 项目: {project_dir}")
    print(f"📋 模式: {pattern}")
    print("=" * 50)

    # 检查 Mock Server
    try:
        resp = requests.get("http://localhost:3456/api/config", timeout=5)
        if resp.status_code != 200:
            print("❌ Mock Server 未运行")
            sys.exit(1)
    except:
        print("❌ Mock Server 未运行")
        sys.exit(1)

    codes = push_all_tasks(project_dir, pattern)

    if codes:
        print("\n✅ 任务已推送，浏览器插件将自动执行")
    else:
        print("\n❌ 推送失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
