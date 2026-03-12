#!/usr/bin/env python3
"""
智能生成产品营销视频任务

根据用户指示或产品图片，自动生成营销视频任务。
如果没有具体场景指示，将自动按照 Hook-Body-CTA 结构生成 15s 英文口播带字幕的视频。

图片目录说明：
- keyframes/: 参考图片（产品设计图、渲染图等）
- raw/: 实拍图片（真实产品的质感照片，用于要求 AI 还原质感）

如果 raw/ 文件夹存在且包含图片，生成的任务会：
1. 从 raw/ 随机选择 3 张（或少于 3 张则全部）作为实拍参考
2. 复制并重命名为英文文件名（避免 prompt 出现中文）
3. 在 prompt 中明确要求还原实拍产品的质感
4. 所有产品画面必须忠实还原实拍图片的材质、光线和表面质感

参考模式：
- seedance_reference_mode.md: 包含 Seedance 2.0 参考模式的使用说明
- 支持"参考图像"、"参考视频"、"视频编辑"等模式
- 在 generate_tasks.py 中通过参数启用

使用方法：
    python3 scripts/generate_tasks.py /path/to/project [num_versions]

示例：
    python3 scripts/generate_tasks.py /path/to/project        # 生成 5 个版本
    python3 scripts/generate_tasks.py /path/to/project 3      # 生成 3 个版本
    python3 scripts/generate_tasks.py /path/to/project 5 --reference-mode    # 启用参考模式
"""
import json
import os
import sys
import random
import shutil
import re


def copy_and_rename_raw_images(raw_dir, project_dir):
    """
    复制 raw 文件夹中的图片并重命名为英文，避免 prompt 中出现中文

    返回：(重命名后的英文文件名列表, 临时文件夹路径)
    """
    renamed_files = []
    temp_raw_dir = os.path.join(project_dir, "temp_raw")

    # 创建临时文件夹
    if not os.path.exists(temp_raw_dir):
        os.makedirs(temp_raw_dir)

    # 复制并重命名所有 raw 图片
    for i, filename in enumerate(sorted(os.listdir(raw_dir)), 1):
        if not filename.lower().endswith((".jpg", ".png", ".jpeg")):
            continue

        src = os.path.join(raw_dir, filename)
        new_filename = f"raw_photo_{i:03d}.jpg"
        dst = os.path.join(temp_raw_dir, new_filename)

        # 复制文件
        shutil.copy2(src, dst)
        renamed_files.append(new_filename)

    return renamed_files, temp_raw_dir


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
        "product_images": [],
        "raw_images": []  # 新增：raw 文件夹中的实拍图片
    }

    if not os.path.exists(zai_report):
        return result

    with open(zai_report) as f:
        content = f.read()

    for line in content.split("\n"):
        if "产品名称" in line and ":" in line:
            # 提取纯中文名（去掉英文括号）
            match = re.search(r'^(.*?)\s*\(', line.split(":")[-1])
            if match:
                result["product_name"] = match.group(1).strip()
            else:
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

    # 获取 keyframes 图片（参考图）
    keyframes_dir = os.path.join(project_dir, "keyframes")
    if os.path.exists(keyframes_dir):
        for f in os.listdir(keyframes_dir):
            if f.endswith((".jpg", ".png", ".jpeg")):
                result["product_images"].append(f)

    # 获取 raw 文件夹中的实拍图片（使用原始文件名，后续会重命名）
    raw_dir = os.path.join(project_dir, "raw")
    if os.path.exists(raw_dir):
        for f in os.listdir(raw_dir):
            if f.endswith((".jpg", ".png", ".jpeg")):
                result["raw_images"].append(f)

    return result


