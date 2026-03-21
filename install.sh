#!/bin/bash
# produce-product 一键安装脚本

set -e

echo "=============================================="
echo "  produce-product 一键安装脚本"
echo "=============================================="

# 1. 检查 Node.js
echo ""
echo "[1/5] 检查 Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    echo "   请先安装 Node.js: https://nodejs.org"
    exit 1
fi
echo "✅ Node.js: $(node -v)"

# 2. 检查 Python
echo ""
echo "[2/5] 检查 Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 未安装"
    echo "   请先安装 Python: https://www.python.org"
    exit 1
fi
echo "✅ Python: $(python3 --version)"

# 3. 安装扩展依赖
echo ""
echo "[3/5] 安装扩展依赖..."
cd "$(dirname "$0")/Seedance2-Chrome-Extensions"
npm install
echo "✅ npm install 完成"

# 4. 安装 Playwright Chromium
echo ""
echo "[4/5] 安装 Playwright Chromium..."
npx playwright install chromium
echo "✅ Playwright Chromium 安装完成"

# 5. 安装 Python 依赖
echo ""
echo "[5/5] 安装 Python 依赖..."
pip3 install requests pillow pyyaml
echo "✅ Python 依赖安装完成"

# 完成
echo ""
echo "=============================================="
echo "  ✅ 安装完成！"
echo "=============================================="
echo ""
echo "下一步："
echo "1. 启动 Mock Server:"
echo "   cd Seedance2-Chrome-Extensions"
echo "   node mock-server.js &"
echo ""
echo "2. 启动 Chrome + 扩展:"
echo "   bash scripts/start-chrome.sh &"
echo ""
echo "3. 运行 produce-product:"
echo "   python3 scripts/generate_tasks.py /path/to/project"
echo "   python3 scripts/convert_to_base64_fixed.py /path/to/project"
echo "   python3 scripts/submit_tasks.py /path/to/project"
