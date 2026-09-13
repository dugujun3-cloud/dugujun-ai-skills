# dugujun-ai-skills

[![Validate public skills](https://github.com/dugujun3-cloud/dugujun-ai-skills/actions/workflows/validate.yml/badge.svg)](https://github.com/dugujun3-cloud/dugujun-ai-skills/actions/workflows/validate.yml)

独孤菌公开的可安装 AI 工作系统与 Agent Skills，覆盖用户运营、一人公司、AI 交付、面试、内容账号分析和知识工具。

这里是**公开发布仓库**，不是本地 Agent 工作区的镜像。仓库只接收权利清楚、已脱敏、可验证的 Skill、必要许可证和合成样例；不接收知识库、真实用户数据、账号信息、文章素材、图片、视频、日志、状态或备份。

## 快速选择

| Skill | 成熟度 | 适合解决什么 | 公开真源状态 |
| --- | --- | --- | --- |
| [user-operations-playbook](skills/user-operations-playbook/) | Stable | 用户全生命周期、增长、留存、会员、CRM 和客户成功 | 已对齐 |
| [ai-work-bootstrap](skills/ai-work-bootstrap/) | Stable | 把模糊、拖延的工作推进为可验收任务 | 已对齐 |
| [ai-interview-copilot](skills/ai-interview-copilot/) | Stable | 证据驱动的面试准备、模拟和复盘 | 已对齐 |
| [retention-ltv-diagnostic-starter](skills/retention-ltv-diagnostic-starter/) | Stable | 复购、留存、观察窗口价值与实验诊断 | 构建审计 |
| [membership-activity-roi-checker](skills/membership-activity-roi-checker/) | Stable | 会员活动增量 ROI 与预算决策 | 已对齐 |
| [ai-delivery-over-chat](skills/ai-delivery-over-chat/) | Stable | 把“陪聊式 AI”推进成可交付闭环 | 已对齐 |
| [dugujun-account-analysis](skills/dugujun-account-analysis/) | Beta | 内容账号数据分析、归因和实验计划 | 已对齐 |
| [dugujun-solo-business-system](skills/dugujun-solo-business-system/) | Beta | 一人公司定位、验证、交付、定价和获客 | 待同步审计 |
| [getnote-blogger-batch-import](skills/getnote-blogger-batch-import/) | Beta | 得到大脑博主内容的可恢复批量导入 | 待同步审计 |
| [expertise-to-tool](skills/expertise-to-tool/) | Beta | 把领域判断共创成单文件 HTML 工具 | 真源待恢复 |
| [diagnostic-product-builder](skills/diagnostic-product-builder/) | Beta | 把方法做成自测、校准和手册三层产品 | 真源待恢复 |

完整机器可读状态见 [`skills-manifest.json`](skills-manifest.json)。

### 成熟度

- **Stable**：已有公开包和清晰边界，可正常安装；后续更新仍需通过 CI 和发布审计。
- **Beta**：可以试用，但依赖、公开真源或跨环境行为仍需继续验证。

成熟度不是效果承诺。真实结果仍取决于输入质量、业务条件、权限和数据口径。

## 安装

需要本机安装 Node.js，并能运行 `npx`。

### 查看并安装全部 Skill

```bash
npx skills add dugujun3-cloud/dugujun-ai-skills
```

### 安装单个 Skill

```bash
npx skills add dugujun3-cloud/dugujun-ai-skills@user-operations-playbook
npx skills add dugujun3-cloud/dugujun-ai-skills@ai-work-bootstrap
npx skills add dugujun3-cloud/dugujun-ai-skills@ai-interview-copilot
```

如需全局安装或指定宿主，请使用 `skills` CLI 支持的 `-g` / `-a` 参数。不同 Agent 对 Skills 的发现、权限和工具支持可能不同，安装成功不等于所有外部依赖已经配置。

安装前请阅读对应的 `SKILL.md`。第三方 Skill 在运行时可能获得与 Agent 相同的文件、命令或浏览器权限。

### 可选环境变量

| 变量 | 用途 |
| --- | --- |
| `DUGUJUN_KNOWLEDGE_BASE_ROOT` | 账号分析与一人公司 Skill 可选的只读知识库根目录 |
| `GETNOTE_CLI` | `getnote` 可执行路径；未设置时从 PATH 查找 |

## 可信发布边界

每次 Pull Request 自动检查：

- Skill 目录与 Manifest 一一对应。
- `SKILL.md` 的 name 与目录一致，description 非空。
- JSON、Python 语法和仓库内 Markdown 链接有效。
- 不包含缓存、ZIP、日志、符号链接、本机绝对路径或常见密钥模式。
- 单文件和仓库总体积保持在公开 Skill 的合理范围内。

自动检查只能验证机器可观察项，不能替代版权、事实、专业风险和真实任务验收。

## 维护流程

公开更新遵循：本地真源 → 公开适配/脱敏 → 机器校验 → 权利审查 → Pull Request → CI → 人工验收 → 合并 → Tag/Release。

目前没有 Release 的 Skill 不应被解读为已有稳定版本号。版本和变更记录从 [`CHANGELOG.md`](CHANGELOG.md) 开始维护。

## 仓库结构

```text
dugujun-ai-skills/
├── skills/                    公开运行包
├── skills-manifest.json      成熟度、许可证和真源状态
├── scripts/validate_repo.py  无外部依赖的发布检查
├── tests/                    仓库验证测试
├── .github/workflows/        GitHub Actions
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
└── LICENSE
```

## 许可

- 仓库根目录与多数 Skill：MIT。
- `user-operations-playbook`：Apache-2.0，以该目录内 `LICENSE` / `NOTICE` 为准。
- 个别 Skill 有自己的 LICENSE、NOTICE、PRIVACY 或 LIMITATIONS 时，以该目录文件为准。

许可证只覆盖仓库中实际包含、且有权公开的原创代码和文档，不覆盖未包含的第三方材料或用户数据。

## 反馈与安全

- 使用问题和功能建议：使用 GitHub Issues。
- 贡献公开 Skill：先阅读 [`CONTRIBUTING.md`](CONTRIBUTING.md)。
- 涉及隐私、密钥或可利用漏洞：阅读 [`SECURITY.md`](SECURITY.md)，不要把敏感细节发到公开 Issue。
