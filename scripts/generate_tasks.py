#!/usr/bin/env python3
"""
智能生成产品营销视频任务

根据 ZAI 识别报告和图片特点，自动决定生成几个版本、什么风格
"""
import json
import os
import sys
from pathlib import Path


def parse_zai_report(project_dir):
    """解析 ZAI 报告"""
    products_dir = os.path.join(project_dir, "products")
    zai_report = os.path.join(products_dir, "ZAI_full_analysis_report.md")

    result = {
        "product_name": "Product",
        "product_type": "Product",
        "colors": [],
        "features": [],
        "product_images": [],
        "feature_images": []
    }

    if not os.path.exists(zai_report):
        return result

    with open(zai_report) as f:
        content = f.read()

    for line in content.split("\n"):
        if "产品名称" in line and ":" in line:
            result["product_name"] = line.split(":")[-1].strip()
        if "产品类型" in line and ":" in line:
            result["product_type"] = line.split(":")[-1].strip()

    keyframes_dir = os.path.join(project_dir, "keyframes")
    if os.path.exists(keyframes_dir):
        for f in os.listdir(keyframes_dir):
            if f.endswith((".jpg", ".png", ".jpeg")):
                result["product_images"].append(f)

    return result


def analyze_versions(info):
    """根据图片特点分析版本"""
    versions = []
    product_name = info["product_name"]
    images = info["product_images"]

    if not images:
        return versions

    # V1: 奢华展示
    ref_files = [f"keyframes/{images[0]}"]
    if len(images) > 1:
        ref_files.append(f"keyframes/{images[1]}")
    if len(images) > 2:
        ref_files.append(f"keyframes/{images[2]}")

    prompt = f"""(@{images[0]}) is {product_name} product photo showing elegant design. """
    if len(images) > 1:
        prompt += f"(@{images[1]}) shows model wearing the product. "
    if len(images) > 2:
        prompt += f"(@{images[2]}) is pure product shot. "

    prompt += f"""

Elegant unboxing video of {product_name}. A premium box opens to reveal the sleek product. Close-up shots of premium finish. The product sparkles. Hand shows the product. Add English text overlays: '{product_name}', 'Premium Design'. CRITICAL: WRIST IS BARE if wearable. Cinematic 9:16, 15 seconds."""

    versions.append({"name": "奢华展示", "direction": "Luxury", "ref_files": ref_files, "prompt": prompt})

    # V2: 功能展示
    if len(images) >= 2:
        ref_files2 = [f"keyframes/{images[0]}"]
        if len(images) > 1:
            ref_files2.append(f"keyframes/{images[1]}")

        prompt2 = f"""(@{images[0]}) is {product_name} showing product features. """
        if len(images) > 1:
            prompt2 += f"(@{images[1]}) demonstrates the feature. "

        prompt2 += f"""

Dynamic feature showcase of {product_name}. Person interacts with the product. The feature displays. Person smiles. Cut to different scenarios. Add English text overlays: 'Smart Features', '{product_name}'. CRITICAL: WRIST IS BARE if wearable. Cinematic 9:16, 15 seconds."""

        versions.append({"name": "功能展示", "direction": "Features", "ref_files": ref_files2, "prompt": prompt2})

    # V3: 生活方式
    if len(images) >= 2:
        ref_files3 = [f"keyframes/{images[0]}"]
        if len(images) > 1:
            ref_files3.append(f"keyframes/{images[1]}")

        prompt3 = f"""(@{images[0]}) is {product_name} in everyday life场景. (@{images[1]}) shows person using the product daily.

Lifestyle showcase of {product_name}. Person goes through their day with the product. Morning to evening. The product fits seamlessly. Add English text overlays: 'Your Daily Companion', '{product_name}'. CRITICAL: WRIST IS BARE if wearable. Cinematic 9:16, 15 seconds."""

        versions.append({"name": "生活方式", "direction": "Lifestyle", "ref_files": ref_files3, "prompt": prompt3})

    return versions


def generate_task(version_info, product_name, project_dir):
    """生成单个版本 JSON"""
    ref_files = version_info["ref_files"]

    task_data = {
        "project_id": f"PRODUCT-{version_info['direction']}",
        "project_name": f"{product_name} - {version_info['name']}",
        "project_type": "product",
        "video_structure": "single",
        "total_tasks": 1,
        "realSubmit": True,
        "tasks": [{
            "video_id": f"PRODUCT-{version_info['direction']}",
            "segment_index": 0,
            "prompt": version_info["prompt"],
            "description": f"{product_name} {version_info['name']} 15s",
            "modelConfig": {
                "model": "Seedance 2.0 Fast",
                "referenceMode": "全能参考",
                "aspectRatio": "9:16",
                "duration": "15s"
            },
            "referenceFiles": ref_files,
            "videoReferences": [],
            "realSubmit": True,
            "priority": 1,
            "tags": [product_name, version_info["name"], "Product"],
            "dependsOn": []
        }]
    }
    return task_data


def main():
    if len(sys.argv) < 2:
        print("用法: python3 generate_tasks.py /path/to/project")
        sys.exit(1)

    project_dir = sys.argv[1]
    print(f"📁 项目: {project_dir}")

    info = parse_zai_report(project_dir)
    print(f"📦 产品: {product_name}")

    versions = analyze_versions(info)

    for v in versions:
        task = generate_task(v, info['product_name'], project_dir)
        filename = f"seedance_tasks_{v['direction']}.json"
        with open(os.path.join(project_dir, filename), "w") as f:
            json.dump(task, f, indent=2)
        print(f"✅ {filename}")

    print("完成!")


if __name__ == "__main__":
    main()
