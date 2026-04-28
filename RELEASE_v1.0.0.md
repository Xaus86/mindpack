# 🧠 MindPack v1.0.0

**让你的 AI 助理真正记住你。**

> 首个正式版本发布

---

## 📦 版本信息

- **版本**：v1.0.0
- **发布日期**：2026-04-28
- **许可证**：MIT

---

## ✨ 新功能

### 📚 Session Search
- SQLite FTS5 全文搜索
- 自动后台索引（每 30 分钟）
- 相关会话 AI 摘要
- 隐私保护（仅搜索直接对话）

### ✨ Skill Creator
- 标准化 SKILL.md 格式
- 技能质量验证工具
- AI 辅助技能创建流程
- 最佳实践指南

### 💾 Memory Manager
- 主动记忆建议
- 记忆健康检查报告
- 自动去重和清理
- Frozen Snapshot 模式

---

## 🚀 快速开始

```bash
# 1. 克隆
git clone https://github.com/Xaus86/mindpack.git

# 2. 安装
cd mindpack
cp -r session-search skill-creator memory-manager ~/.openclaw/workspace/skills/

# 3. 重启 OpenClaw
openclaw restart
```

---

## 📁 项目结构

```
mindpack/
├── session-search/       # 会话搜索技能
│   └── scripts/
│       ├── index_sessions.py    # 索引脚本
│       └── search_sessions.py   # 搜索脚本
├── skill-creator/       # 技能创建技能
│   └── scripts/
│       ├── validate_skill.py    # 验证工具
│       └── auto_create_skill.py # 自动创建
├── memory-manager/       # 记忆管理技能
│   └── scripts/
│       └── memory_maintenance.py # 维护脚本
└── README.md
```

---

## 🔧 系统要求

- OpenClaw 已安装并配置
- Python 3.8+
- macOS / Linux / Windows (WSL)

---

## 📝 更新日志

### v1.0.0 (2026-04-28)
- 首个正式版本
- 三个核心技能：session-search, skill-creator, memory-manager
- 后台自动索引和维护 cron 任务

---

## 🙏 致谢

灵感来自 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 的自学习能力，MindPack 用更轻量的方式为 OpenClaw 用户带来类似体验。

---

**下载地址**：https://github.com/Xaus86/mindpack/archive/refs/tags/v1.0.0.zip
