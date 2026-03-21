#!/usr/bin/env python3
"""
智能生成产品功能展示视频任务（面向后期可剪辑素材）

根据产品图片与分析报告，自动生成多版本 15s 竖屏任务。
- 不使用 Hook-Body-CTA
- 不要配音，不要字幕
- 禁止任何画面文字（no overlay text / no subtitles）
- keyframes: 仅提供功能和场景 idea
- raw: 视觉质感与材质还原主参考

使用方法：
    python3 scripts/generate_tasks.py /path/to/project [num_versions]
"""
import json
import os
import sys
import re
import subprocess
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
        "raw_images": [],
        "image_notes": {}
    }

    if not os.path.exists(zai_report):
        return result

    with open(zai_report) as f:
        content = f.read()

    current_section = ""
    for raw_line in content.split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("### "):
            current_section = line
            continue

        if "产品名称" in line and ":" in line:
            name_raw = line.split(":")[-1].strip()
            result["product_name"] = name_raw
            # 优先提取括号中的英文名：智能戒指 (Smart Ring)
            en_match = re.search(r"\(([^)]+)\)", name_raw)
            if en_match and not contains_chinese(en_match.group(1)):
                result["product_name_en"] = en_match.group(1).strip()
        if "产品类型" in line and ":" in line:
            result["product_type"] = line.split(":")[-1].strip()

        if line.startswith("|") and (".jpg" in line or ".png" in line or ".jpeg" in line):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 3:
                file_name = cells[0]
                note = " ".join(cells[1:])
                if file_name.lower().endswith((".jpg", ".jpeg", ".png")):
                    normalized_terms = " ".join(to_english_terms([current_section, note]))
                    result["image_notes"][file_name] = f"{current_section} {note} {normalized_terms}".strip()

        # 仅用于功能/场景抽取时过滤噪声行（文件表格、图片名行等）
        if is_report_noise_line(line):
            continue

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
    if result["product_name_en"] == "Product":
        result["product_name_en"] = cn_to_en.get(product_name, product_name)
    result["product_name_en"] = force_english_text(result["product_name_en"], "Product")

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
        if is_noise_keyword(text):
            continue
        output.append(text)
    return unique_preserve(output)


