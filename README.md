# dugujun-ai-skills

卢国军公开的 Agent Skills。基于使用 AI Agent 的实践经验整理，可安装到 Claude Code、Cursor、Codex、Grok 等支持 [Agent Skills](https://skills.sh/) 的工具。

部分 skill 同步用于小红书创作服务平台（Red Skill）公开领取。

## 包含的 skill

### 运营 / 商业

| Skill | 作用 |
|-------|------|
| **user-operations-playbook** | 用户运营全域诊断与设计（17 个高频领域） |
| **retention-ltv-diagnostic-starter** | 复购/留存与观察窗口用户价值诊断 |
| **membership-activity-roi-checker** | 会员活动增量 ROI 体检与预算决策卡 |
| **dugujun-account-analysis** | 内容账号（小红书/抖音/B站/知乎）数据分析与实验计划 |
| **dugujun-solo-business-system** | 一人公司端到端主控：定位→验证→交付→定价→获客→产品化 |

### AI 用法 / 工作流

| Skill | 作用 |
|-------|------|
| **ai-delivery-over-chat** | 诊断「用 AI 越用越累」：从陪聊推进到能交 |
| **ai-work-bootstrap** | 把模糊、拖延的工作烦恼推进为可验收的真实任务 |
| **ai-interview-copilot** | 证据驱动的面试准备、模拟与复盘 |

### 工具

| Skill | 作用 |
|-------|------|
| **getnote-blogger-batch-import** | 得到大脑博主内容批量导出为 Markdown / ZIP |
| **expertise-to-tool** | 把领域专家的方法论共创成单文件 HTML 工具：逐题深问对焦 + 规则库提炼 + 分支问卷规则引擎 + surge 上线 |

## 安装

需要本机已装 Node.js（有 `npx`）。

### 全部安装

```bash
npx skills add dugujun3-cloud/dugujun-ai-skills
```

### 单装示例

```bash
npx skills add dugujun3-cloud/dugujun-ai-skills@ai-delivery-over-chat
npx skills add dugujun3-cloud/dugujun-ai-skills@user-operations-playbook
npx skills add dugujun3-cloud/dugujun-ai-skills@dugujun-solo-business-system
npx skills add dugujun3-cloud/dugujun-ai-skills@ai-work-bootstrap
```

### 全局 / 指定 Agent

```bash
npx skills add dugujun3-cloud/dugujun-ai-skills@ai-delivery-over-chat -g
npx skills add dugujun3-cloud/dugujun-ai-skills@user-operations-playbook -a claude-code
```

安装前请阅读对应 `SKILL.md`（第三方 skill 拥有与 Agent 相同的文件权限）。

## 可选环境变量

| 变量 | 用途 |
|------|------|
| `DUGUJUN_KNOWLEDGE_BASE_ROOT` | 可选只读知识库根目录（账号分析 / 一人公司主控防写回） |
| `GETNOTE_CLI` | `getnote` 可执行路径，默认从 PATH 找 `getnote` |

## 仓库结构

```text
dugujun-ai-skills/
├── README.md
├── LICENSE
└── skills/
    ├── ai-delivery-over-chat/
    ├── ai-work-bootstrap/
    ├── ai-interview-copilot/
    ├── retention-ltv-diagnostic-starter/
    ├── membership-activity-roi-checker/
    ├── user-operations-playbook/
    ├── dugujun-account-analysis/
    ├── dugujun-solo-business-system/
    ├── getnote-blogger-batch-import/
    └── expertise-to-tool/
```

## 许可说明

- 仓库根目录与多数 skill：MIT
- `user-operations-playbook`：Apache-2.0（以该目录内 `LICENSE` / `NOTICE` 为准）

## 关于

基于卢国军使用 AI Agent 的实践经验整理。
