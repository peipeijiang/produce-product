#!/bin/bash

# 产品营销视频制作 Web 应用 - 一键启动脚本

set -e

echo "🚀 产品营销视频制作 - 启动脚本"
echo "=================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查是否已经启动 Mock Server
check_mock_server() {
    if curl -s http://localhost:3456/ > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Mock Server 已经在运行${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Mock Server 未运行${NC}"
        return 1
    fi
}

# 启动 Mock Server
start_mock_server() {
    echo "正在启动 Mock Server..."
    cd /Users/shane/.openclaw/workspace/skills/produce-product/Seedance2-Chrome-Extensions
    node mock-server.js > /dev/null 2>&1 &
    MOCK_PID=$!

    # 等待 Mock Server 启动
    for i in {1..10}; do
        sleep 1
        if curl -s http://localhost:3456/ > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Mock Server 启动成功 (PID: $MOCK_PID)${NC}"
            return 0
        fi
    done

    echo -e "${RED}✗ Mock Server 启动失败${NC}"
    return 1
}

# 检查是否已经启动 Web 应用
check_web_app() {
    if curl -s http://localhost:5173/ > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Web 应用已经在运行${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Web 应用 未运行${NC}"
        return 1
    fi
}

# 启动 Web 应用
start_web_app() {
    echo "正在启动 Web 应用..."
    cd /Users/shane/.openclaw/workspace/skills/produce-product/web/enterprise-app
    npm run dev > /dev/null 2>&1 &
    WEB_PID=$!

    # 等待 Web 应用启动
    for i in {1..10}; do
        sleep 1
        if curl -s http://localhost:5173/ > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Web 应用 启动成功 (PID: $WEB_PID)${NC}"
            return 0
        fi
    done

    echo -e "${RED}✗ Web 应用 启动失败${NC}"
    return 1
}

# 打开浏览器
open_browser() {
    echo "正在打开浏览器..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open http://localhost:5173
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open http://localhost:5173
    else
        echo "请在浏览器中打开 http://localhost:5173"
    fi
}

# 主流程
main() {
    # 检查 Mock Server
    if ! check_mock_server; then
        if ! start_mock_server; then
            exit 1
        fi
    fi

    echo ""

    # 检查 Web 应用
    if ! check_web_app; then
        if ! start_web_app; then
            exit 1
        fi
    fi

    echo ""

    # 打开浏览器
    open_browser

    echo ""
    echo -e "${GREEN}✓ 所有服务已启动${NC}"
    echo "=================================="
    echo "Mock Server: http://localhost:3456"
    echo "Web 应用:    http://localhost:5173"
    echo ""
    echo "💡 提示: 按 Ctrl+C 可以停止此脚本，但服务会继续在后台运行"
    echo ""
}

# 运行主流程
main

# 保持脚本运行
wait