def contains_chinese(text):
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def force_english_text(text, fallback):
    text = (text or "").strip()
    if not text:
        return fallback
    if not contains_chinese(text):
        return text
    # 移除中文，仅保留英文/数字与常见符号
    cleaned = re.sub(r"[\u4e00-\u9fff]", "", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -_:;,.")
    return cleaned if cleaned else fallback


def to_english_terms(items):
    """
    提取英文信号词（仅作为 idea 输入）。
    对常见中文产品/场景线索做轻量映射，避免识别报告里的关键信息被丢掉。
    """
    out = []
    phrase_map = [
        ("sleep tracking", ["睡眠", "夜间", "卧室"]),
        ("activity tracking", ["运动", "健身", "训练"]),
        ("heart rate monitoring", ["心率"]),
        ("blood oxygen", ["血氧"]),
        ("women's health", ["女性健康"]),
        ("office work", ["办公", "会议", "桌面", "工位"]),
        ("commute", ["通勤", "出行", "开车", "车门"]),
        ("home relax", ["居家", "放松", "沙发", "冥想"]),
        ("swim tracking", ["游泳"]),
        ("waterproof use", ["防水", "水下"]),
        ("product appearance", ["外观展示", "产品展示"]),
        ("spec overview", ["参数说明"]),
    ]
    for raw in items:
        token = (raw or "").strip()
        if not token:
            continue
        if is_noise_keyword(token):
            continue
        if contains_chinese(token):
            for english, keywords in phrase_map:
                if any(keyword in token for keyword in keywords):
                    out.append(english)
            continue
        token = re.sub(r"[^a-zA-Z0-9\s\-]", " ", token)
        token = re.sub(r"\s+", " ", token).strip().lower()
        if len(token) < 3:
            continue
        out.append(token)
    return unique_preserve(out)


def is_noise_keyword(text):
    t = (text or "").strip().lower()
    if not t:
        return True
    if re.fullmatch(r"\d+", t):
        return True
    if t in {"jpg", "jpeg", "png", "part"}:
        return True
    if re.fullmatch(r"\d+\.\d+", t):
        return True
    if ".jpg" in t or ".jpeg" in t or ".png" in t:
        return True
    if t.startswith("feature angle") or t.startswith("scene angle"):
        return True
    if t in {"file", "name", "content", "type", "url", "http", "https"}:
        return True
    if re.fullmatch(r"[a-z]{1,2}\d+", t):
        return True
    if re.fullmatch(r"[a-z]+\d+[a-z0-9]*", t):
        return True
    if re.fullmatch(r"[a-z]{1,3}", t) and len(t) <= 2:
        return True
    # 文件名碎片类 token
    if re.search(r"\bpart\b", t) and re.search(r"\d+", t):
        return True
    return False


def is_report_noise_line(line):
    l = line.strip().lower()
    if not l:
        return True
    # markdown 表格与分隔行
    if "|" in l:
        return True
    if set(l) <= {"-", ":", " "}:
        return True
    # 图片文件行或资源链接行
    if ".jpg" in l or ".jpeg" in l or ".png" in l:
        return True
    if l.startswith("http://") or l.startswith("https://"):
        return True
    return False


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
    custom_scene = scenes[0] if scenes else "Daily use"

    # 所有版本统一为生活化 TikTok 带货主播日常使用展示风格
    if family == "wearable":
        return [
            ("Livestream Desk", "host demonstrates core function at desk in one continuous take", "Desk setup"),
            ("Mirror Try-on", "host shows wearing comfort and close interaction near mirror", "Mirror corner"),
            ("Kitchen Counter", "host explains practical daily usage with hands-on gestures", "Kitchen counter"),
            ("Sofa Handheld", "host presents natural handheld usage while sitting on sofa", "Living room sofa"),
            ("Window Light Detail", "host demonstrates material and interaction under natural window light", "Window daylight"),
        ]
    if family == "pet":
        return [
            ("Morning Pet Routine", "creator films feeding and chill moments at home", "Real home pet life"),
            ("Living Room Chill", "casual couch and floor moments with the pet", "Daily comfort moments"),
            ("Balcony Sunlight", "natural light and relaxed interaction", "Natural daylight use"),
            ("Quick Clean-up", "creator tidies and resets product area", "Practical daily maintenance"),
            ("Night Pet Calm", "quiet bedtime pet routine and settling down", "Calm night routine"),
        ]
    if family == "audio":
        return [
            ("Morning Commute POV", "creator records subway and walking audio moments", "Daily commute vibe"),
            ("Study Desk Session", "creator does focused work and task switching", "Focus block session"),
            ("Gym Movement Clip", "creator shows fit stability while moving", "Move freely all day"),
            ("Street Call Moment", "creator takes real-life phone calls outdoors", "Clear call moments"),
            ("Evening Unwind", "creator relaxes with music at home", "Evening chill routine"),
        ]

    return [
        ("Morning Routine", "creator starts daily tasks and uses product naturally", "Daily creator routine"),
        ("Errands & Commute", "creator moves through normal city moments", "Real on-the-go usage"),
        ("Desk & Messages", "creator alternates between work and social check-ins", "Work-life flow"),
        ("Home Reset", f"{custom_scene}", "Practical at-home usage"),
        ("Night Wrap-up", "creator ends the day with low-key usage moments", "Nightly lifestyle scene"),
    ]


def infer_scene_id(scene_text):
    text = (scene_text or "").lower()
    mapping = [
        ("sleep", ["sleep", "night", "bed", "bedroom"]),
        ("office", ["office", "desk", "meeting", "work", "workflow"]),
        ("workout", ["workout", "gym", "fitness", "exercise", "training", "sport"]),
        ("waterproof", ["swim", "water", "pool", "waterproof"]),
        ("commute", ["commute", "car", "drive", "door", "travel", "outdoor"]),
        ("relax", ["meditation", "relax", "sofa", "home", "window", "living room"]),
    ]
    for scene_id, keywords in mapping:
        if any(keyword in text for keyword in keywords):
            return scene_id
    return "daily"


def build_scene_package_templates(family):
    if family == "wearable":
        return {
            "sleep": {
                "scene_name": "Bedroom Night Routine",
                "scene_text": "soft bedroom or bedside setting",
                "focus_seed": "host stays in a bedroom night routine and demonstrates comfortable all-night wear",
                "show_plan": "start with a close hand reveal, show the ring being worn before rest, then hold one steady bedside interaction that suggests sleep or recovery tracking",
                "token_hints": ["sleep", "night", "bedroom", "bedside", "rest", "recovery"],
            },
            "office": {
                "scene_name": "Desk Work Routine",
                "scene_text": "clean desk, meeting table, or laptop workspace",
                "focus_seed": "host demonstrates the ring during a focused work session with natural hand movement around laptop, notebook, or coffee",
                "show_plan": "open on the hand wearing the ring at the desk, keep one main angle while the host types, gestures, or checks a small moment on the ring, then finish with a natural close detail in the same setup",
                "token_hints": ["desk", "office", "meeting", "laptop", "workspace", "typing"],
            },
            "workout": {
                "scene_name": "Gym Routine",
                "scene_text": "gym corner or home workout area",
                "focus_seed": "host shows the ring through a light workout or stretch routine in one continuous scene",
                "show_plan": "begin with the ring on hand before movement, then keep the same workout corner while the host does a short practical motion sequence that makes activity tracking feel real",
                "token_hints": ["gym", "fitness", "workout", "training", "movement", "activity"],
            },
            "waterproof": {
                "scene_name": "Poolside Waterproof Routine",
                "scene_text": "poolside, sink edge, or water-related setup",
                "focus_seed": "host demonstrates the ring in a realistic water-related setting to support durability or swim-use cues",
                "show_plan": "show the ring in hand first, then keep one continuous scene while the host moves through a simple water interaction without changing location, emphasizing confidence and practicality",
                "token_hints": ["swim", "water", "pool", "waterproof", "splash", "durability"],
            },
            "commute": {
                "scene_name": "Out-The-Door Routine",
                "scene_text": "entryway, bag table, doorway, or car-side setup",
                "focus_seed": "host presents the ring as part of a quick leaving-home or commuting routine",
                "show_plan": "start with the hand putting on or already wearing the ring, keep the same doorway or car-side environment, and show one believable daily action like grabbing keys, opening a door, or settling into the seat",
                "token_hints": ["commute", "door", "car", "keys", "entryway", "outdoor"],
            },
            "relax": {
                "scene_name": "Sofa Relax Routine",
                "scene_text": "sofa corner, window seat, or calm living-room setup",
                "focus_seed": "host demonstrates the ring in a calm home setting with slow, natural gestures",
                "show_plan": "open with a detail of the ring catching light, then remain in the same sofa or window setup while the host relaxes, gestures naturally, and lets the product feel premium and easy to wear",
                "token_hints": ["sofa", "window", "relax", "meditation", "living room", "home"],
            },
            "daily": {
                "scene_name": "Single-Scene Daily Routine",
                "scene_text": "clean everyday home setting",
                "focus_seed": "host shows one practical daily-use moment in a simple lifestyle setup",
                "show_plan": "keep one stable scene and let the host explain through action, alternating between ring close details and natural hand use in the same place",
                "token_hints": ["daily", "home", "routine", "practical"],
            },
        }

    return {
        "daily": {
            "scene_name": "Single-Scene Daily Routine",
            "scene_text": "clean everyday lifestyle setting",
            "focus_seed": "host demonstrates practical use in one continuous lifestyle scene",
            "show_plan": "keep the full presentation in one place and reveal value through natural hands-on use instead of fast cuts",
            "token_hints": ["daily", "lifestyle", "routine"],
        }
    }


def build_default_focus_pool(family):
    if family == "wearable":
        return (
            ["health monitoring", "sleep insights", "activity tracking", "gesture control", "battery life"],
            ["morning routine", "commute", "desk workflow", "workout session", "night routine"]
        )
    if family == "pet":
        return (
            ["daily comfort", "easy clean-up", "pet relaxation", "home-friendly design", "material durability"],
            ["morning feeding", "living room chill", "balcony sunlight", "afternoon nap", "night calm"]
        )
    if family == "audio":
        return (
            ["stable fit", "clear calls", "focus listening", "portable use", "battery endurance"],
            ["commute", "desk session", "workout", "street call", "evening unwind"]
        )
    return (
        ["daily utility", "comfort use", "practical function", "durable design", "easy routine fit"],
        ["morning routine", "on-the-go use", "desk workflow", "home reset", "night wrap-up"]
    )


def build_focus_pool(features, scenes, family):
    feature_pool = sanitize_keywords(features)
    scene_pool = sanitize_keywords(scenes)
    feature_pool = to_english_terms(feature_pool)
    scene_pool = to_english_terms(scene_pool)
    default_features, default_scenes = build_default_focus_pool(family)
    if not feature_pool:
        feature_pool = default_features
    if not scene_pool:
        scene_pool = default_scenes
    return feature_pool, scene_pool


def choose_scene_packages(scene_pool, family, num_versions):
    templates = build_scene_package_templates(family)
    chosen_ids = []
    for raw_scene in scene_pool:
        scene_id = infer_scene_id(raw_scene)
        if scene_id not in templates:
            scene_id = "daily"
        if scene_id not in chosen_ids:
            chosen_ids.append(scene_id)

    if not chosen_ids:
        chosen_ids = ["daily"]

    preferred_order = ["office", "relax", "commute", "workout", "sleep", "waterproof", "daily"]
    for scene_id in preferred_order:
        if len(chosen_ids) >= num_versions:
            break
        if scene_id in templates and scene_id not in chosen_ids:
            chosen_ids.append(scene_id)

    while len(chosen_ids) < num_versions:
        chosen_ids.append("daily")

    packages = []
    for idx, scene_id in enumerate(chosen_ids[:num_versions], start=1):
        package = dict(templates[scene_id])
        package["scene_id"] = scene_id
        package["version_num"] = idx
        packages.append(package)
    return packages


def choose_features_for_scene(feature_pool, scene_package, feature_usage):
    scene_id = scene_package["scene_id"]
    scene_like_terms = {
        "commute", "office work", "home relax", "product appearance", "spec overview"
    }
    candidate_features = [f for f in feature_pool if f.lower() not in scene_like_terms]
    if not candidate_features:
        candidate_features = list(feature_pool)
    priorities = {
        "sleep": ["sleep", "recovery", "comfort", "health"],
        "office": ["heart", "oxygen", "health", "tracking", "smart"],
        "workout": ["activity", "fitness", "sport", "tracking", "heart"],
        "waterproof": ["swim", "water", "durable", "activity"],
        "commute": ["comfort", "daily", "activity", "health"],
        "relax": ["sleep", "health", "comfort", "heart"],
        "daily": ["health", "activity", "sleep", "comfort"],
    }
    keywords = priorities.get(scene_id, priorities["daily"])

    ranked = []
    for feature in candidate_features:
        score = 0
        lower = feature.lower()
        for idx, keyword in enumerate(keywords):
            if keyword in lower:
                score += 10 - idx
        ranked.append((score, feature_usage[lower], lower, feature))
    ranked.sort(key=lambda item: (-item[0], item[1], item[2]))

    primary = ranked[0][3] if ranked else "daily use"
    feature_usage[primary.lower()] += 1

    secondary = primary
    for _, _, _, candidate in ranked[1:]:
        if candidate.lower() != primary.lower():
            secondary = candidate
            feature_usage[secondary.lower()] += 1
            break

    return primary, secondary


def choose_focus(feature_pool, scene_pool, feature_usage, scene_usage, version_num):
    feature_sorted = sorted(feature_pool, key=lambda x: (feature_usage[x.lower()], x.lower()))
    scene_sorted = sorted(scene_pool, key=lambda x: (scene_usage[x.lower()], x.lower()))

    # 固定选择“当前使用最少”的项，先覆盖完整维度，再进入重复
    feature = feature_sorted[0]
    scene = scene_sorted[0]
    feature_usage[feature.lower()] += 1
    scene_usage[scene.lower()] += 1
    return feature, scene


def select_keyframes_for_scene(images, image_notes, scene_name, scene_focus, features, version_num, image_usage):
    if not images:
        return []

    scored = []
    scene_tokens = tokenize_text(scene_name) + tokenize_text(scene_focus)
    feature_tokens = []
    for f in features[:6]:
        feature_tokens.extend(tokenize_text(f))
    tokens = set(scene_tokens + feature_tokens)

    for img in images:
        note_text = image_notes.get(img, "")
        name_tokens = set(tokenize_text(f"{img} {note_text}"))
        score = 0
        for t in tokens:
            if t in name_tokens:
                score += 2
            elif t in img.lower() or t in note_text.lower():
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
    selected = ranked[:pick_count]
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
            "name": "Single-Scene Livestream",
            "plan": "Keep the full 15s inside the same location, but allow 2 to 4 natural camera angles such as a medium host shot, a hand close-up, and a product detail shot.",
            "detail_insert": "Cuts are allowed only within the same physical setup and must feel like natural coverage, not a scene change."
        },
        {
            "name": "Single-Scene Host Walkthrough",
            "plan": "Keep one host-led scene as if in a live selling stream, and cover it with a few complementary angles in the same space from start to finish.",
            "detail_insert": "Angle changes may include hand details, over-shoulder views, or tighter product framing, but the environment must stay the same."
        },
        {
            "name": "Single-Scene Real Routine",
            "plan": "Sustain one real-life daily-use moment in one setting for the full piece, using a small set of realistic coverage shots to make the edit usable.",
            "detail_insert": "Allow close, medium, and detail shots as long as they clearly belong to the same setup and timeline."
        },
    ]
    return styles[(version_num - 1) % len(styles)]


