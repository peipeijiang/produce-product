#!/usr/bin/env python3
"""
Use GLM-4.6V-FlashX to analyze product images and write a structured
products/ZAI_full_analysis_report.md report for downstream task generation.

Usage:
    ZHIPU_API_KEY=... python3 scripts/analyze_products_glm.py /path/to/project
"""
import base64
import json
import os
import re
import sys
import time
from datetime import date
from pathlib import Path

import requests


API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
MODEL_NAME = "glm-4.6v-flashx"
SUMMARY_IMAGE_LIMIT = 10
CACHE_FILE_NAME = ".glm_image_analysis_cache.json"


def collect_images(directory: Path):
    if not directory.exists():
        return []
    return sorted(
        p for p in directory.iterdir()
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )


def encode_image(image_path: Path):
    mime = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
    payload = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{payload}"


def extract_json(text):
    text = text.strip()
    fence_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
    if fence_match:
        return json.loads(fence_match.group(1))
    brace_match = re.search(r"(\{.*\})", text, re.S)
    if brace_match:
        return json.loads(brace_match.group(1))
    return json.loads(text)


def request_glm(api_key, content, temperature=0.1):
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": content}],
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_error = None
    for attempt in range(8):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=180)
            if response.status_code == 200:
                body = response.json()
                return body["choices"][0]["message"]["content"]
            last_error = f"HTTP {response.status_code}: {response.text[:800]}"
        except Exception as exc:  # pragma: no cover
            last_error = str(exc)
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(last_error or "unknown GLM request failure")


