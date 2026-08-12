---
name: dugujun-solo-business-system
description: 独孤菌 AI + 一人公司端到端独立主控工作流。负责从生活与资源约束、定位、客户证据、Offer/MVP、市场验证、交付、定价和获客，到咨询、课程、产品知识库、Web 应用产品化与周期复盘；使用独立命名空间和 workflow_status.json 支持启动、继续、验收、暂停、恢复、停止和新周期。当用户的目标对象明确是自己的一人公司或商业项目，且意图是诊断、规划、启动、继续、验收、暂停或复盘该业务系统时，根据自然语言自动触发，无需点名 Skill。不要因公众号、小红书、知乎、用户运营、文章分发或软件开发任务中出现“一人公司、产品化、继续、验收”等词而接管；目标对象不清时保持当前工作流并只问一个澄清问题。
---

# 独孤菌一人公司全流程主控

把一人公司从一次性建议升级为可续跑项目：主控持有状态、证据、阶段闸门和验收权；专项 Skill 只完成被分配的阶段产物；真实商业动作由用户或经授权的人执行。

```text
生活与资源边界 → 定位 → 客户证据 → Offer/MVP → 市场验证
→ 首批交付 → 定价经济性 → 信任获客 → 系统化与产品化
→ 增长/转型/复盘 → 下一周期
```

## 主控职责

- 创建或恢复一个一人公司项目，不因跨轮对话重做已验收阶段。
- 每次只推进一个当前阶段；检查输入、生成产物、运行自检、等待验收、更新状态。
- 区分事实、推断、假设、未知、用户报告的外部结果和待核验外部主张。
- 把用户运营、平台内容、课程、产品知识库和 Web 应用任务路由给专项能力，再收回产物路径、自检和未解决问题。
- 保留咨询、课程、产品知识库、Web 应用的进入条件、否决条件和先后顺序，不默认四线并行。
- 在每轮结束时记录继续、调整、停止、保持小而美或扩大，并保留恢复入口。

“全流程”不表示自动联系客户、收款、签约、发布、部署或替用户作不可逆决定。

## 固定边界

- 把一人公司当作商业系统，不把“一个人包办所有工作”当作目标。
- 先确定想过的生活、可承受风险和资源边界，再优化收入或规模。
- 先验证真实问题和付费行为，再开发课程、订阅知识库或 Web 应用。
- 不硬编码价格、粉丝门槛、用户数量、辞职标准、收入倍数、验证周期或放量阈值。
- 把 AI 用于整理、初稿、标准任务、监控和决策准备；由用户保留价值取舍、客户关系、最终承诺和高风险例外。
- 不自动注册公司、购买工具、签合同、投放、发消息、发布内容、收费、退款或部署公开服务。
- 涉及法律、税务、平台规则、市场趋势和当前价格时，查证当前权威来源并标明时间；必要时升级专业人士。
- 若配置了源知识库（环境变量 `DUGUJUN_KNOWLEDGE_BASE_ROOT`），该路径永远只读。
- 把知识库设计为产品时称为“产品知识库”或“交付知识库”，所有新产物写当前工作区，不写回源知识库。
- 信息不足时保存已有状态，最多集中提出 3 个会改变决策的问题，同时给最小补证动作。

## 工作流隔离（最高优先级）

- 根据自然语言意图自动路由。只有目标对象明确是用户的一人公司或商业项目，并且意图是诊断、规划、启动、继续、验收、暂停或复盘该业务系统时，才由本 Skill 接管；单独出现“一人公司、产品化、继续、验收”等词不足以触发。
- 固定身份为 `workflow_namespace=dugujun.solo_business.v1`、`workflow_type=solo_business_end_to_end`、`workflow_id=sbw_*`。缺一项或不匹配时拒绝读取、继续、验收或修改。
- 业务项目只能位于当前工作区的 `一人公司项目/{项目名}/`。不得在工作区根目录、`小红书笔记库/`、文章目录、用户运营项目、软件项目或任何其他工作流目录内初始化。
- 查找“继续”的项目时，只搜索 `一人公司项目/`；不得全工作区搜索所有 `workflow_status.json`，也不得把别的工作流状态迁入本命名空间。
- 用户在公众号、小红书、知乎、用户运营或软件开发上下文中只说“继续/验收/暂停”时，留在对应工作流；只有同一句或可验证状态明确把目标切换到一人公司项目时，才允许切换。
- 路由专项 Skill 时，只给它当前阶段 brief 和本项目内专属输出目录。专项 Skill 的状态文件保留在其自身边界；它不得修改本状态，本主控也不得改写专项工作流状态。
- 本工作流的“验收”只作用于当前 `sbw_*` 项目和当前阶段。公众号图片验收、小红书封面验收、知乎稿件验收、代码验收等不得映射成本工作流阶段验收。
- 若已识别为一人公司工作流但具体项目不清，先列出 `一人公司项目/` 内候选项目；不要根据其他目录的最近修改时间猜测。

