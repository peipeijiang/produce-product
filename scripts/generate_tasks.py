#!/usr/bin/env python3
"""
智能生成产品功能展示视频任务（面向后期可剪辑素材）

根据产品图片与分析报告，自动生成多版本 15s 竖屏任务。
- 不使用 Hook-Body-CTA
- 不要配音，不要字幕
- 可包含类似 PPT 的英文文字说明（overlay text）
- keyframes: 功能与场景参考
- raw: 材质与质感参考

使用方法：
    python3 scripts/generate_tasks.py /path/to/project [num_versions]
"""
import json
import os
import sys
import re
from collections import defaultdict


def collect_image_files(directory):
    """收集目录中的图片文件名（仅文件，不含子目录）"""
    image_files = []
    if not os.path.exists(directory):
        return image_files

    for file_name in os.listdir(directory):
        full_path = os.path.join(directory, file_name)
        if not os.path.isfile(full_path):
            continue
        if file_name.lower().endswith((".jpg", ".jpeg", ".png")):
            image_files.append(file_name)

    return image_files


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
        "scenes": [],
        "product_images": [],
        "raw_images": []
    }

    if not os.path.exists(zai_report):
        return result

    with open(zai_report) as f:
        content = f.read()

    for raw_line in content.split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        if "产品名称" in line and ":" in line:
            result["product_name"] = line.split(":")[-1].strip()
        if "产品类型" in line and ":" in line:
            result["product_type"] = line.split(":")[-1].strip()

        # 尽量从报告里抽取功能和场景关键词
        if any(k in line for k in ["核心功能", "功能", "卖点", "特性", "亮点"]):
            result["features"].extend(extract_keywords(line))
        if any(k in line for k in ["场景", "使用场景", "适用场景"]):
            result["scenes"].extend(extract_keywords(line))

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

    # 如果报告信息不足，则从图片文件名补充关键词
    if not result["features"] and not result["scenes"]:
        keyframes_dir = os.path.join(project_dir, "keyframes")
        for file_name in collect_image_files(keyframes_dir):
            tokens = tokenize_text(file_name)
            result["features"].extend(tokens)

    result["features"] = unique_preserve(result["features"])
    result["scenes"] = unique_preserve(result["scenes"])

    # 获取产品图片（keyframes）
    keyframes_dir = os.path.join(project_dir, "keyframes")
    result["product_images"] = collect_image_files(keyframes_dir)

    # 获取 raw 质感参考图（可选）
    raw_dir = os.path.join(project_dir, "raw")
    result["raw_images"] = collect_image_files(raw_dir)

    return result


def tokenize_text(text):
    tokens = re.findall(r"[a-zA-Z0-9\u4e00-\u9fff]+", text.lower())
    return [t for t in tokens if len(t) >= 2]


def extract_keywords(line):
    cleaned = re.sub(r"^[\-\*\d\.\s]+", "", line)
    parts = re.split(r"[，,;；、:：|/]", cleaned)
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        # 长片段再拆词，短片段直接留原词
        if len(p) > 12:
            out.extend(tokenize_text(p))
        else:
            out.append(p)
    return out


def sanitize_keywords(items):
    banned = {
        "核心功能", "功能", "卖点", "特性", "亮点",
        "场景", "使用场景", "适用场景", "产品名称", "产品类型"
    }
    output = []
    for i in items:
        text = re.sub(r"[\s_\-]+", " ", i).strip()
        if not text:
            continue
        if text in banned:
            continue
        output.append(text)
    return unique_preserve(output)


def unique_preserve(items):
    seen = set()
    output = []
    for i in items:
        key = i.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(i)
    return output


def guess_product_family(product_name_en, product_type, features):
    text = f"{product_name_en} {product_type} {' '.join(features)}".lower()
    if any(k in text for k in ["ring", "watch", "band", "wear", "health", "fitness"]):
        return "wearable"
    if any(k in text for k in ["pet", "cat", "dog"]):
        return "pet"
    if any(k in text for k in ["speaker", "audio", "earbud", "headphone"]):
        return "audio"
    return "generic"


