#!/usr/bin/env python3
"""
智能生成产品营销视频任务

根据用户指示或产品图片，自动生成营销视频任务。
如果没有具体场景指示，将自动按照 Hook-Body-CTA 结构生成 15s 英文口播带字幕的视频。

使用方法：
    python3 scripts/generate_tasks.py /path/to/project [num_versions]
"""
import json
import os
import sys
import random


def parse_zai_report(project_dir):
    """解析 ZAI 报告"""
    products_dir = os.path.join(project_dir, "products")
    zai_report = os.path.join(products_dir, "ZAI_full_analysis_report.md")

    result = {
        "product_name": "Product",
        "product_name_en": "Product",
        "product_type": "Product",
        "colors": [],
        "features": [],
        "product_images": []
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

    # 简单的产品名翻译
    cn_to_en = {
        "智能戒指": "Smart Ring",
        "智能手环": "Smart Band",
        "智能手表": "Smart Watch",
        "智能耳机": "Smart Earbuds",
        "宠物床": "Pet Bed",
        "智能音箱": "Smart Speaker"
    }

    product_name = result["product_name"]
    result["product_name_en"] = cn_to_en.get(product_name, product_name)

    # 获取产品图片
    keyframes_dir = os.path.join(project_dir, "keyframes")
    if os.path.exists(keyframes_dir):
        for f in os.listdir(keyframes_dir):
            if f.endswith((".jpg", ".png", ".jpeg")):
                result["product_images"].append(f)

    return result


def generate_hook_body_cta_prompt(product_name, product_name_en, feature, images, version_num):
    """
    生成 Hook-Body-CTA 结构的 15s Prompt

    结构：
    - Hook (0-3s): 吸引注意力
    - Body (3-12s): 展示功能和优势
    - CTA (12-15s): 行动号召
    """

    # 随机选择 3-5 张图片
    selected_images = random.sample(images, min(len(images), random.randint(3, 5)))

    # 构建 prompt
    image_refs = " ".join([f"(@{img})" for img in selected_images])

    prompt = f"""{image_refs}

HOOK-Body-CTA structured marketing video for {product_name_en}.

HOOK [0-3s]: Eye-catching opening. Product revealed dramatically. Text overlay: "Upgrade Your Life Today". Dynamic camera movement. Product sparkles. ({product_name_en}) takes center stage.

BODY [3-12s]: Feature showcase: {feature}. Person using product in real-life scenario. Multiple angles showing design excellence. Smooth transitions between scenes. Text overlays appear dynamically: "Premium Quality", "Smart Design", "Daily Essential". Close-up shots highlight details. Product demonstrates its value through action.

CTA [12-15s]: Strong call to action. Final dramatic shot of {product_name_en}. Text overlay: "Shop Now - Limited Time Offer". Urgent feeling. Product name displayed prominently. Link to purchase. Bold, confident ending.

CRITICAL: Include professional English voiceover throughout: "Ready to upgrade your daily routine? This is {product_name_en}. Experience premium quality and smart design that fits perfectly into your life. Don't wait, transform your experience today. Shop now limited time offer." Include matching English subtitles. Cinematic style 9:16 15 seconds."""

    return prompt, selected_images


def analyze_versions(info, num_versions=5):
    """
    根据图片特点自动生成多个版本

    如果没有具体场景指示，自动选择不同的营销角度
    """
    versions = []
    product_name = info["product_name"]
    product_name_en = info["product_name_en"]
    images = info["product_images"]

    if not images:
        return versions

    # 不同的营销角度
    marketing_angles = [
        {
            "name": "Premium_Luxury",
            "feature": "premium craftsmanship and elegant design",
            "description": "Premium Luxury 15s"
        },
        {
            "name": "Smart_Features",
            "feature": "innovative smart features",
            "description": "Smart Features 15s"
        },
        {
            "name": "Lifestyle_Daily",
            "feature": "seamless daily integration",
            "description": "Lifestyle Daily 15s"
        },
        {
            "name": "Performance_Quality",
            "feature": "exceptional performance and reliability",
            "description": "Performance Quality 15s"
        },
        {
            "name": "Best_Value",
            "feature": "unbeatable value and benefits",
            "description": "Best Value 15s"
        }
    ]

    # 根据版本数生成
    for i in range(min(num_versions, len(marketing_angles))):
        angle = marketing_angles[i]
        prompt, selected_images = generate_hook_body_cta_prompt(
            product_name, product_name_en,
            angle["feature"], images, i + 1
        )

        versions.append({
            "name": angle["description"],
            "direction": f"V{i+1}_{angle['name']}",
            "ref_files": [f"keyframes/{img}" for img in selected_images],
            "prompt": prompt
        })

    return versions


def generate_task(version_info, product_name_en, project_dir):
    """生成单个版本 JSON"""
    ref_files = version_info["ref_files"]

    task_data = {
        "project_id": f"PRODUCT-{version_info['direction']}",
        "project_name": f"{product_name_en} - {version_info['name']}",
        "project_type": "product",
        "video_structure": "single",
        "total_tasks": 1,
        "realSubmit": True,
        "tasks": [{
            "video_id": f"PRODUCT-{version_info['direction']}",
            "segment_index": 0,
            "prompt": version_info["prompt"],
            "description": version_info["name"],
            "modelConfig": {
                "model": "Seedance 2.0 Fast",
                "referenceMode": "全能参考",
                "aspectRatio": "9:16",
                "duration": 15
            },
            "referenceFiles": ref_files,
            "videoReferences": [],
            "realSubmit": True,
            "priority": 1,
            "tags": ["PRODUCT", product_name_en.replace(" ", "_"), version_info['name'].replace(" ", "_"), "VOICEOVER", "SUBTITLE"],
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
    print(f"📦 产品: {info['product_name']} ({info['product_name_en']})")
    print(f"📸 可用图片: {len(info['product_images'])} 张")

    if not info['product_images']:
        print("❌ 错误: 没有找到产品图片")
        print("   请确保项目目录下有 keyframes/ 文件夹，且包含图片")
        sys.exit(1)

    versions = analyze_versions(info, num_versions)

    if not versions:
        print("❌ 错误: 无法生成版本")
        sys.exit(1)

    for v in versions:
        task = generate_task(v, info['product_name_en'], project_dir)
        filename = f"seedance_tasks_{v['direction']}.json"
        with open(os.path.join(project_dir, filename), "w", encoding="utf-8") as f:
            json.dump(task, f, indent=2, ensure_ascii=False)
        print(f"✅ {filename} - {v['name']}")

    print(f"\n✅ 完成! 生成了 {len(versions)} 个版本")
    print(f"📁 位置: {project_dir}")
    print("\n下一步:")
    print("   1. python3 convert_to_base64_fixed.py  # 转换为 base64 格式")
    print("   2. python3 submit_tasks.py              # 提交任务")


if __name__ == "__main__":
    main()
