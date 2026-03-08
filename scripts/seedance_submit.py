#!/usr/bin/env python3
"""
Seedance 任务提交脚本

用法:
    python seedance_submit.py /path/to/project              # 模拟提交
    python seedance_submit.py /path/to/project --real       # 真实提交
    python seedance_submit.py /path/to/project --batch 10   # 批次大小
    python seedance_submit.py /path/to/project --ep 1-5    # 指定集数
    python seedance_submit.py /path/to/project --wait       # 等待任务完成
"""
import json
import base64
import os
import sys
import time
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


API_BASE = "http://localhost:3456/api/tasks/push"
DEFAULT_BATCH_SIZE = 10
POLL_INTERVAL = 10  # 轮询间隔（秒）
MAX_WAIT_TIME = 3600  # 最大等待时间（秒）


def expand_reference_files(ref_paths, project_dir):
    """将相对路径展开为 base64 对象，并在 prompt 中添加引用语法"""
    result = []
    ref_syntax = []

    for rel_path in ref_paths:
        abs_path = project_dir / rel_path
        if not abs_path.exists():
            print(f"  ⚠️ 文件不存在: {abs_path}")
            continue
        file_name = abs_path.name
        # 提取文件名作为引用 key (不含扩展名或用原名)
        ref_key = file_name.split('.')[0]
        ref_syntax.append(f"(@{file_name})")

        mime_type = mimetypes.guess_type(str(abs_path))[0] or "image/png"
        with open(abs_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        result.append({
            "fileName": file_name,
            "base64": f"data:{mime_type};base64,{b64}",
            "fileType": mime_type,
            "mediaType": "image"
        })

    # 返回 (展开后的文件列表, prompt引用语法)
    return result, " ".join(ref_syntax)


def get_task_status(task_code):
    """获取任务状态"""
    try:
        resp = requests.get(f"{API_BASE}/api/tasks", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for task in data.get("tasks", []):
                if task.get("taskCode") == task_code:
                    return task.get("status"), task
    except Exception as e:
        print(f"  ⚠️ 获取状态失败: {e}")
    return None, None


def wait_for_task_complete(task_code, max_wait=MAX_WAIT_TIME):
    """等待任务完成，返回视频URL"""
    print(f"\n  ⏳ 等待任务 {task_code} 完成...")
    start_time = time.time()

    while time.time() - start_time < max_wait:
        status, task_info = get_task_status(task_code)
        if status in ["completed", "success", "done"]:
            # 尝试获取视频URL
            video_url = None
            if task_info:
                # 根据实际API响应结构获取URL
                video_url = task_info.get("outputUrl") or task_info.get("videoUrl") or task_info.get("url")
            print(f"  ✅ 任务完成: {task_code}")
            return True, video_url
        elif status in ["failed", "error"]:
            print(f"  ❌ 任务失败: {task_code}")
            return False, None
        else:
            print(f"  ⏳ 状态: {status}...")
            time.sleep(POLL_INTERVAL)

    print(f"  ⚠️ 等待超时")
    return False, None


def fetch_completed_videos(task_codes):
    """获取已完成任务的视频URL"""
    video_map = {}
    for task_code in task_codes:
        status, video_url = wait_for_task_complete(task_code)
        if status and video_url:
            video_map[task_code] = video_url
    return video_map


def filter_by_episodes(tasks, ep_range):
    """按集数过滤任务"""
    if not ep_range:
        return tasks
    ep_codes = {f"EP{e:02d}" for e in ep_range}
    filtered = []
    for task in tasks:
        tags = task.get("tags", [])
        if any(ep in tags for ep in ep_codes):
            filtered.append(task)
    return filtered


def submit_batch(tasks, api_url=API_BASE):
    """提交一批任务"""
    try:
        response = requests.post(api_url, json={"tasks": tasks}, timeout=180)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return {
                    "success": True,
                    "taskCodes": result.get("taskCodes", []),
                    "failed": 0
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "未知错误"),
                    "failed": len(tasks)
                }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "failed": len(tasks)
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "failed": len(tasks)
        }


