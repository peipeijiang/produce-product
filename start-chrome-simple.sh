#!/bin/bash
# 简化启动 Chrome + Seedance 扩展

cd "$(dirname "$0")/Seedance2-Chrome-Extensions"

echo "✅ 启动 Chrome 浏览器（简化模式）..."
echo "⚠️  请手动加载 Seedance 扩展"
echo ""
echo "📋 手动加载步骤："
echo "1. 打开 Chrome 浏览器"
echo "2. 地址栏输入：chrome://extensions/"
echo "3. 开启“开发者模式”（右上角开关）"
echo "4. 点击“加载已解压的扩展程序”"
echo "5. 选择扩展文件夹："
echo "   /Users/shane/.openclaw/workspace/skills/produce-product/Seedance2-Chrome-Extensions"
echo ""
echo "6. 确认权限（允许访问所有网站）"
echo ""
echo "✅ 加载完成后，打开即梦网站："
echo "   https://jimeng.jianying.com/ai-tool/image/generate"
echo ""
echo "📌 扩展会自动连接到 Mock Server（http://localhost:3456）"
echo ""
echo "💡 如果任务没有自动处理，可以在即梦网站手动选择图片和填写 prompt"
