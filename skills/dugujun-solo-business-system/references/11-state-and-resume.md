# 项目状态、恢复与验收协议

## 状态源

每个运行项目必须有独立目录。建议结构：

```text
一人公司项目/{project_slug}/
├── workflow_status.json
├── handoff.md
├── events.jsonl
├── 00_scope_constraints/
├── 10_positioning/
├── ...
└── 90_scale_transition_review/
```

`workflow_status.json` 是续跑状态的唯一事实源；`handoff.md` 是从状态和已验收产物提炼的人类可读交接。两者冲突时，先核查产物和日志，再修复状态，不根据 handoff 静默覆盖 JSON。

不得把运行状态写入只读知识库。原知识库只作为来源，项目产物默认写当前工作区。

本协议只属于独立命名空间 `dugujun.solo_business.v1`，项目根固定为当前工作区的 `一人公司项目/`。恢复前同时校验 `workflow_namespace`、`workflow_type=solo_business_end_to_end`、`workflow_id=sbw_*` 和 `project.root`；任何一项不匹配，都按其他工作流状态拒绝处理。不得扫描或复用公众号、小红书、知乎、文章分发、用户运营和软件开发目录里的同名 `workflow_status.json`。

## 最小状态模型

```json
{
  "schema_version": "2.0",
  "workflow_namespace": "dugujun.solo_business.v1",
  "workflow_id": "sbw_0123456789ab",
  "workflow_type": "solo_business_end_to_end",
  "revision": 3,
  "cycle": 1,
  "project": {"name": "项目名", "root": "绝对路径", "goal": "本轮目标"},
  "guardrails": {"knowledge_base_read_only": true, "no_external_writes": true},
  "overall_status": "active",
  "current_stage": "20_customer_evidence",
  "stages": {"20_customer_evidence": {"status": "in_progress", "artifacts": []}},
  "event_log": {"path": "events.jsonl", "last_seq": 3},
  "handoff": {"path": "handoff.md", "generated_from_revision": 3},
  "external_actions": [],
  "next_actions": ["下一步唯一动作"],
  "updated_at": "ISO-8601 timestamp"
}
```

完整字段、枚举和约束以 `assets/workflow-status.schema.json` 为准；不要根据上面的缩略示例手写状态。

业务成熟度只使用：`idea / validation / first_sales / delivery / systemization / transition / expansion`，并记录在阶段业务产物中。控制器的 `current_stage` 只使用：`00_scope_constraints / 10_positioning / 20_customer_evidence / 30_offer_mvp / 40_market_validation / 50_pilot_delivery / 60_pricing_economics / 70_acquisition_trust / 80_systemization_productization / 90_scale_transition_review`。不得创建 P0、P1 等同义阶段，也不得因为生成文件自动提升业务成熟度。

## 状态值

整体状态只使用：`active / awaiting_acceptance / blocked / paused / completed / stopped / recovery_needed`。

单阶段状态只使用：`pending / in_progress / awaiting_acceptance / accepted / blocked / paused / stopped`。缺用户输入或外部结果时，用 `block` 登记 `owner`、原因、恢复条件、保底路径和证据，不另造 `awaiting_user`、`awaiting_external` 等运行时状态。需要修改时保持当前阶段 `in_progress`，产物继续为 `draft`，通过 `next` 重新送审。

## 产物登记

每个产物至少记录：

```text
artifact_id｜phase｜type｜absolute_path｜version｜status
｜acceptance_criteria｜checks｜accepted_by｜accepted_at｜supersedes
```

控制器产物状态只使用：`missing / draft / ready / accepted`。已验收版本不得被静默覆盖；修改时先保留旧版本或变更记录，控制器会用哈希把静默变化识别为漂移。

## “启动”语义

收到“启动、开始做、把这个经验做成产品”等指令时：

1. 先检查工作区是否存在同主题未结束项目。
2. 能唯一匹配时提示将恢复还是新建立项；用户明确新项目时创建新的 `workflow_id`。
3. 不存在项目时创建 `00_scope_constraints` 必备状态和章程，不先生成完整课程、知识库或 Web 应用。
4. 将可发现的已有资产登记为来源，不复制或修改只读知识库。

## “继续”语义

收到“继续、接着做、上次做到哪”等指令时：