def load_cache(cache_path: Path):
    if not cache_path.exists():
        return {}
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_cache(cache_path: Path, cache_data):
    cache_path.write_text(json.dumps(cache_data, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_list(value):
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        items = re.split(r"[,\n;/|]+", value)
    else:
        items = []
    cleaned = []
    seen = set()
    for item in items:
        text = re.sub(r"\s+", " ", str(item).strip())
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(text)
    return cleaned


def safe_text(value, fallback=""):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text or fallback


def fallback_summary_text(field_name):
    fallbacks = {
        "product_name_cn": "图片中未明确标出品牌名，按视觉特征推断为该品类产品",
        "product_name_en": "Product inferred from image content",
        "product_type_cn": "图片显示为消费品/实体商品，具体子类按画面特征归纳",
        "product_type_en": "Consumer product inferred from image content",
        "optional_colors_cn": "图片中可见配色有限，建议以画面出现的主色为准",
        "optional_sizes_cn": "图片中未直接展示完整尺寸信息",
        "battery_life_cn": "图片中未直接展示续航信息",
        "purchase_link": "图片中未出现明确购买链接",
        "usage_overview": "图片主要用于展示产品外观、核心卖点、使用场景和转化信息。",
    }
    return fallbacks.get(field_name, "图片中未直接展示")


def normalize_summary_value(value, fallback):
    if isinstance(value, list):
        items = normalize_list(value)
        return ", ".join(items) if items else fallback
    text = safe_text(value, "")
    if not text:
        return fallback
    if text in {"待识别", "未识别", "unknown", "n/a", "[]"}:
        return fallback
    return text


def summarize_color_tags(image_rows):
    color_text = " ".join(
        safe_text(row.get("color"))
        for row in image_rows
        if safe_text(row.get("color")) and safe_text(row.get("color")) != "-"
    ).lower()
    mappings = [
        ("黑色", ["黑色", "black"]),
        ("银色", ["银色", "银灰", "silver"]),
        ("金色", ["金色", "gold"]),
        ("蓝色发光元素", ["蓝色", "led", "blue"]),
    ]
    tags = [label for label, terms in mappings if any(term in color_text for term in terms)]
    if not tags:
        return "当前图片中可确认的颜色信息有限，以实拍主色和局部细节为准"
    return "、".join(tags)


def summarize_scene_tags(image_rows):
    scene_text = " ".join(
        safe_text(row.get("scene_or_purpose"))
        for row in image_rows
        if safe_text(row.get("scene_or_purpose")) and safe_text(row.get("scene_or_purpose")) != "-"
    ).lower()
    mappings = [
        ("产品外观展示", ["外观", "产品展示", "静物", "展示智能戒指", "智能穿戴设备展示"]),
        ("睡眠场景", ["睡眠", "卧室", "夜间"]),
        ("办公会议场景", ["办公", "会议"]),
        ("运动健身场景", ["健身", "运动"]),
        ("防水/游泳场景", ["游泳", "水下", "防水"]),
        ("居家放松场景", ["居家", "冥想"]),
        ("日常通勤/出行场景", ["车门", "出行"]),
        ("功能参数说明", ["数字信息", "时间显示", "充电", "健康监测"]),
    ]
    tags = [label for label, terms in mappings if any(term in scene_text for term in terms)]
    if not tags:
        return "当前图片主要覆盖外观展示、功能说明和生活方式场景"
    return "、".join(tags)


def normalize_image_row(row):
    normalized = dict(row or {})
    image_type = safe_text(normalized.get("image_type"))
    scene = safe_text(normalized.get("scene_or_purpose"))
    notes = safe_text(normalized.get("notes"))
    copy_points = " ".join(normalize_list(normalized.get("extracted_copy_points"))).lower()
    merged_text = " ".join([image_type, scene, notes, copy_points]).lower()

    if normalized.get("is_product_related") is False:
        normalized["category"] = "不相关图片"
        return normalized

    strong_function_signals = [
        "功能", "演示", "监测", "睡眠", "心率", "血氧", "防水", "游泳", "健身",
        "冥想", "办公", "会议", "车门", "充电", "app", "界面", "时间显示", "数字信息",
        "认证标志", "rohs", "ce", "fcc", "规格", "参数", "使用状态",
    ]
    appearance_signals = [
        "外观", "佩戴效果", "模特佩戴", "静物", "产品展示", "多色展示", "外观展示",
        "产品照片", "戒指外观", "智能穿戴设备展示",
    ]
    lifestyle_scene_signals = [
        "卧室", "睡眠场景", "水下", "游泳场景", "商务办公", "会议", "冥想场景",
        "健身房", "车门把手", "居家场景", "使用场景",
    ]

    function_score = sum(1 for signal in strong_function_signals if signal.lower() in merged_text)
    appearance_score = sum(1 for signal in appearance_signals if signal.lower() in merged_text)
    lifestyle_score = sum(1 for signal in lifestyle_scene_signals if signal.lower() in merged_text)

    if function_score >= 2 or lifestyle_score >= 1:
        normalized["category"] = "功能示意图"
        if image_type in {"产品照片", "模特佩戴图"}:
            normalized["image_type"] = "海报功能图"
        return normalized

    if appearance_score >= 1:
        normalized["category"] = "产品外观图"
        return normalized

    normalized["category"] = safe_text(normalized.get("category"), "功能示意图")
    return normalized


def analyze_product_summary(api_key, image_paths):
    image_names = ", ".join(path.name for path in image_paths)
    prompt = (
        "Analyze these product images from a general product-marketing perspective and return strict JSON only. "
        "Do not assume the product is a ring or wearable unless the images clearly show that. "
        "The JSON keys must be: "
        "product_name_cn, product_name_en, product_type_cn, product_type_en, "
        "one_sentence_positioning_cn, target_price_band_cn, optional_colors_cn, optional_sizes_cn, battery_life_cn, purchase_link, "
        "core_functions_cn, feature_keywords_en, primary_use_scenarios_cn, suitable_talent_or_user_types_cn, "
        "visual_style_cn, material_texture_cn, selling_points_cn, conversion_points_cn, risk_or_missing_info_cn, "
        "smart_select_image_strategy_cn, prompt_direction_cn, video_marketing_points_cn, target_audience_cn, "
        "conversion_hook_angles_cn, image_usage_overview_cn. "
        "Use Chinese for *_cn fields and English for *_en fields. "
        "Use arrays for list-like fields. "
        "Be specific, useful, and commercially practical for downstream image selection and video prompt generation. "
        "When the image does not explicitly show a fact, infer conservatively from visible evidence instead of leaving blank. "
        "Do not output placeholders like unknown, N/A, 待识别, 未识别. "
        f"Included image files: {image_names}."
    )
    content = [{"type": "text", "text": prompt}]
    for image_path in image_paths:
        content.append({"type": "image_url", "image_url": {"url": encode_image(image_path)}})
    return extract_json(request_glm(api_key, content))


def analyze_single_image(api_key, image_path):
    prompt = (
        "Analyze this single product image for downstream marketing asset selection and return strict JSON only. "
        "The JSON keys must be: "
        "file_name, category, image_type, color, scene_or_purpose, extracted_copy_points, "
        "is_product_related, notes, marketing_role_cn, prompt_value_cn. "
        "Use Chinese for category, image_type, color, scene_or_purpose, notes. "
        "Use English short phrases in extracted_copy_points if visible copy is English; "
        "otherwise summarize the visible selling points in concise Chinese phrases. "
        "category must be one of: 产品外观图, 功能示意图, 不相关图片. "
        "image_type should be a short Chinese label like 产品照片, 海报功能图, 规格图, 模特佩戴图, APP界面图. "
        "marketing_role_cn should explain how this image helps conversion, such as 外观种草, 功能背书, 参数说明, 场景代入, 材质细节. "
        "prompt_value_cn should explain how this image should be used for later video generation or image selection. "
        "is_product_related must be true or false."
    )
    content = [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": encode_image(image_path)}},
    ]
    data = extract_json(request_glm(api_key, content))
    data["file_name"] = image_path.name
    return data


def fallback_image_row(image_path, error_message):
    return {
        "file_name": image_path.name,
        "category": "功能示意图",
        "image_type": "待重试识别",
        "color": "-",
        "scene_or_purpose": "识别暂未完成",
        "extracted_copy_points": [f"GLM retry needed: {safe_text(error_message, 'unknown error')}"],
        "is_product_related": True,
        "notes": "本张图片因接口限流未完成识别，可再次运行脚本续跑。",
    }


def should_retry_cached_row(row):
    notes = safe_text((row or {}).get("notes"))
    image_type = safe_text((row or {}).get("image_type"))
    return "限流" in notes or image_type == "待重试识别"


def markdown_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        safe_row = [safe_text(cell, "-").replace("|", "/") for cell in row]
        lines.append("| " + " | ".join(safe_row) + " |")
    return "\n".join(lines)


def build_report(summary, image_rows):
    product_name_cn = normalize_summary_value(summary.get("product_name_cn"), fallback_summary_text("product_name_cn"))
    product_name_en = normalize_summary_value(summary.get("product_name_en"), fallback_summary_text("product_name_en"))
    product_type_cn = normalize_summary_value(summary.get("product_type_cn"), fallback_summary_text("product_type_cn"))
    product_type_en = normalize_summary_value(summary.get("product_type_en"), fallback_summary_text("product_type_en"))
    purchase_link = normalize_summary_value(summary.get("purchase_link"), fallback_summary_text("purchase_link"))
    usage_overview = normalize_summary_value(summary.get("image_usage_overview_cn"), fallback_summary_text("usage_overview"))
    visual_style = normalize_summary_value(summary.get("visual_style_cn"), "整体视觉更偏产品展示与场景代入混合表达。")
    material_texture = normalize_summary_value(summary.get("material_texture_cn"), "材质信息可从表面反光、边缘处理和局部特写中提炼。")
    core_functions = normalize_list(summary.get("core_functions_cn"))
    feature_keywords = normalize_list(summary.get("feature_keywords_en"))
    primary_scenarios = normalize_list(summary.get("primary_use_scenarios_cn"))
    talent_or_user_types = normalize_list(summary.get("suitable_talent_or_user_types_cn"))
    selling_points = normalize_list(summary.get("selling_points_cn"))
    marketing_points = normalize_list(summary.get("video_marketing_points_cn"))
    target_audience = normalize_list(summary.get("target_audience_cn"))
    conversion_points = normalize_list(summary.get("conversion_points_cn"))
    hook_angles = normalize_list(summary.get("conversion_hook_angles_cn"))
    image_strategy = normalize_summary_value(summary.get("smart_select_image_strategy_cn"), "后续选图应优先平衡外观图、功能图、场景图与参数说明图。")
    prompt_direction = normalize_summary_value(summary.get("prompt_direction_cn"), "后续视频 prompt 应围绕真实使用场景、核心功能展示和可剪辑模块化镜头展开。")

    confirmed_color_text = summarize_color_tags(image_rows)
    confirmed_scene_text = summarize_scene_tags(image_rows)

    appearance_rows = []
    function_rows = []
    unrelated_rows = []

    for row in image_rows:
        category = safe_text(row.get("category"), "功能示意图")
        file_name = safe_text(row.get("file_name"), "-")
        image_type = safe_text(row.get("image_type"), "-")
        color = safe_text(row.get("color"), "-")
        scene = safe_text(row.get("scene_or_purpose"), "-")
        copy_points = safe_text(", ".join(normalize_list(row.get("extracted_copy_points"))), "画面文案较少，建议以后续视觉表达为主。")
        marketing_role = safe_text(row.get("marketing_role_cn"), "可用于补充卖点表达")
        prompt_value = safe_text(row.get("prompt_value_cn"), "可作为后续镜头设计与选图的辅助参考")
        notes = safe_text(row.get("notes"), "-")

        if category == "产品外观图":
            appearance_rows.append([file_name, image_type, color, scene])
        elif category == "不相关图片" or row.get("is_product_related") is False:
            unrelated_rows.append([file_name, safe_text(row.get("image_type"), "非产品图"), notes])
        else:
            function_rows.append([file_name, f"{scene} / {marketing_role}", f"{copy_points} / {prompt_value}"])

    lines = [
        f"# {product_name_en} - ZAI 图片识别报告",
        "",
        "## 图片中可直接确认的信息",
        "",
        f"- **产品名称**: {product_name_cn} ({product_name_en})",
        f"- **产品类型**: {product_type_cn} ({product_type_en})",
        f"- **购买链接**: {purchase_link}",
        f"- **图片中可见主色/配色线索**: {confirmed_color_text}",
        f"- **图片中已覆盖的场景线索**: {confirmed_scene_text}",
        f"- **视觉风格**: {visual_style}",
        f"- **材质质感**: {material_texture}",
        "",
        "---",
        "",
        "## 图片分类汇总",
        "",
        f"### 一、产品外观图 ({len(appearance_rows)}张) - 用于 Seedance 参考",
        "",
        markdown_table(["文件", "类型", "颜色", "场景/用途"], appearance_rows or [["-", "-", "-", "-"]]),
        "",
        f"### 二、功能示意图 ({len(function_rows)}张) - 用于文案提取",
        "",
        markdown_table(["文件", "内容", "提取文案要点"], function_rows or [["-", "-", "-"]]),
        "",
        f"### 三、不相关图片 ({len(unrelated_rows)}张)",
        "",
        markdown_table(["文件", "识别结果", "说明"], unrelated_rows or [["-", "-", "-"]]),
        "",
        "---",
        "",
        "## 产品核心功能点 (从文案提取)",
        "",
    ]

    if core_functions:
        for idx, item in enumerate(core_functions, start=1):
            lines.append(f"{idx}. {item}")
    else:
        lines.append("- 画面中可提炼的核心功能有限，建议结合功能示意图和文案图继续补强。")

    lines.extend([
        "",
        "---",
        "",
        "## 选图与 Prompt 素材",
        "",
        "### 英文特征关键词",
    ])
    if feature_keywords:
        for item in feature_keywords:
            lines.append(f"- {item}")
    else:
        lines.append("- Feature keywords should be refined from visible product shape, usage scene, and UI or copy cues.")

    lines.extend([
        "",
        "### 主使用场景",
    ])
    if primary_scenarios:
        for item in primary_scenarios:
            lines.append(f"- {item}")
    else:
        lines.append("- 画面主要支持从外观展示、功能演示和生活化代入三个方向选图。")

    lines.extend([
        "",
        "### 适合的出镜人设/用户类型",
    ])
    if talent_or_user_types:
        for item in talent_or_user_types:
            lines.append(f"- {item}")
    else:
        lines.append("- 可优先匹配与画面场景一致的生活方式人设，而不是泛泛的模特表达。")

    lines.extend([
        "",
        "### 智能选图策略",
        "",
        f"- {image_strategy}",
        "",
        "### 后续 Prompt 方向",
        "",
        f"- {prompt_direction}",
        "",
        "## 图片用途概览",
        "",
        f"- {usage_overview}",
        "",
        "---",
        "",
        "## 产品卖点拆解",
        "",
        "### 卖点清单",
    ])
    if selling_points:
        for item in selling_points:
            lines.append(f"- {item}")
    else:
        lines.append("- 卖点可从外观质感、使用结果、参数证明和生活方式代入四个角度拆解。")

    lines.extend([
        "",
        "## 视频营销要点",
        "",
        "### 主推卖点",
    ])

    if marketing_points:
        for idx, item in enumerate(marketing_points, start=1):
            lines.append(f"{idx}. {item}")
    else:
        lines.append("1. 建议从最直观的外观价值、最强功能利益点和最高频使用场景三个方向做主推卖点。")

    lines.extend([
        "",
        "### 目标人群",
    ])
    if target_audience:
        for item in target_audience:
            lines.append(f"- {item}")
    else:
        lines.append("- 目标人群可优先围绕画面中已经出现的典型使用场景和生活方式来收敛。")

    lines.extend([
        "",
        "### 营销转化要点",
    ])
    if conversion_points:
        for item in conversion_points:
            lines.append(f"- {item}")
    else:
        lines.append("- 转化表达建议优先强调结果感、使用门槛低、适用场景广和差异化细节。")

    lines.extend([
        "",
        "### 转化切入角度",
    ])
    if hook_angles:
        for item in hook_angles:
            lines.append(f"- {item}")
    else:
        lines.append("- 可从痛点对比、使用前后、生活方式代入、细节特写背书几个方向切入。")

    lines.extend([
        "",
        f"*报告生成时间: {date.today().isoformat()}*",
        f"*识别工具: 智谱清言 {MODEL_NAME}*",
    ])
    return "\n".join(lines) + "\n"


def build_rows_from_cache(images, cache_data):
    image_rows = []
    for image_path in images:
        row = cache_data.get(image_path.name)
        if row:
            image_rows.append(normalize_image_row(row))
        else:
            image_rows.append(fallback_image_row(image_path, "pending analysis"))
    return image_rows


def main():
    if len(sys.argv) != 2:
        print("Usage: ZHIPU_API_KEY=... python3 scripts/analyze_products_glm.py /path/to/project")
        sys.exit(1)

    project_dir = Path(sys.argv[1]).expanduser().resolve()
    products_dir = project_dir / "products"
    report_path = products_dir / "ZAI_full_analysis_report.md"
    cache_path = products_dir / CACHE_FILE_NAME
    api_key = os.environ.get("ZHIPU_API_KEY")

    if not api_key:
        print("Missing ZHIPU_API_KEY")
        sys.exit(1)
    if not products_dir.exists():
        print(f"Missing products directory: {products_dir}")
        sys.exit(1)

    images = collect_images(products_dir)
    if not images:
        print(f"No product images found in: {products_dir}")
        sys.exit(1)

    cache_data = load_cache(cache_path)
    summary_images = images[:SUMMARY_IMAGE_LIMIT]
    if "summary" not in cache_data:
        print(f"Analyzing {len(summary_images)} summary images with {MODEL_NAME}")
        cache_data["summary"] = analyze_product_summary(api_key, summary_images)
        save_cache(cache_path, cache_data)
    summary = cache_data["summary"]

    image_rows = []
    for index, image_path in enumerate(images, start=1):
        print(f"[{index}/{len(images)}] {image_path.name}")
        cache_key = image_path.name
        if cache_key not in cache_data or should_retry_cached_row(cache_data.get(cache_key)):
            try:
                cache_data[cache_key] = analyze_single_image(api_key, image_path)
            except Exception as exc:
                cache_data[cache_key] = fallback_image_row(image_path, str(exc))
            save_cache(cache_path, cache_data)
            report_path.write_text(
                build_report(summary, build_rows_from_cache(images, cache_data)),
                encoding="utf-8",
            )
            time.sleep(2)
        image_rows.append(cache_data[cache_key])

    report_path.write_text(build_report(summary, image_rows), encoding="utf-8")
    print(f"Saved report: {report_path}")


if __name__ == "__main__":
    main()
