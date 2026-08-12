# dugujun-ai-skills

卢国军公开的 Agent Skills。基于使用 AI Agent 的实践经验整理，可安装到 Claude Code、Cursor、Codex、Grok 等支持 [Agent Skills](https://skills.sh/) 的工具。

部分 skill 同步用于小红书创作服务平台（Red Skill）公开领取。

## 包含的 skill

| Skill | 作用 |
|-------|------|
| **ai-delivery-over-chat** | 诊断「用 AI 越用越累」：根因多半是聊天式用法，不是模型本身。三关自检 + 从陪聊推进到能交。 |
| **retention-ltv-diagnostic-starter** | 复购/留存与观察窗口用户价值诊断：先对齐 6 项数据口径，再给可小范围验证的方向。 |
| **membership-activity-roi-checker** | 会员活动增量 ROI 体检：对照/基线、完整成本、证据等级与续投/调整/停止决策卡。 |
| **user-operations-playbook** | 用户运营全域诊断与设计（17 个高频领域）：目标→机制→指标→护栏→停止条件。 |
| **ai-interview-copilot** | 证据驱动的 AI 面试准备与复盘：岗位拆解、硬门槛、模拟、逐字稿复盘与结果校准。 |

## 安装（给使用者）

需要本机已装 Node.js（有 `npx`）。

### 安装本仓库全部 skill

```bash
npx skills add dugujun3-cloud/dugujun-ai-skills
```

### 只装某一个

```bash
npx skills add dugujun3-cloud/dugujun-ai-skills@ai-delivery-over-chat
npx skills add dugujun3-cloud/dugujun-ai-skills@retention-ltv-diagnostic-starter
npx skills add dugujun3-cloud/dugujun-ai-skills@membership-activity-roi-checker
npx skills add dugujun3-cloud/dugujun-ai-skills@user-operations-playbook
npx skills add dugujun3-cloud/dugujun-ai-skills@ai-interview-copilot
```

### 装到全局（所有项目可用）

```bash
npx skills add dugujun3-cloud/dugujun-ai-skills@ai-delivery-over-chat -g
```

### 指定 Agent

```bash
npx skills add dugujun3-cloud/dugujun-ai-skills@ai-delivery-over-chat -a claude-code
npx skills add dugujun3-cloud/dugujun-ai-skills@user-operations-playbook -a cursor
```

安装前请打开本仓库阅读对应 `SKILL.md`（第三方 skill 拥有与 Agent 相同的文件权限）。

## 触发示例

- 「我用 AI 改活动表改了一个小时更累了，帮我诊断」→ `ai-delivery-over-chat`
- 「复购掉了，先别发券，帮我查数据口径」→ `retention-ltv-diagnostic-starter`
- 「会员日 GMV 涨了，预算还要不要续」→ `membership-activity-roi-checker`
- 「用户分层打了一堆标签，群发还是一套」→ `user-operations-playbook`
- 「帮我拆解这个 JD 并准备业务二面」→ `ai-interview-copilot`

## 仓库结构

```text
dugujun-ai-skills/
├── README.md
├── LICENSE                 # 仓库默认 MIT
└── skills/
    ├── ai-delivery-over-chat/
    ├── retention-ltv-diagnostic-starter/
    ├── membership-activity-roi-checker/
    ├── user-operations-playbook/   # Apache-2.0（见 skill 内 LICENSE）
    └── ai-interview-copilot/
```

每个 skill 目录以 `SKILL.md` 为入口；可附带 `references/`、`scripts/`、`assets/`、`agents/`。

## 许可说明

- 仓库根目录与多数 skill：MIT
- `user-operations-playbook`：Apache-2.0（以该目录内 `LICENSE` / `NOTICE` 为准）

## 关于

基于卢国军使用 AI Agent 的实践经验整理。`ai-delivery-over-chat` 的来源说明见 skill 内 `references/sources.md`。