1. 查找最近相关、未 `completed/stopped` 的项目。
2. 读取 `workflow_status.json`、`handoff.md`、当前阶段已验收产物和待办。
3. 核验 JSON 可解析、产物路径存在、状态与验收记录一致。
4. 从 `next_actions` 和未通过的当前闸门继续，不重新做完整诊断，不覆盖已验收产物。
5. 如果有多个候选项目且无法唯一判断，最多询问一个项目选择问题。
6. 状态损坏时根据产物和日志重建最小状态，明确标注修复依据和无法恢复的信息。

## “验收”语义

必须区分：

- **产物验收**：用户明确说“Offer 验收、封面验收、方案验收”等，只记录该产物已通过；只有当前阶段全部必备产物就绪时才运行控制器 `accept`。
- **阶段验收**：用户只说“验收、可以、验收成功”时，默认验收当前阶段；检查必备产物后更新阶段状态。
- **总体验收**：当前阶段已通过且没有待执行阶段时，将项目标记为 `completed`。
- **客户验收**：真实客户对交付结果的确认，单独记录，不能由用户对 Codex 文件的验收替代。
- **发布验收**：内容草稿验收与平台实际发布分开；草稿通过不代表已发布。

验收前执行阶段自检：必备文件存在、关键字段完整、事实与假设分开、外部动作状态真实、没有写入只读知识库。验收失败时保持当前阶段可修改，不运行 `accept`；记录原因、责任人和下一版标准，修改后重新运行 `next` 送审。

## “修改”与回退语义

用户要求修改已验收内容时：

1. 判断修改是否只影响局部产物，还是推翻了上游假设。
2. 局部修改先保留旧版本或变更记录，再重新自检和送审。
3. 上游假设变化时，停止并归档当前周期，再用 `new-cycle --from-stage` 从最早受影响阶段重开；不要手工改控制器状态。
4. 不因为一次措辞修改重跑整个项目；也不在核心客户、问题或承诺改变后继续沿用旧成交/交付证据。

## “暂停”语义

收到“暂停、先放一下”时：

- 设置 `overall_status=paused`。
- 保存当前阶段、最后完成动作、未完成产物、待输入、外部等待和下一步。
- 生成或更新 handoff；不触发下一阶段，不执行外部动作。
- 恢复后先核验时效性主张、平台规则、价格、法律和未完成批准是否仍有效。

## “停止”语义

收到“停止、放弃这个项目”或满足预设止损条件时：

- 区分用户主动停止、证据性停止和风险性停止。
- 保存停止依据、已投入资源、外部承诺、需履行的退款/通知/售后和可复用资产。
- 将未执行外部动作取消或标记失效；已执行动作不能伪装成可回滚。
- 设置 `overall_status=stopped`，不得自动新建相似项目绕过停止决定。

## 外部动作状态机

任何发布、发送、投放、付款、退款、购买、签约、注册、部署公开服务、权限变更或不可逆动作，都使用：

```text
prepared → awaiting_approval → approved → user_reported_performed → verified
                 └────────────→ rejected / expired
```

- `prepared`：只完成草稿、材料或执行计划。
- `awaiting_approval`：已准备好，但等待用户针对具体目标批准。
- `approved`：用户批准了明确对象、范围和动作；批准不能泛化到其他对象或以后版本。
- `user_reported_performed`：用户或获授权的人报告已实际执行，记录时间、目标、执行者和证据；这仍不等于结果已核验。
- `verified`：通过回执、页面、付款记录、平台状态或用户证据核验结果。
- `rejected/expired`：拒绝或因版本、时间、目标变化失效。

不得从 `prepared` 直接写成 `user_reported_performed`，不得把 `approved` 写成已经发布/付款/成交。等待外部动作时，用 `block --owner external_state` 保存恢复条件；不依赖该结果的本地工作可以先完成，但不得越过阶段闸门。

## handoff 最小内容

```markdown
# 项目交接
- 项目与当前状态：
- 当前业务成熟度 / 工作流阶段：
- 已验收产物：
- 当前唯一假设与闸门：
- 等待用户 / 外部证据 / 批准：
- 已准备但未执行的外部动作：
- 主要风险和失效信息：
- 下一步唯一动作：
- 最近一次状态更新时间：
```

## 幂等与恢复检查

- 重复“继续”不得重复创建项目或复制产物。
- 重复“验收”不得推进两个阶段。
- 重复专项请求优先复用已返回且输入未变化的产物。
- 已失效批准、旧平台规则和旧价格信息不能在恢复后继续使用。
- 删除、移动或覆盖关键文件前必须获得明确授权，并保留恢复方案。