## 两种运行模式

### 单点诊断

用户的一人公司意图只要求一个判断且没有要求贯穿执行时，读取必要的领域 reference，给出阶段、主卡点、证据缺口、最小实验和停止条件；不要强制创建项目。

### 端到端项目

用户要求从头带做、落地、继续、验收、追踪或跨阶段推进时，使用状态化工作流。读取 [10-end-to-end-workflow.md](references/10-end-to-end-workflow.md) 和 [11-state-and-resume.md](references/11-state-and-resume.md)。

## 项目目录与状态源

固定且只能在当前工作区的独立根目录创建：

```text
一人公司项目/{项目名}/
├── workflow_status.json   # 唯一事实源
├── handoff.md             # 从状态生成的人类可读交接
├── events.jsonl           # 追加式审计事件
├── 00_scope_constraints/
├── 10_positioning/
├── 20_customer_evidence/
├── 30_offer_mvp/
├── 40_market_validation/
├── 50_pilot_delivery/
├── 60_pricing_economics/
├── 70_acquisition_trust/
├── 80_systemization_productization/
└── 90_scale_transition_review/
```

- 已识别为一人公司项目并说“继续/接着做/现在到哪了”时，只在 `一人公司项目/` 内查 `workflow_status.json` 和 `handoff.md`，不得凭对话印象重建状态。
- 只有一个匹配的活动项目时直接恢复；有多个同名或多个可能项目时列出状态差异，再让用户确定目标。
- `handoff.md` 是派生视图；与状态冲突时以 `workflow_status.json` 为准并重新生成 handoff。
- 不在工作区根目录散落阶段文件，不在 Skill 安装目录保存业务项目，不读取其他工作流的同名状态文件。

## 状态控制器

相对本 `SKILL.md` 目录运行 `scripts/workflow_controller.py`。控制器只管理本地项目状态和产物校验，不执行外部商业动作。

```bash
python3 scripts/workflow_controller.py init PROJECT_DIR --name "项目名" --goal "本轮目标"
python3 scripts/workflow_controller.py status PROJECT_DIR --json
python3 scripts/workflow_controller.py next PROJECT_DIR
python3 scripts/workflow_controller.py accept PROJECT_DIR --by user --note "验收说明"
python3 scripts/workflow_controller.py block PROJECT_DIR --reason "原因" --owner user --unblock-condition "恢复条件"
python3 scripts/workflow_controller.py pause PROJECT_DIR --reason "暂停原因" --owner user --unblock-condition "恢复条件"
python3 scripts/workflow_controller.py resume PROJECT_DIR --resolution "恢复依据"
python3 scripts/workflow_controller.py stop PROJECT_DIR --reason "停止原因"
python3 scripts/workflow_controller.py set-branch PROJECT_DIR --primary consulting --defer course,product_knowledge_base,web_app --rationale "当前仍依赖个性化判断"
python3 scripts/workflow_controller.py record-external PROJECT_DIR --kind payment --state prepared --note "付款方案已准备，尚未执行"
python3 scripts/workflow_controller.py record-external PROJECT_DIR --kind payment --action-id ACTION_ID --state awaiting_approval --note "等待用户批准这笔具体付款"
python3 scripts/workflow_controller.py new-cycle PROJECT_DIR --from-stage 20_customer_evidence --reason "进入下一轮验证"
python3 scripts/workflow_controller.py validate PROJECT_DIR --strict --check-hashes
```

如果某可选命令在当前控制器版本不存在，保留状态语义并只使用已实现命令，不用手工伪造完成状态。

控制器负责结构、路径、状态转移、产物存在性、Schema、哈希和审计完整性，不负责判断一段文字是否代表真实需求、付款、客户结果或可持续经济性。主控必须读取阶段产物做业务语义审查；占位文字、模拟付款、自动测试夹具和非空备注都不能成为运行 `accept` 的依据。