def to_overlay_phrase(feature_text, family, slot):
    text = (feature_text or "").lower()
    if "sleep" in text:
        return "Sleep insights every night"
    if "heart" in text or "oxygen" in text:
        return "Health stats at a glance"
    if "activity" in text or "sport" in text or "workout" in text:
        return "Track every move"
    if "gesture" in text or "control" in text or "remote" in text:
        return "Hands-free control"
    if "battery" in text or "endurance" in text:
        return "Power that lasts"
    if "water" in text or "durable" in text:
        return "Ready for daily conditions"
    if "comfort" in text:
        return "Comfort for all-day use"
    if "call" in text:
        return "Clear calls in real life"

    # 无明确特征时的通用自主文案
    generic = {
        "wearable": ["Smart habits, made simple", "Designed for daily rhythm"],
        "pet": ["Fits naturally into home life", "Comfort your pet can feel"],
        "audio": ["Sound that fits your routine", "Built for everyday listening"],
        "generic": ["Built for real daily moments", "Simple value in daily life"],
    }
    pool = generic.get(family, generic["generic"])
    return pool[slot % len(pool)]


def generate_editable_scene_prompt(
    product_name_en,
    family,
    scene_name,
    scene_focus,
    scene_text,
    show_plan,
    primary_feature,
    secondary_feature,
    selected_images,
    selected_raw_images,
    version_num
):
    keyframe_refs = " ".join([f"(@{img})" for img in selected_images])
    feature_line = f"{primary_feature}; {secondary_feature}"
    style = build_shot_style(version_num)
    segments = [
        keyframe_refs,
        f"Create a 15s vertical 9:16 editable product video for {product_name_en} in TikTok live-selling host style.",
        f"Scene: {scene_name}. Setting: {scene_text}. Focus: {scene_focus}. Features: {feature_line}. Style: {style['name']}.",
        "No story arc and no plot progression; direct demonstration only.",
        "Keep the whole video in one consistent scene and one physical setting, but allow several natural shot changes within that same scene for editing flexibility.",
        f"Presentation flow: {show_plan}.",
        f"{style['plan']} {style['detail_insert']}",
        "No on-screen text of any kind: no overlay text, no subtitles, no labels, no UI text, no sticker text.",
        "No voiceover and no spoken text.",
        (
            "Use keyframes only for function and scene idea. "
            + (
                "Prioritize RAW references for material realism."
                if selected_raw_images
                else "Keep material rendering realistic and consistent with the product photos."
            )
        ),
        "Keep this version visually distinct from other versions by scene setup and function emphasis."
    ]
    if selected_raw_images:
        segments.insert(1, " ".join([f"(@{img})" for img in selected_raw_images]))
    return " ".join(s.strip() for s in segments if s and s.strip())