def generate_hook_body_cta_prompt(product_name_en, feature, images, raw_images, version_num, temp_raw_dir, use_reference_mode=False):
    """
    生成 Hook-Body-CTA 结构的 15s Prompt（纯英文）

    结构：
    - Hook (0-3s): 吸引注意力
    - Body (3-12s): 展示功能和优势
    - CTA (12-15s): 行动号召

    参数：
        product_name_en: 英文产品名（Prompt 中必须使用英文）
        raw_images: raw 文件夹中的实拍图片列表（英文文件名）
        images: keyframes 文件夹中的参考图片列表
        temp_raw_dir: 临时 raw 文件夹路径（用于引用）
        use_reference_mode: 是否使用参考模式（包含参考视频、镜头语言等）
    """
    # 从 raw 文件夹中选择图片（如果有）
    if raw_images:
        # 选择 3 张，如果少于 3 张则全部使用
        selected_raw_images = random.sample(raw_images, min(len(raw_images), 3))
        print(f"   📸 Using {len(selected_raw_images)} real photos (from raw/)")
    else:
        selected_raw_images = []
        print(f"   ⚠️  No raw images, using keyframes only")

    # 随机选择 3-5 张 keyframes 图片作为参考
    if images:
        selected_keyframes = random.sample(images, min(len(images), random.randint(3, 5)))
    else:
        selected_keyframes = []

    # 构建图片引用（所有引用的图片，包括实拍图和参考图）
    all_ref_images = selected_raw_images + selected_keyframes
    image_refs = " ".join([f"(@{img})" for img in all_ref_images])

    # 如果有实拍图片，添加质感还原要求
    quality_instruction = ""
    if selected_raw_images:
        quality_instruction = """

CRITICAL QUALITY REQUIREMENT: All product shots must faithfully recreate texture, material quality, and lighting from raw product images. Pay special attention to:
- Surface texture (matte, glossy, metallic, fabric grain, etc.)
- Material quality and craftsmanship
- Lighting and reflections that match real product appearance
- Color accuracy and depth
- Any product-specific material characteristics (wood grain, metal finish, fabric softness, etc.)
The final product render should look indistinguishable from actual physical product's material quality."""

    # 如果使用参考模式，尝试读取参考模式文件
    if use_reference_mode:
        import os
        ref_mode_file = os.path.join(os.path.dirname(__file__), "seedance_reference_mode.md")
        reference_mode_instruction = ""
        if os.path.exists(ref_mode_file):
            with open(ref_mode_file, "r", encoding="utf-8") as f:
                ref_mode_content = f.read()
            # 提取参考模式的要点
            if "【参考图像】" in ref_mode_content:
                reference_mode_instruction = "\n\n【参考图像】参考图像可精准还原画面构图、角色细节。\n"
            if "【参考视频】" in ref_mode_content:
                reference_mode_instruction += "【参考视频】参考视频支持镜头语言、复杂的动作节奏、创意特效的复刻。\n"
            if "【视频编辑】" in ref_mode_content:
                reference_mode_instruction += "【视频编辑】视频支持平滑延长与衔接，可按用户提示生成连续镜头，不止生成，还能\"接着拍\"。\n"
            if "【编辑能力】" in ref_mode_content:
                reference_mode_instruction += "【编辑能力】编辑能力同步增强，支持对已有视频进行角色更替、删减、增加。\n"
            if reference_mode_instruction:
                quality_instruction += "\n\n" + reference_mode_instruction

    prompt = f"""{image_refs}

HOOK-Body-CTA structured marketing video for {product_name_en}.{quality_instruction}

HOOK [0-3s]: Eye-catching opening. Product revealed dramatically. Text overlay: "Upgrade Your Life Today". Dynamic camera movement. Product sparkles. ({product_name_en}) takes center stage.

BODY [3-12s]: Feature showcase: {feature}. Person using product in real-life scenario. Multiple angles showing design excellence. Smooth transitions between scenes. Text overlays appear dynamically: "Premium Quality", "Smart Design", "Daily Essential". Close-up shots highlight details. Product demonstrates its value through action.

CTA [12-15s]: Strong call to action. Final dramatic shot of {product_name_en}. Text overlay: "Shop Now - Limited Time Offer". Urgent feeling. Product name displayed prominently. Link to purchase. Bold, confident ending.

CRITICAL: Include professional English voiceover throughout: "Ready to upgrade your daily routine? This is {product_name_en}. Experience premium quality and smart design that fits perfectly into your life. Don't wait, transform your experience today. Shop now limited time offer." Include matching English subtitles. Cinematic style 9:16 15s duration."""

    return prompt, all_ref_images


