#!/bin/bash
#
# MindPack Installer
# 一键安装 MindPack 到 OpenClaw
#

set -e

echo "🧠 MindPack Installer"
echo "====================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check OpenClaw
if [ ! -d "$HOME/.openclaw/workspace/skills" ]; then
    echo -e "${RED}❌ 错误：找不到 OpenClaw skills 目录${NC}"
    echo "   请确认 OpenClaw 已正确安装"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$HOME/.openclaw/workspace/skills"

echo "📦 安装 MindPack 到: $SKILLS_DIR"
echo ""

# Install each skill
install_skill() {
    local skill_name="$1"
    local skill_path="$SCRIPT_DIR/$skill_name"
    
    if [ ! -d "$skill_path" ]; then
        echo -e "${YELLOW}⚠️  跳过 $skill_name（目录不存在）${NC}"
        return
    fi
    
    if [ -d "$SKILLS_DIR/$skill_name" ]; then
        echo -e "${YELLOW}⚠️  $skill_name 已存在，是否覆盖？ [y/N]${NC}"
        read -r response
        if [ "$response" != "y" ] && [ "$response" != "Y" ]; then
            echo "   跳过 $skill_name"
            return
        fi
        rm -rf "$SKILLS_DIR/$skill_name"
    fi
    
    cp -r "$skill_path" "$SKILLS_DIR/"
    echo -e "${GREEN}✅ 安装 $skill_name${NC}"
}

install_skill "session-search"
install_skill "skill-creator"
install_skill "memory-manager"

echo ""
echo "====================="
echo -e "${GREEN}🎉 安装完成！${NC}"
echo ""
echo "下一步："
echo "  1. 重启 OpenClaw: openclaw restart"
echo "  2. 索引现有会话: python3 ~/.openclaw/workspace/skills/session-search/scripts/index_sessions.py"
echo ""
echo "📚 使用方法："
echo "  - 会话搜索：'上次我们聊过什么？'"
echo "  - 创建技能：'把这个做成技能'"
echo "  - 记忆管理：'记住我喜欢简洁的回复'"
echo ""
