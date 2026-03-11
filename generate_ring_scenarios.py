#!/usr/bin/env python3
"""
生成 5 个英文口播带字幕的智能戒指视频任务
"""
import json
import os

# 项目配置
project_id = "PV-002-RING"
project_name = "JELLY BELLES Smart Ring"
project_dir = "/Users/shane/Downloads/Micro-Drama-Skills-main/projects/PV-002-戒指_product"

# 5 个场景配置
scenarios = [
    {
        "id": "V1_SLEEP",
        "name": "Sleep Health Monitoring",
        "duration": "10s",
        "description": "Sleep Health Monitoring 10s with English voiceover and subtitles",
        "reference_files": [
            "keyframes/ring-01_part_15.jpg",
            "keyframes/ring-01_part_14.jpg",
            "keyframes/ring-01_part_16.jpg"
        ],
        "prompt": """(@ring-01_part_15.jpg) is JELLY BELLES smart ring showing elegant gold design on finger. (@ring-01_part_14.jpg) displays smart ring during sleep monitoring. (@ring-01_part_16.jpg) shows sleep data analysis on phone screen. Sleep health monitoring video. Scene 1 [0-3s]: Person in bed hand reaching for phone with smart ring visible on finger. Text overlay: Track your sleep quality 24/7. Scene 2 [3-7s]: Close-up of ring on finger sleeping peacefully. Phone screen displays sleep data with metrics: REM Analysis Deep Sleep Light Sleep Smart Insights. Text overlay: REM Analysis | Deep Sleep | Light Sleep | Smart Insights. Scene 3 [7-10s]: Person wakes up refreshed checking phone for sleep summary. Ring gleams on finger. Text overlays: Better Sleep Better Day JELLY BELLES Smart Ring. CRITICAL: Include ENGLISH VOICEOVER throughout: Sleep better with JELLY BELLES Smart Ring. Track your sleep quality 24/7. It analyzes your REM deep sleep and light sleep patterns. Get smart insights to improve your rest. Wake up refreshed and ready for day. Your wellness journey starts with better sleep. Include ENGLISH SUBTITLES matching all text overlays. Fast-paced engaging style 9:16 10 seconds."""
    },
    {
        "id": "V2_FITNESS",
        "name": "Fitness Athlete Companion",
        "duration": "10s",
        "description": "Fitness Athlete Companion 10s with English voiceover and subtitles",
        "reference_files": [
            "keyframes/ring-01_part_09.jpg",
            "keyframes/ring-01_part_10.jpg",
            "keyframes/ring-01_part_12.jpg"
        ],
        "prompt": """(@ring-01_part_09.jpg) shows person running outdoors with JELLY BELLES smart ring visible. (@ring-01_part_10.jpg) displays multiple exercise modes on phone screen. (@ring-01_part_12.jpg) shows heart rate monitoring feature. Fitness athlete companion video. Scene 1 [0-3s]: Person running with ring on finger phone tracking activity in background. Text overlay: Workout Tracking Made Easy. Scene 2 [3-7s]: Phone screen displays multiple exercise modes with icons: Run Cycle Hike Golf. Person doing different exercises with ring tracking. Text overlay: 12+ Exercise Modes Run Cycle Hike Golf. Scene 3 [7-10s]: Person finishing workout checking statistics on phone. Ring sparkling on finger. Text overlays: Precise Data Every Step The Athlete's Choice. CRITICAL: Include ENGLISH VOICEOVER throughout: Take your fitness to the next level with JELLY BELLES Smart Ring. It tracks 12+ exercise modes including running cycling hiking and golf. Monitor your heart rate steps calories and distance with precision. Know your progress every step of the way. The athlete's choice for accurate convenient fitness tracking. Include ENGLISH SUBTITLES matching all text overlays. Dynamic energetic style 9:16 10 seconds."""
    },
    {
        "id": "V3_GESTURE",
        "name": "Smart Gesture Control",
        "duration": "10s",
        "description": "Smart Gesture Control 10s with English voiceover and subtitles",
        "reference_files": [
            "keyframes/ring-01_part_05.jpg",
            "keyframes/ring-01_part_07.jpg",
            "keyframes/ring-01_part_06.jpg"
        ],
        "prompt": """(@ring-01_part_05.jpg) shows person doing double-tap gesture with JELLY BELLES smart ring. (@ring-01_part_07.jpg) demonstrates remote selfie feature. (@ring-01_part_06.jpg) displays person using phone with ring control. Smart gesture control video. Scene 1 [0-3s]: Person scrolling TikTok with ring phone screen changes content smoothly. Text overlay: Gesture Control Without Touching. Scene 2 [3-7s]: Close-up of double tap gesture videos switch on phone. Person swiping through content with hand gesture. Text overlay: Double Tap to Switch Content Gesture Brush. Scene 3 [7-10s]: Person using ring to take selfie remotely phone captures photo. Ring highlighted on finger. Text overlays: Remote Selfie Gesture Swing Control Everything. CRITICAL: Include ENGLISH VOICEOVER throughout: Control your phone without ever touching it. Simply double-tap your JELLY BELLES Smart Ring to switch between TikTok videos. Swipe through content with your hand. Even take remote selfies without reaching for your phone. Your smart assistant fits right on your finger making everything more convenient and effortless. Include ENGLISH SUBTITLES matching all text overlays. Tech-focused modern style 9:16 10 seconds."""
    },
    {
        "id": "V4_HEALTH",
        "name": "Real-Time Health Tracker",
        "duration": "10s",
        "description": "Real-Time Health Tracker 10s with English voiceover and subtitles",
        "reference_files": [
            "keyframes/ring-01_part_13.jpg",
            "keyframes/ring-01_part_12.jpg",
            "keyframes/ring-01_part_17.jpg"
        ],
        "prompt": """(@ring-01_part_13.jpg) shows JELLY BELLES smart ring blood oxygen monitoring feature. (@ring-01_part_12.jpg) displays heart rate tracking. (@ring-01_part_17.jpg) shows health data summary on phone. Real-time health tracker video. Scene 1 [0-3s]: Phone dashboard shows heart rate 72 BPM blood oxygen 98% metrics updating. Text overlay: 24/7 Health Guardian. Scene 2 [3-7s]: Multiple health metrics displayed on screen: Heart Rate SpO2 Fatigue Stress. Ring monitoring finger visible. Text overlay: Heart Rate SpO2 Fatigue Stress Monitoring. Scene 3 [7-10s]: Person checking health summary on phone with insights. Ring gleams on finger. Text overlay: Your Personal Health Companion. CRITICAL: Include ENGLISH VOICEOVER throughout: Your personal health companion always with you. JELLY BELLES Smart Ring monitors your heart rate and blood oxygen levels 24/7. Track your fatigue level stress indicators and overall wellness. Get instant health insights from your ring. Never miss important health data. Your wellness journey tracked in real-time. Include ENGLISH SUBTITLES matching all text overlays. Professional medical style 9:16 10 seconds."""
    },
    {
        "id": "V5_WATERPROOF",
        "name": "Waterproof Active Life",
        "duration": "10s",
        "description": "Waterproof Active Life 10s with English voiceover and subtitles",
        "reference_files": [
            "keyframes/ring-01_part_15.jpg",
            "keyframes/ring-01_part_19.jpg",
            "keyframes/ring-01_part_20.jpg"
        ],
        "prompt": """(@ring-01_part_15.jpg) shows JELLY BELLES smart ring gold design on finger. (@ring-01_part_19.jpg) displays battery life feature. (@ring-01_part_20.jpg) demonstrates waterproof capability. Waterproof active life video. Scene 1 [0-3s]: Person swimming underwater with ring clearly visible on finger. Text overlay: IP68 Waterproof Anytime Anywhere. Scene 2 [3-7s]: Ring floating in pool water phone showing heart rate metrics. Battery life indicator showing 5-7 days. Text overlay: 5-7 Day Battery Life All-Day Comfort. Scene 3 [7-10s]: Multiple rings gleaming in gold black silver colors. Lightweight comfortable. Text overlay: 3 Colors Light as Nothing Fashion & Function. CRITICAL: Include ENGLISH VOICEOVER throughout: Live life without limits. JELLY BELLES Smart Ring is IP68 waterproof so wear it swimming showering or in the rain. No need to recharge for 5-7 days with ultra-long battery life. Choose from three stunning colors gold black or silver. Lightweight and comfortable it's fashion meets function. Your ring goes everywhere you go. Include ENGLISH SUBTITLES matching all text overlays. Active lifestyle style 9:16 10 seconds."""
    }
]