def analyze_versions(info, num_versions=5, temp_raw_dir=None, use_reference_mode=False):
    """
    根据图片特点自动生成多个版本

    如果没有具体场景指示，自动选择不同的营销角度

    参数：
        info: 包含 product_images（keyframes）和 raw_images（实拍图）
        temp_raw_dir: 临时 raw 文件夹路径（英文文件名）
        use_reference_mode: 是否使用 Seedance 参考模式
    """
    versions = []
    product_name = info["product_name"]
    product_name_en = info["product_name_en"]
    images = info["product_images"]
    raw_images = info["raw_images"]

    if not images and not raw_images:
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

    # 更新 raw_images 为重命名后的英文文件名
    if temp_raw_dir and os.path.exists(temp_raw_dir):
        renamed_files = os.listdir(temp_raw_dir)
        raw_images = [f for f in renamed_files if f.endswith((".jpg", ".png", ".jpeg"))]
        print(f"📸 Updated raw_images with {len(raw_images)} English filenames")

    # 根据版本数生成
    for i in range(min(num_versions, len(marketing_angles))):
        angle = marketing_angles[i]
        prompt, selected_images = generate_hook_body_cta_prompt(
            product_name_en, angle["feature"], images, raw_images, i + 1, temp_raw_dir, use_reference_mode
        )

        # 构建引用文件列表（temp_raw/ 和 keyframes/）
        ref_files = []
        for img in selected_images:
            # 如果图片以 raw_photo_ 开头，使用 temp_raw/ 路径
            if img.startswith("raw_photo_"):
                ref_files.append(f"temp_raw/{img}")
            # 否则使用 keyframes/ 路径
            else:
                ref_files.append(f"keyframes/{img}")

        versions.append({
            "name": angle["description"],
            "direction": f"V{i+1}_{angle['name']}",
            "ref_files": ref_files,
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
                "referenceMode": "全能参考",  # 英文：全能参考
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
    use_reference_mode = False  # 是否使用参考模式

    for arg in sys.argv[1:]:
        if arg.isdigit():
            num_versions = int(arg)
        elif arg == "--reference-mode":
            use_reference_mode = True
        elif not arg.startswith("-"):
            project_dir = arg

    if not project_dir:
        print("Usage: python3 generate_tasks.py /path/to/project [num_versions] [--reference-mode]")
        print("       python3 generate_tasks.py /path/to/project 3        # Generate 3 versions")
        print("       python3 generate_tasks.py /path/to/project 5 --reference-mode    # Enable reference mode")
        sys.exit(1)

    print(f"📁 Project: {project_dir}")
    print(f"📊 Versions to generate: {num_versions}")
    print(f"🔄 Reference mode: {'Enabled' if use_reference_mode else 'Disabled'}")

    # 处理 raw 文件夹（复制并重命名为英文文件名）
    raw_dir = os.path.join(project_dir, "raw")
    temp_raw_dir = None
    if os.path.exists(raw_dir):
        print(f"\n📸 Processing raw images...")
        renamed_raw_images, temp_raw_dir = copy_and_rename_raw_images(raw_dir, project_dir)
        print(f"✅ Created temp_raw/ with {len(renamed_raw_images)} English filenames")
    else:
        print("\n⚠️  No raw folder found, using keyframes only")
        renamed_raw_images = []

    info = parse_zai_report(project_dir)
    print(f"\n📦 Product: {info['product_name']} ({info['product_name_en']})")
    print(f"📸 keyframes images: {len(info['product_images'])} files")
    print(f"📸 raw images: {len(info['raw_images'])} files (before rename)")

    # 更新 raw_images 为重命名后的英文文件名
    info["raw_images"] = renamed_raw_images

    if not info['product_images'] and not info['raw_images']:
        print("❌ Error: No product images found")
        print("   Please ensure project directory has keyframes/ or raw/ folder with images")
        sys.exit(1)

    versions = analyze_versions(info, num_versions, temp_raw_dir, use_reference_mode)

    if not versions:
        print("❌ Error: Unable to generate versions")
        sys.exit(1)

    for v in versions:
        task = generate_task(v, info['product_name_en'], project_dir)
        filename = f"seedance_tasks_{v['direction']}.json"
        with open(os.path.join(project_dir, filename), "w", encoding="utf-8") as f:
            json.dump(task, f, indent=2, ensure_ascii=False)
        print(f"✅ {filename} - {v['name']}")

    print(f"\n✅ Complete! Generated {len(versions)} versions")
    print(f"📁 Location: {project_dir}")
    print("\nNext steps:")
    print("   1. python3 convert_to_base64_fixed.py /path/to/project  # Convert to base64 format")
    print("   2. python3 submit_tasks.py /path/to/project              # Submit tasks")


if __name__ == "__main__":
    main()