def build_scene_bank(product_name_en, family, features, scenes):
    feature_text = ", ".join(features[:4]) if features else "core product benefits"
    custom_scene = scenes[0] if scenes else "Everyday use"

    if family == "wearable":
        return [
            ("Morning Routine", "quick setup and glanceable metrics", "Fast setup, clear status"),
            ("Workout Tracking", "active movement and live feedback", "Track movement in real time"),
            ("Desk Focus", "distraction-free passive monitoring", "Stay focused, stay informed"),
            ("Night Recovery", "sleep and recovery insights", "Recover better overnight"),
            ("Close-up Materials", "premium finish and tactile details", "Premium materials, refined finish"),
        ]
    if family == "pet":
        return [
            ("Living Room Comfort", "pet relaxing naturally at home", "Comfort for everyday rest"),
            ("Nap Time Detail", "supportive shape and soft contact points", "Supportive and soft"),
            ("Owner Interaction", "human-pet interaction in normal routine", "Fits real home routines"),
            ("Material Close-up", "surface texture and stitching details", "Quality you can see"),
            ("Multi-angle Utility", "different placement and use moments", "Practical in every corner"),
        ]
    if family == "audio":
        return [
            ("Commute Scene", "portable daily audio usage", "Ready for daily commute"),
            ("Work Session", "focus audio in desk scenario", "Focused sound, clean setup"),
            ("Workout Scene", "stable fit during movement", "Stable fit in motion"),
            ("Call Scenario", "clear communication moment", "Clear calls, less noise"),
            ("Material Close-up", "driver housing and finishing details", "Precision build quality"),
        ]

    return [
        ("Hero Overview", f"{feature_text}", "Core value at a glance"),
        ("Scene 1", f"{custom_scene}", "Designed for real-world use"),
        ("Scene 2", "functional interaction with the product", "Function shown in context"),
        ("Detail Macro", "material and structure close-up", "Details define quality"),
        ("Lifestyle Wrap", "integration into daily routine", "Fits into everyday life"),
    ]


def build_focus_pool(features, scenes):
    feature_pool = sanitize_keywords(features) or ["core function"]
    scene_pool = sanitize_keywords(scenes) or ["everyday use"]
    return feature_pool, scene_pool


def choose_focus(feature_pool, scene_pool, feature_usage, scene_usage, version_num):
    feature_sorted = sorted(feature_pool, key=lambda x: (feature_usage[x.lower()], x.lower()))
    scene_sorted = sorted(scene_pool, key=lambda x: (scene_usage[x.lower()], x.lower()))

    # 固定选择“当前使用最少”的项，先覆盖完整维度，再进入重复
    feature = feature_sorted[0]
    scene = scene_sorted[0]
    feature_usage[feature.lower()] += 1
    scene_usage[scene.lower()] += 1
    return feature, scene


