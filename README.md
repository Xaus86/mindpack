# 🧠 MindPack

**让你的 AI 助理真正记住你。**

MindPack 是一套为 OpenClaw 打造的技能包，包含长期记忆、会话搜索和自动创建技能的能力。解决 AI 助理"每次对话都是陌生人"的痛点。

---

## 这个项目解决什么问题？

你有没有遇到过这种情况——

> 上周我们讨论过 XX 项目用 Vue 还是 React，你说倾向 React，但 AI 完全不记得。
> 你纠正过一次"我不喜欢太啰嗦的回复"，结果下一周 AI 依然长篇大论。

**因为大多数 AI 助理根本没有记忆。**

MindPack 把记忆能力带回来。

---

## 三个技能

### 📚 Session Search — 找到过去的对话

用过但忘了在哪？Session Search 帮你搜索全部历史会话，基于内容相关性而非时间顺序。

```
你：上次我们聊过 K8s 部署的那些内容？
AI：找到 2 个相关会话，分别是 4 月 15 日和 4 月 22 日的讨论。
```

### ✨ Skill Creator — 让 AI 学会新技能

发现一个工作流程值得复用？一键把它变成可重用的技能，AI 下次遇到类似任务自动调用。

```
你：把我们部署流程做成技能
AI：已创建 'deploy-workflow' 技能。
    下次部署时说"用 deploy-workflow" 就行。
```

### 💾 Memory Manager — 持久记忆，不用重复

AI 会主动捕捉值得记住的信息，你也可以随时告诉它。

```
你：我喜欢简洁的回复
AI：💡 要记住这个偏好吗？
```

---

## 安装

```bash
# 克隆到本地
git clone https://github.com/Xaus86/mindpack.git

# 复制到 OpenClaw skills 目录
cp -r mindpack/* ~/.openclaw/workspace/skills/
```

然后重启 OpenClaw 即可。

---

## 工作原理

| 技能 | 存储位置 | 数据来源 |
|------|---------|---------|
| session-search | SQLite + FTS5 | OpenClaw 会话历史 |
| skill-creator | `~/.openclaw/workspace/skills/` | 手动/自动创建 |
| memory-manager | `MEMORY.md` + `USER.md` | 实时学习 |

---

## 技术细节

- **会话索引**：Python 3 + SQLite FTS5，后台每 30 分钟自动更新
- **技能格式**：纯 SKILL.md，完全兼容 OpenClaw 技能系统
- **记忆管理**：文件持久化，支持健康检查和自动清理

---

## 兼容性

- ✅ 不依赖 OpenClaw 内部 API
- ✅ 不修改 OpenClaw 核心代码
- ✅ 大版本升级后依然可用
- ✅ 支持 macOS / Linux / Windows (WSL)

---

## 关于作者

初衷是给 OpenClaw 加上 Hermes Agent 那样的自学习能力，但用更轻量的方式实现。

如果你也有类似需求，欢迎 Fork 和贡献代码。

---

**许可证**：MIT  
**作者**：[@Xaus86](https://github.com/Xaus86)
