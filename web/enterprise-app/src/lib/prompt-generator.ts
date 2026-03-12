// Prompt 生成器

import type { MarketingAngle } from './types';

// 营销角度定义
const MARKETING_ANGLES: MarketingAngle[] = [
  { name: 'Premium_Luxury', feature: 'premium craftsmanship and elegant design' },
  { name: 'Smart_Features', feature: 'innovative smart features' },
  { name: 'Lifestyle_Daily', feature: 'seamless daily integration' },
  { name: 'Performance_Quality', feature: 'exceptional performance and reliability' },
  { name: 'Best_Value', feature: 'unbeatable value and benefits' }
];

/**
 * 生成 Hook-Body-CTA 结构的营销 Prompt
 */
export function generateMarketingPrompt(
  productName: string,
  angle: MarketingAngle,
  duration: number,
  options: {
    enableVoiceover: boolean;
    enableSubtitles: boolean;
    enableHookCta: boolean;
  }
): string {
  const { enableVoiceover, enableSubtitles, enableHookCta } = options;
  const feature = angle.feature;

  let prompt = `(@selected_images) `;

  if (enableHookCta) {
    const hookEnd = Math.floor(duration * 0.2);
    const bodyStart = Math.floor(duration * 0.2);
    const bodyEnd = Math.floor(duration * 0.8);
    const ctaStart = Math.floor(duration * 0.8);

    prompt += `HOOK-Body-CTA structured marketing video for ${productName}.\n\n`;
    prompt += `HOOK [0-${hookEnd}s]: Eye-catching opening. Product revealed dramatically. Text overlay: "Upgrade Your Life Today". Dynamic camera movement. ${productName} takes center stage.\n\n`;
    prompt += `BODY [${bodyStart}-${bodyEnd}s]: Feature showcase: ${feature}. Person using product in real-life scenario. Multiple angles showing design excellence. Smooth transitions between scenes. Text overlays appear dynamically: "Premium Quality", "Smart Design", "Daily Essential". Close-up shots highlight details. Product demonstrates its value through action.\n\n`;
    prompt += `CTA [${ctaStart}-${duration}s]: Strong call to action. Final dramatic shot of ${productName}. Text overlay: "Shop Now - Limited Time Offer". Urgent feeling. Product name displayed prominently. Bold, confident ending.\n\n`;
  } else {
    prompt += `Marketing video for ${productName}.\n\n`;
    prompt += `Feature showcase: ${feature}. Person using product in real-life scenario. Multiple angles showing design excellence. Smooth transitions between scenes. Text overlays: "Premium Quality", "Smart Design", "Daily Essential".\n\n`;
  }

  // 添加语音和字幕
  if (enableVoiceover) {
    prompt += `CRITICAL: Include professional English voiceover throughout: "Ready to upgrade your daily routine? This is ${productName}. Experience premium quality and smart design that fits perfectly into your life.`;
    
    if (enableHookCta) {
      prompt += ` Don't wait, transform your experience today. Shop now limited time offer."`;
    }
    
    prompt += `"`;
  }

  if (enableSubtitles) {
    prompt += ` Include matching English subtitles.`;
  }

  prompt += ` Cinematic style 9:16 ${duration}s.`;

  return prompt;
}

/**
 * 生成任务 JSON
 */
export function generateTaskJson(
  productId: string,
  productName: string,
  angle: MarketingAngle,
  duration: number,
  materials: { fileName: string; base64: string }[],
  options: {
    enableVoiceover: boolean;
    enableSubtitles: boolean;
    enableHookCta: boolean;
  }
) {
  const prompt = generateMarketingPrompt(productName, angle, duration, options);

  return {
    project_id: `PRODUCT-${productId}_${angle.name}`,
    project_name: `${productName} - ${angle.name.replace(/_/g, ' ')} ${duration}s`,
    project_type: 'product',
    video_structure: 'single',
    total_tasks: 1,
    realSubmit: true,
    tasks: [{
      video_id: `PRODUCT-${productId}_${angle.name}`,
      segment_index: 0,
      prompt,
      description: `${angle.name.replace(/_/g, ' ')} ${duration}s`,
      modelConfig: {
        model: 'Seedance 2.0 Fast',
        referenceMode: '全能参考',
        aspectRatio: '9:16',
        duration: duration // 纯数字
      },
      referenceFiles: materials,
      videoReferences: [],
      realSubmit: true,
      priority: 1,
      tags: ['PRODUCT', productName.replace(/ /g, '_'), angle.name, 'VOICEOVER', 'SUBTITLE'],
      dependsOn: []
    }]
  };
}

/**
 * 获取所有营销角度
 */
export function getMarketingAngles() {
  return MARKETING_ANGLES;
}