def analyze_versions(info, num_versions=5):
    """
    根据图片特点自动生成多个版本

    如果没有具体场景指示，自动选择不同的营销角度
    """
    versions = []
    product_name_en = info["product_name_en"]
    images = info["product_images"]
    raw_images = info.get("raw_images", [])
    image_notes = info.get("image_notes", {})

    if not images:
        return versions

    features = info.get("features", [])
    scenes = info.get("scenes", [])
    family = guess_product_family(product_name_en, info.get("product_type", ""), features)
    feature_pool, scene_pool = build_focus_pool(features, scenes, family)
    feature_usage = defaultdict(int)
    image_usage = defaultdict(int)
    scene_packages = choose_scene_packages(scene_pool, family, num_versions)

    for i, scene_package in enumerate(scene_packages):
        version_num = i + 1
        scene_name = scene_package["scene_name"]
        scene_text = scene_package["scene_text"]
        primary_feature, secondary_feature = choose_features_for_scene(
            feature_pool, scene_package, feature_usage
        )
        scene_focus = f"{scene_package['focus_seed']}; emphasize {primary_feature} in this exact setting"

        selected_images = select_keyframes_for_scene(
            images,
            image_notes,
            scene_name,
            f"{scene_text} {scene_focus} {' '.join(scene_package['token_hints'])}",
            [primary_feature, secondary_feature] + scene_package["token_hints"] + features,
            version_num,
            image_usage
        )
        selected_raw_images = select_raw_images(raw_images, version_num)
        prompt = generate_editable_scene_prompt(
            product_name_en,
            family,
            scene_name,
            scene_focus,
            scene_text,
            scene_package["show_plan"],
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
                "TIKTOK_LIFESTYLE",
                "NO_VOICEOVER",
                "NO_SUBTITLE",
                "NO_ONSCREEN_TEXT"
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

    report_path = os.path.join(project_dir, "products", "ZAI_full_analysis_report.md")
    analysis_script = os.path.join(os.path.dirname(__file__), "analyze_products_glm.py")
    if not os.path.exists(report_path) and os.environ.get("ZHIPU_API_KEY") and os.path.exists(analysis_script):
        print("🔎 未检测到分析报告，先调用 GLM-4.6V-FlashX 识别产品图片...")
        try:
            subprocess.run(
                [sys.executable, analysis_script, project_dir],
                check=True,
            )
        except subprocess.CalledProcessError:
            print("⚠️ 图片识别失败，将继续使用默认信息生成任务")

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

    for file_name in os.listdir(project_dir):
        if file_name.startswith("seedance_tasks_V") and file_name.endswith(".json"):
            os.remove(os.path.join(project_dir, file_name))

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
