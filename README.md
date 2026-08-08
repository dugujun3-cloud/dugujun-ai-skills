# dugujun-ai-skills

卢国军公开的 Agent Skills。基于使用 AI Agent 的实践经验整理，可安装到 Claude Code、Cursor、Codex、Grok 等支持 [Agent Skills](https://skills.sh/) 的工具。

## 包含的 skill

| Skill | 作用 |
|-------|------|
| **ai-delivery-over-chat** | 诊断「用 AI 越用越累」：根因多半是聊天式用法，不是模型本身。三关自检 + 从陪聊推进到能交。 |

## 安装（给使用者）

需要本机已装 Node.js（有 `npx`）。

### 安装本仓库全部 skill

```bash
npx skills add dugujun3-cloud/dugujun-ai-skills
```

### 只装「别陪聊，要能交」

```bash
npx skills add dugujun3-cloud/dugujun-ai-skills@ai-delivery-over-chat
```

### 装到全局（所有项目可用）

```bash
npx skills add dugujun3-cloud/dugujun-ai-skills@ai-delivery-over-chat -g
```

### 指定 Agent

```bash
npx skills add dugujun3-cloud/dugujun-ai-skills@ai-delivery-over-chat -a claude-code
npx skills add dugujun3-cloud/dugujun-ai-skills@ai-delivery-over-chat -a cursor
```

安装前请打开本仓库阅读 `SKILL.md`（第三方 skill 拥有与 Agent 相同的文件权限）。

## 触发示例

装好后，在对话里说例如：

- 「我用 AI 改活动表改了一个小时更累了，帮我诊断」
- 「是不是该换更强的模型？」
- `/ai-delivery-over-chat`

## 仓库结构

```text
dugujun-ai-skills/
├── README.md
├── LICENSE
└── skills/
    └── ai-delivery-over-chat/
        ├── SKILL.md
        └── references/
            ├── framework.md
            ├── self-check.md
            └── sources.md
```

## 关于

基于卢国军使用 AI Agent 的经验形成。说明见 skill 内 `references/sources.md`。

## License

MIT