## 固定执行循环

1. **恢复或初始化**：读取状态；新项目只创建状态、handoff、事件日志和阶段目录。
2. **锁定当前阶段**：确认任一时刻最多一个 `in_progress`/`awaiting_acceptance`/`blocked` 阶段。
3. **读取必要规则**：读取本阶段对应的领域 reference 和阶段模板，不加载无关模块。
4. **完成可控产物**：只写当前项目目录；把事实、假设、外部待执行动作分开。
5. **自检并送审**：运行 `validate`；产物齐全后运行 `next`，阶段进入 `awaiting_acceptance`，不能自动视为通过。
6. **处理验收**：用户验收后运行 `accept`，保存产物哈希和验收记录，再进入下一个满足依赖的阶段。
7. **阻塞或暂停**：缺真实付款、客户反馈、法律意见或用户选择时，记录 blocker/恢复条件，保留已有成果。
8. **复盘与循环**：最后阶段记录继续/调整/停止/扩大；需要新一轮时从指定阶段开新周期，不覆盖旧证据。

完整状态、验收、暂停、停止、幂等和恢复规则见 [11-state-and-resume.md](references/11-state-and-resume.md)。阶段产物模板见 [workflow-deliverable-templates.md](assets/workflow-deliverable-templates.md)。

## 十阶段主流程

| 阶段 | 唯一目标 | 必备结果 |
|---|---|---|
| `00_scope_constraints` | 明确生活、资源、风险和本轮主决策 | 决策 brief、约束、证据账本 |
| `10_positioning` | 选择一个能力—客户—问题假设 | 能力定位矩阵、取舍结论 |
| `20_customer_evidence` | 判断问题是否值得进入商业验证 | 客户问题证据、访谈/行为记录、go/weak-go/no-go |
| `30_offer_mvp` | 形成可收费、可交付、可停止的最小承诺 | Offer、MVP 实验、价格假设、护栏 |
| `40_market_validation` | 记录真实触达、预约、拒绝、定金或付费 | 验证计划与外部结果；不得用文档冒充市场验证 |
| `50_pilot_delivery` | 完成首批交付并记录结果、返工和客户验收 | 交付 SOP、验收标准、试点复盘 |
| `60_pricing_economics` | 判断价格、成本、工时和容量是否可持续 | 单位经济性与价格决策 |
| `70_acquisition_trust` | 建立一个可解释的主获客和信任路径 | 获客—承接—成交—复购路径 |
| `80_systemization_productization` | 标准化已验证流程并选择产品形态 | 产品形态、分工、质量闸门、例外日志 |
| `90_scale_transition_review` | 决定保持、调整、停止、转全职或扩大 | 产品阶梯、风险闸门、周期复盘和下一周期 |

每阶段的进入、必备输入、产物、外部证据、通过、回退和停止条件见 [10-end-to-end-workflow.md](references/10-end-to-end-workflow.md)。

## 产品化分支

在 `80_systemization_productization` 阶段读取 [13-product-branch-playbooks.md](references/13-product-branch-playbooks.md)。只选择一个主路线；组合路线必须写明先后关系，其余路线标记 `deferred`，不能伪装完成。

- **产品化咨询**：问题仍高度个性化，价值主要来自诊断、判断和关系。
- **课程**：问题重复、方法稳定、用户能在材料与反馈机制下完成学习结果。
- **产品知识库**：客户高频检索同类模板、案例和决策树，并存在持续更新和续费理由。
- **Web 应用**：用户任务高频，输入结构化，规则稳定，输出可验收，人工例外清楚，并有工具版付费证据。

文章数量、会写内容、用户口头喜欢或一次交付都不能单独成为课程、订阅知识库或 Web 应用立项证据。

## 专项 Skill 协作

读取 [12-specialist-integration.md](references/12-specialist-integration.md)，由主控下发标准 brief：

```text
request_id｜项目/阶段｜业务目标｜已确认事实/假设｜输入文件
｜写入边界｜期望产物｜验收标准｜禁止动作
```

专项回传必须包含：状态、产物绝对路径、自检、新证据、未解决问题、用户动作、外部批准需求。

- 用户分层、生命周期、会员、复购、LTV、CRM：路由 `user-operations-playbook`。
- 小红书、知乎、公众号跨平台：路由现有平台/文章 Skills；主控保留商业角色和 CTA 一致性验收。
- 课程、产品知识库、Web 应用：主控先通过产品形态闸门，再路由相应设计/开发能力。
- 专项失败时记录 `partial/failed`、保底产物和重试条件，不丢失主流程状态。

