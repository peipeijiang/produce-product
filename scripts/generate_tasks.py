#!/usr/bin/env python3
"""
智能生成产品营销视频任务

根据 ZAI 识别报告和图片特点，自动决定生成几个版本、什么风格

注意：此脚本只生成 JSON 任务文件，不自动提交。
如需提交，请使用 seedance_submit.py 或手动提交。
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


def analyze_versions(info, num_versions=5):
    """根据图片特点分析版本 - 英文 prompt"""
    versions = []
    product_name = info["product_name"]
    images = info["product_images"]

    if not images:
        return versions

    # V1: Luxury Display
    if num_versions >= 1:
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

Elegant unboxing video of {product_name}. A premium box opens to reveal the sleek product. Close-up shots of premium finish. The product sparkles. Hand shows the product. Add text overlays: {product_name}, Premium Design. Cinematic 9:16, 15 seconds."""

        versions.append({"name": "Luxury", "direction": "V1_Luxury", "ref_files": ref_files, "prompt": prompt})

    # V2: Features
    if num_versions >= 2 and len(images) >= 2:
        ref_files2 = [f"keyframes/{images[0]}"]
        if len(images) > 1:
            ref_files2.append(f"keyframes/{images[1]}")

        prompt2 = f"""(@{images[0]}) is {product_name} showing product features. """
        if len(images) > 1:
            prompt2 += f"(@{images[1]}) demonstrates the feature. "

        prompt2 += f"""

Dynamic feature showcase of {product_name}. Person interacts with the product. The feature displays. Person smiles. Cut to different scenarios. Add text overlays: Smart Features, {product_name}. Cinematic 9:16, 15 seconds."""

        versions.append({"name": "Features", "direction": "V2_Features", "ref_files": ref_files2, "prompt": prompt2})

    # V3: Lifestyle
    if num_versions >= 3 and len(images) >= 2:
        ref_files3 = [f"keyframes/{images[0]}"]
        if len(images) > 1:
            ref_files3.append(f"keyframes/{images[1]}")

        prompt3 = f"""(@{images[0]}) is {product_name} in everyday life. (@{images[1]}) shows person using the product daily.

Lifestyle showcase of {product_name}. Person goes through their day with the product. Morning to evening. The product fits seamlessly. Add text overlays: Your Daily Companion, {product_name}. Cinematic 9:16, 15 seconds."""

        versions.append({"name": "Lifestyle", "direction": "V3_Lifestyle", "ref_files": ref_files3, "prompt": prompt3})

    # V4: Cozy Scene (for pet products)
    if num_versions >= 4 and len(images) >= 2:
        ref_files4 = [f"keyframes/{images[0]}"]
        if len(images) > 1:
            ref_files4.append(f"keyframes/{images[1]}")

        prompt4 = f"""(@{images[0]}) shows {product_name} with soft texture. (@{images[1]}) displays comfortable usage.

Cozy showcase of {product_name}. Close-up of soft fabric surface. Gentle touch to show softness. Warm and peaceful atmosphere. Slow motion scenes. Add text overlays: Super Soft, Cloud Comfort, Sweet Dreams. Cinematic 9:16, 15 seconds."""

        versions.append({"name": "Cozy", "direction": "V4_Cozy", "ref_files": ref_files4, "prompt": prompt4})

    # V5: Quality Assurance
    if num_versions >= 5 and len(images) >= 2:
        ref_files5 = [f"keyframes/{images[0]}"]
        if len(images) > 1:
            ref_files5.append(f"keyframes/{images[1]}")

        prompt5 = f"""(@{images[0]}) is {product_name} showing premium quality. (@{images[1]}) demonstrates material excellence.

Quality assurance showcase of {product_name}. Display certification badges. Show premium materials. Durability demonstration. Customer satisfaction. Add text overlays: Premium Quality, Certified, Quality Guaranteed. Cinematic 9:16, 15 seconds."""

        versions.append({"name": "Quality", "direction": "V5_Quality", "ref_files": ref_files5, "prompt": prompt5})

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
    # 解析参数
    num_versions = 5  # 默认生成 5 个版本
    project_dir = None

    for arg in sys.argv[1:]:
        if arg.isdigit():
            num_versions = int(arg)
        elif not arg.startswith("-"):
            project_dir = arg

    if not project_dir:
        print("用法: python3 generate_tasks.py /path/to/project [num_versions]")
        print("       python3 generate_tasks.py /path/to/project 3  # 生成 3 个版本")
        sys.exit(1)

    print(f"📁 项目: {project_dir}")
    print(f"📊 生成版本数: {num_versions}")

    info = parse_zai_report(project_dir)
    print(f"📦 产品: {info['product_name']}")

    versions = analyze_versions(info, num_versions)

    for v in versions:
        task = generate_task(v, info['product_name'], project_dir)
        filename = f"seedance_tasks_{v['direction']}.json"
        with open(os.path.join(project_dir, filename), "w", encoding="utf-8") as f:
            json.dump(task, f, indent=2, ensure_ascii=False)
        print(f"✅ {filename}")

    print(f"\n完成! 生成了 {len(versions)} 个版本")
    print("\n⚠️ 注意：JSON 文件仅供预览，如需提交请使用 seedance_submit.py")
    print("   或手动提交（确保 prompt 无中文，referenceFiles 为 base64 格式）")


if __name__ == "__main__":
    main()