def generate_tasks():
    """生成任务 JSON 文件"""

    for scenario in scenarios:
        task_data = {
            "project_id": f"{project_id}-{scenario['id']}",
            "project_name": f"{project_name} - {scenario['name']}",
            "project_type": "product",
            "video_structure": "single",
            "total_tasks": 1,
            "realSubmit": True,
            "tasks": [{
                "video_id": f"{project_id}-{scenario['id']}",
                "segment_index": 0,
                "prompt": scenario["prompt"],
                "description": scenario["description"],
                "modelConfig": {
                    "model": "Seedance 2.0 Fast",
                    "referenceMode": "全能参考",
                    "aspectRatio": "9:16",
                    "duration": scenario["duration"]
                },
                "referenceFiles": scenario["reference_files"],
                "videoReferences": [],
                "realSubmit": True,
                "priority": 1,
                "tags": ["PRODUCT", "RING", scenario["name"].replace(" ", "_"), "VOICEOVER", "SUBTITLE"],
                "dependsOn": []
            }]
        }

        # 保存到文件
        filename = f"seedance_tasks_{scenario['id']}.json"
        filepath = os.path.join(project_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(task_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Generated: {filename}")

    print(f"\n✅ Total: {len(scenarios)} tasks generated")
    print(f"📁 Location: {project_dir}")

if __name__ == "__main__":
    generate_tasks()