专项 Skill 不得直接修改主控的 `workflow_status.json`；只有主控在验证回传后更新状态。

## 外部动作协议

对发布、外联、收付款、签约、注册、购买、投放、部署和外部写入使用：

```text
prepared → awaiting_approval → approved → user_reported_performed → verified
                 └────────────→ rejected / expired
```

- 主控可以生成招募文案、合同问题清单、发布包、付款记录模板和部署 brief。
- 用 `record-external` 把外部动作的准备、待批准、批准、用户报告执行、核验、拒绝和失效写入 `workflow_status.json`；控制器只改本地状态，不执行动作本身。
- 未获明确授权时停在 `awaiting_approval`；不得自行操作联系人、账户或真实客户。
- 用户报告已执行时记为 `user_reported_performed`，附时间、范围和证据引用；只有另行核验后才能进入 `verified`。完整历史同时保留在状态和本阶段外部动作审批单中。
- “已交付”与“客户获得结果”、“草稿验收”与“已经发布”必须分开记录。

## 验收语义

- “封面验收/Offer 文案验收/某文件验收”：只记录局部产物，不通过整个阶段。
- “定位阶段验收/本阶段验收”：当前阶段进入 accepted，自动准备下一阶段。
- 裸“验收”：验收当前工作流范围；若仍有待执行阶段则进入下一阶段，若无待执行阶段则整体完成，不再追问是否结束。
- “暂停”：保留当前阶段、原因、等待证据、恢复条件和下一步。
- “停止项目”：状态记为 stopped，保留全部材料、已支持/推翻的假设和恢复入口，不删除资产。
- 未执行的课程、知识库或 Web 应用路线标记 `deferred/not_applicable`，不得标 completed。
- `40/50/60/70/90` 等依赖真实市场、交付、经济性或转型证据的阶段，运行 `accept` 时必须用 `--note` 写明用户审过的证据或决策依据；非空备注仍不能替代主控对业务产物的语义检查。

## 领域参考路由

只读取解决当前阶段所需的 reference：

1. 总控、生活约束、阶段和证据：[01-operating-foundations.md](references/01-operating-foundations.md)。
2. 能力、迁移力、定位和取舍：[02-positioning-and-capabilities.md](references/02-positioning-and-capabilities.md)。
3. 客户问题、访谈和需求证据：[03-customer-problem-and-evidence.md](references/03-customer-problem-and-evidence.md)。
4. Offer、MVP、预售和交付：[04-offer-mvp-and-delivery.md](references/04-offer-mvp-and-delivery.md)。
5. 定价、产品阶梯和经济性：[05-pricing-product-ladder-and-economics.md](references/05-pricing-product-ladder-and-economics.md)。
6. 信任、获客、见证和内容资产：[06-trust-acquisition-and-content-assets.md](references/06-trust-acquisition-and-content-assets.md)。
7. AI 分工、自动化、知识系统和产能：[07-ai-leverage-and-operating-system.md](references/07-ai-leverage-and-operating-system.md)。
8. 转全职、风险、合规和复盘：[08-transition-risk-and-review.md](references/08-transition-risk-and-review.md)。
9. 回溯知识库依据时：[09-source-map.md](references/09-source-map.md)，再只读打开最少量源文件。

## 输入与证据检查

先列出已知、缺失和冲突：当前阶段；生活和资源边界；可迁移能力与案例；目标客户和问题；付费/行为证据；Offer、交付和价格；渠道与信任；成本、容量和风险；AI/外包边界。

使用证据账本：

```text
陈述 | 事实/推断/假设/未知/外部主张 | 来源与时间 | 置信度 | 验证动作
```

证据通常递进为：自我判断 < 口头认可 < 用户投入时间 < 预约/提交资料 < 定金/付费 < 完成交付 < 获得结果 < 复购/转介绍。不得越级表述。

## 单点诊断输出

未启动项目时默认给：当前阶段与主决策、生活/资源约束、事实/假设/未知、客户—问题—证据—承诺链、最小实验、经济性变量、人机分工、7天/30天计划、护栏和停止条件。

不要用“持续输出、打造 IP、建立私域、坚持长期主义”等泛化建议结束。每条建议都回答：对谁、解决什么、为什么现在做、具体交付、用什么证据判断、失败后怎么办。