def select_keyframes_for_scene(images, scene_name, scene_focus, features, version_num, image_usage):
    if not images:
        return []

    scored = []
    scene_tokens = tokenize_text(scene_name) + tokenize_text(scene_focus)
    feature_tokens = []
    for f in features[:6]:
        feature_tokens.extend(tokenize_text(f))
    tokens = set(scene_tokens + feature_tokens)

    for img in images:
        name_tokens = set(tokenize_text(img))
        score = 0
        for t in tokens:
            if t in name_tokens:
                score += 2
            elif t in img.lower():
                score += 1
        # 使用次数越少越优先，推动版本间多样性
        score += max(0, 5 - image_usage[img])
        scored.append((score, img))

    # 高分优先；分数相同按文件名排序，保证可复现
    scored.sort(key=lambda x: (-x[0], x[1]))
    high_ranked = [name for score, name in scored if score > 0]
    fallback = [name for _, name in scored]
    if high_ranked:
        ranked = high_ranked + [name for name in fallback if name not in high_ranked]
    else:
        ranked = fallback

    pick_count = min(4, max(3, len(images) // 2))

    # 通过版本号偏移，保证多版本选图有差异
    offset = (version_num - 1) % len(ranked)
    rotated = ranked[offset:] + ranked[:offset]
    selected = rotated[:pick_count]
    for img in selected:
        image_usage[img] += 1
    return selected


def select_raw_images(raw_images, version_num):
    if not raw_images:
        return []
    if len(raw_images) <= 3:
        return list(raw_images)
    start = (version_num - 1) % len(raw_images)
    rotated = raw_images[start:] + raw_images[:start]
    return rotated[:3]


def build_shot_style(version_num):
    styles = [
        {
            "name": "Narrative Flow",
            "plan": [
                "0-3s: Establish scene context and product entry.",
                "3-8s: Demonstrate a key interaction with medium and close shots.",
                "8-12s: Capture macro details and tactile realism.",
                "12-15s: End with stable product-environment lockup."
            ],
        },
        {
            "name": "Comparison Flow",
            "plan": [
                "0-3s: Show baseline lifestyle context.",
                "3-8s: Highlight product-enabled improvement in same context.",
                "8-12s: Focus on design/structure that enables the function.",
                "12-15s: Present clean hero composition for editing handoff."
            ],
        },
        {
            "name": "Detail-first Flow",
            "plan": [
                "0-3s: Start with close-up material/detail hook.",
                "3-8s: Pull out to full scene usage.",
                "8-12s: Alternate detail and interaction inserts for cut points.",
                "12-15s: End with a minimal, static confirmation shot."
            ],
        },
    ]
    return styles[(version_num - 1) % len(styles)]


def generate_editable_scene_prompt(
    product_name_en,
    scene_name,
    scene_focus,
    scene_text,
    primary_feature,
    secondary_feature,
    selected_images,
    selected_raw_images,
    version_num
):
    keyframe_refs = " ".join([f"(@{img})" for img in selected_images])
    raw_refs = " ".join([f"(@{img})" for img in selected_raw_images]) if selected_raw_images else "N/A"
    all_refs = " ".join([f"(@{img})" for img in selected_images + selected_raw_images])
    feature_line = f"{primary_feature}; {secondary_feature}"
    style = build_shot_style(version_num)

    return f"""{all_refs}
KEYFRAME REFERENCES (function and scenario priority): {keyframe_refs}
RAW TEXTURE REFERENCES (material realism priority): {raw_refs}

Create a 15-second vertical (9:16) product footage sequence for {product_name_en}.
Goal: provide highly editable clips for post-production. No voiceover. No subtitles.
Allow concise PPT-style on-screen text overlays only.

Scene theme: {scene_name}
Scene focus: {scene_focus}
Feature context: {feature_line}
Version style: {style["name"]}

Shot plan:
{style["plan"][0]} Overlay text: "{scene_text}".
{style["plan"][1]} Overlay text: "{primary_feature}".
{style["plan"][2]} Overlay text: "{secondary_feature}".
{style["plan"][3]} Overlay text: "{product_name_en}".

Editing requirements:
- Keep each shot modular and easy to cut.
- Use clean transitions and stable motion, avoid complex effects.
- Prioritize realism from RAW references and usage cues from KEYFRAME references.
- Ensure this version is visually distinct from other versions in scene setting and function emphasis.
- No narration, no subtitles, no spoken text."""


def analyze_versions(info, num_versions=5):
    """
    根据图片特点自动生成多个版本

    如果没有具体场景指示，自动选择不同的营销角度
    """
    versions = []
    product_name_en = info["product_name_en"]
    images = info["product_images"]
    raw_images = info.get("raw_images", [])

    if not images:
        return versions

    features = info.get("features", [])
    scenes = info.get("scenes", [])
    family = guess_product_family(product_name_en, info.get("product_type", ""), features)
    scene_bank = build_scene_bank(product_name_en, family, features, scenes)

    # 多样性跟踪：尽量均匀覆盖功能/场景/图片
    feature_pool, scene_pool = build_focus_pool(features, scenes)
    feature_usage = defaultdict(int)
    scene_usage = defaultdict(int)
    image_usage = defaultdict(int)

    # 按用户要求数量生成，可循环场景库并在选图上做偏移增强差异
    for i in range(num_versions):
        version_num = i + 1
        scene = scene_bank[i % len(scene_bank)]
        scene_name, scene_focus_seed, scene_text = scene
        primary_feature, dynamic_scene_focus = choose_focus(
            feature_pool, scene_pool, feature_usage, scene_usage, version_num
        )
        # 次要功能用于增加版本差异
        secondary_candidates = [f for f in feature_pool if f.lower() != primary_feature.lower()]
        if secondary_candidates:
            secondary_candidates = sorted(
                secondary_candidates,
                key=lambda x: (feature_usage[x.lower()], x.lower())
            )
            secondary_feature = secondary_candidates[0]
            feature_usage[secondary_feature.lower()] += 1
        else:
            secondary_feature = primary_feature

        scene_focus = f"{scene_focus_seed}; scenario: {dynamic_scene_focus}; feature: {primary_feature}"

        selected_images = select_keyframes_for_scene(
            images,
            scene_name,
            scene_focus,
            [primary_feature, secondary_feature] + features,
            version_num,
            image_usage
        )
        selected_raw_images = select_raw_images(raw_images, version_num)
        prompt = generate_editable_scene_prompt(
            product_name_en,
            scene_name,
            scene_focus,
            scene_text,
            primary_feature,
            secondary_feature,
            selected_images,
            selected_raw_images,
            version_num
        )

        versions.append({
            "name": f"{scene_name} - {primary_feature} Editable 15s",
            "direction": f"V{i+1}_{scene_name.replace(' ', '_')}",
            "ref_files": (
                [f"keyframes/{img}" for img in selected_images] +
                [f"raw/{img}" for img in selected_raw_images]
            ),
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
                "duration": "15s"
            },
            "referenceFiles": ref_files,
            "videoReferences": [],
            "realSubmit": True,
            "priority": 1,
            "tags": [
                "PRODUCT",
                product_name_en.replace(" ", "_"),
                version_info['name'].replace(" ", "_"),
                "EDITABLE_FOOTAGE",
                "NO_VOICEOVER",
                "NO_SUBTITLE",
                "PPT_TEXT_OVERLAY"
            ],
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
    print(f"🧱 RAW 质感参考图: {len(info['raw_images'])} 张")

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
    print("   1. python3 scripts/convert_to_base64_fixed.py /path/to/project  # 转换为 base64 格式")
    print("   2. python3 scripts/submit_tasks.py /path/to/project              # 提交任务")


if __name__ == "__main__":
    main()