def submit_tasks(project_dir, real_submit=False, batch_size=DEFAULT_BATCH_SIZE, ep_range=None):
    """提交任务"""
    tasks_file = project_dir / "seedance_project_tasks.json"

    if not tasks_file.exists():
        # 尝试从单集目录加载
        print("⚠️ seedance_project_tasks.json 不存在，尝试从各集目录聚合...")
        return None

    with open(tasks_file, encoding="utf-8") as f:
        data = json.load(f)

    tasks = data.get("tasks", [])

    # 过滤集数
    if ep_range:
        tasks = filter_by_episodes(tasks, ep_range)

    if not tasks:
        print("⚠️ 没有任务可提交")
        return None

    # 设置 realSubmit
    for task in tasks:
        task["realSubmit"] = real_submit

    # 展开 referenceFiles
    print(f"\n📎 展开 {len(tasks)} 个任务的 referenceFiles...")
    for task in tasks:
        expanded_files, _ = expand_reference_files(
            task.get("referenceFiles", []),
            project_dir
        )
        task["referenceFiles"] = expanded_files

    # 分批提交
    total = len(tasks)
    batches = [tasks[i:i + batch_size] for i in range(0, total, batch_size)]

    all_codes = []
    failed_items = []

    print(f"\n📤 提交 {total} 个任务（分 {len(batches)} 批，每批 {batch_size}）...")
    print(f"   模式: {'真实提交' if real_submit else '模拟提交'}")

    for i, batch in enumerate(batches, 1):
        size_mb = len(json.dumps(batch, ensure_ascii=False)) / 1024 / 1024
        print(f"\n  第 {i}/{len(batches)} 批 ({len(batch)} 条, {size_mb:.1f}MB)")

        result = submit_batch(batch)

        if result["success"]:
            codes = result.get("taskCodes", [])
            all_codes.extend(codes)
            print(f"    ✅ 成功! 获得 {len(codes)} 个 taskCode")
        else:
            print(f"    ❌ 失败: {result['error']}")
            failed_items.append({"batch": i, "error": result["error"]})

    return {
        "total": total,
        "submitted": len(all_codes),
        "failed": len(failed_items),
        "task_codes": all_codes,
        "failed_items": failed_items
    }


def detect_project_type(project_dir):
    """检测项目类型"""
    metadata_path = project_dir / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path, encoding="utf-8") as f:
            metadata = json.load(f)
        project_type = metadata.get("project_type", "drama")
        if project_type == "product_video":
            return "product"
        if project_type == "mv":
            return "mv"
    # 检查目录结构
    if (project_dir / "videos").exists():
        return "product"
    return "dm"


def submit_product_video_tasks(project_dir, real_submit=False):
    """产品视频串行提交：VIDEO01 → VIDEO02 → VIDEO03"""
    tasks_file = project_dir / "seedance_project_tasks.json"

    with open(tasks_file, encoding="utf-8") as f:
        data = json.load(f)

    tasks = data.get("tasks", [])
    if not tasks:
        print("⚠️ 没有任务")
        return None

    all_codes = []
    failed_items = []
    video_task_map = {}  # taskCode -> video_id

    # 按依赖顺序提交
    print(f"\n📤 产品视频串行提交（确保视频一致性）...")

    for i, task in enumerate(tasks):
        task["realSubmit"] = real_submit

        # 展开 referenceFiles
        expanded_files, _ = expand_reference_files(
            task.get("referenceFiles", []),
            project_dir
        )
        task["referenceFiles"] = expanded_files

        # 更新 videoReferences（如果前序视频已完成）
        video_refs = task.get("videoReferences", [])
        if video_refs:
            for vr in video_refs:
                prev_video_id = vr.get("videoId", "")
                # 查找前序视频的 taskCode
                for vid, tc in video_task_map.items():
                    if prev_video_id in vid:
                        vr["taskCode"] = tc
                        # 从已完成任务获取视频URL
                        status, video_url = wait_for_task_complete(tc)
                        if video_url:
                            vr["fileUrl"] = video_url

        print(f"\n  提交 {task.get('video_id', f'视频{i+1}')}...")
        print(f"    引用视频: {[vr.get('videoId') for vr in video_refs]}")

        result = submit_batch([task])

        if result["success"]:
            codes = result.get("taskCodes", [])
            task_code = codes[0] if codes else None
            if task_code:
                all_codes.append(task_code)
                video_id = task.get("video_id", f"VIDEO{i+1}")
                video_task_map[video_id] = task_code
                print(f"    ✅ {task_code}")
        else:
            print(f"    ❌ {result['error']}")
            failed_items.append({"task": task.get("video_id"), "error": result["error"]})

    return {
        "total": len(tasks),
        "submitted": len(all_codes),
        "failed": len(failed_items),
        "task_codes": all_codes,
        "failed_items": failed_items,
        "video_task_map": video_task_map
    }


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python seedance_submit.py <项目目录>")
        print("  python seedance_submit.py <项目目录> --real")
        print("  python seedance_submit.py <项目目录> --batch 10")
        print("  python seedance_submit.py <项目目录> --wait")
        sys.exit(1)

    project_path = sys.argv[1]
    project_dir = Path(project_path).resolve()

    if not project_dir.exists():
        print(f"错误: 目录不存在: {project_dir}")
        sys.exit(1)

    # 解析参数
    real_submit = "--real" in sys.argv
    wait_complete = "--wait" in sys.argv
    batch_size = DEFAULT_BATCH_SIZE

    if "--batch" in sys.argv:
        idx = sys.argv.index("--batch")
        if idx + 1 < len(sys.argv):
            try:
                batch_size = int(sys.argv[idx + 1])
            except ValueError:
                pass

    # 检测项目类型
    project_type = detect_project_type(project_dir)

    # 加载 metadata
    metadata_path = project_dir / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path, encoding="utf-8") as f:
            metadata = json.load(f)
    else:
        metadata = {}

    project_id = metadata.get("project_id", project_dir.name.split("_")[0])
    project_name = metadata.get("project_name", project_dir.name)

    print(f"🎬 Seedance 任务提交")
    print(f"📁 项目: {project_name} ({project_id})")
    print(f"📂 目录: {project_dir}")
    print(f"📹 类型: {'产品视频' if project_type == 'product' else '短剧' if project_type == 'dm' else 'MV'}")

    # 产品视频使用串行提交
    if project_type == "product":
        result = submit_product_video_tasks(project_dir, real_submit)
    else:
        result = submit_tasks(project_dir, real_submit, batch_size, None)

    if result is None:
        print("\n❌ 提交失败或无任务")
        sys.exit(1)

    # 如果需要等待完成
    if wait_complete and result.get("task_codes"):
        print("\n⏳ 等待所有任务完成...")
        video_map = fetch_completed_videos(result["task_codes"])
        result["completed_videos"] = video_map

    # 生成报告
    report = {
        "project_id": project_id,
        "project_name": project_name,
        "project_type": project_type,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "api_base": API_BASE,
        "total_tasks": result["total"],
        "submitted_tasks": result["submitted"],
        "failed_tasks": result["failed"],
        "real_submit": real_submit,
        "task_codes": result["task_codes"],
        "failed_items": result["failed_items"]
    }

    if "video_task_map" in result:
        report["video_task_map"] = result["video_task_map"]

    if "completed_videos" in result:
        report["completed_videos"] = result["completed_videos"]

    report_path = project_dir / "submission_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"✅ 提交完成!")
    print(f"   总任务: {result['total']}")
    print(f"   成功: {result['submitted']}")
    print(f"   失败: {result['failed']}")
    print(f"\n📋 报告: {report_path}")

    if result["task_codes"]:
        print(f"\n📝 Task Codes (前5个):")
        for code in result["task_codes"][:5]:
            print(f"   {code}")
        if len(result["task_codes"]) > 5:
            print(f"   ... 共 {len(result['task_codes'])} 个")


if __name__ == "__main__":
    main()
