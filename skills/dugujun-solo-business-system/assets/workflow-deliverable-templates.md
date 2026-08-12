# 一人公司全流程交付模板

按当前阶段选用，不机械填满。事实、推断、假设、未知和外部主张必须分开；数字和阈值来自用户约束、真实证据或明确实验设计。

## 项目章程

```markdown
# 项目章程
- project_id：
- 项目名称：
- 当前业务成熟度 / 工作流阶段：
- 本项目只解决的主决策：
- 用户定义的完成条件：
- 想要的生活和商业目标：
- 时间、现金、健康、家庭、声誉和合规边界：
- 最大可接受投入/损失：
- 已有能力、案例、内容、关系、渠道和产品资产：
- 不做事项：
- 知识库只读与写入目录：
- 首次复盘日期：
```

## 阶段计划与验收单

```markdown
# 阶段计划与验收
- phase：
- 进入依据：
- 本阶段唯一目标：
- 必备输入：
- 缺失和冲突：
- 必备产物及绝对路径：
- 成功信号：
- 护栏与最大损失：
- 外部动作及当前状态：
- 自检：文件 / 证据 / 边界 / 风险 / 专项质量闸门
- 验收结果：accepted / revision_required / stopped
- 验收人和时间：
- 回退阶段及原因：
- 下一步唯一动作：
```

## 证据账本

```markdown
| ID | 陈述 | 事实/推断/假设/未知/外部主张 | 来源与时间 | 样本与偏差 | 置信度 | 影响的决策 | 验证动作 | 状态 |
|---|---|---|---|---|---|---|---|---|
```

## 产物清单

```markdown
| artifact_id | phase | 类型 | 绝对路径 | 版本 | 状态 | 验收标准 | 检查 | 验收/替代记录 |
|---|---|---|---|---|---|---|---|---|
```

## 专项 Skill brief

```markdown
# Specialist Request
- request_id：
- controller_project_id：
- current_phase：
- specialist_skill：
- business_objective：
- target_customer_and_problem：
- validated_facts：
- hypotheses_to_preserve：
- input_files：
- output_directory：
- expected_artifacts：
- acceptance_criteria：
- current_data_or_web_verification_needed：
- write_boundary：
- forbidden_actions：
- external_action_policy：
- failure_fallback：
```

## 专项回传与主控收口

```markdown
# Specialist Result
- request_id：
- status：completed / partial / failed / awaiting_user / awaiting_external
- artifacts：
- checks_performed：
- evidence_added：
- assumptions_and_unknowns：
- unresolved_issues：
- user_action_needed：
- external_action_needed：
- publication_or_execution_state：
- controller_review：通过 / 补做 / 降级 / 拒绝采用
- controller_next_action：
```

## 外部动作审批单

```markdown
# External Action
- action_id：
- 类型：发布 / 发送 / 投放 / 付款 / 退款 / 购买 / 签约 / 注册 / 部署 / 权限 / 其他
- 目标对象和账号/平台：
- 使用的产物及版本：
- 动作范围：
- 风险、成本和可逆性：
- 当前状态：prepared / awaiting_approval / approved / user_reported_performed / verified / rejected / expired
- 批准人、批准时间和批准范围：
- 执行人和执行时间：
- 核验证据：
- 失败、撤回或回滚方案：
```

## 客户准入与交付卡

```markdown
# 客户准入与交付
- 匿名客户 ID：
- 纳入/排除判断及证据：
- 客户目标和当前基线：
- 产品/服务版本：
- 承诺范围与不包含：
- 客户责任：
- 付款/承诺状态及证据：
- 接触点与交付排期：
- 交付记录、工时、成本、返工和例外：
- 结果证据：
- 用户对本地产物的验收：
- 真实客户验收：
- 售后、补救、退款或退出：
- 案例授权和匿名边界：
```

## 产品化咨询规格

```markdown
# 产品化咨询规格
- 目标客户、场景和核心问题：
- 准入/拒绝条件：
- 可观察结果和不承诺结果：
- 事前材料与诊断机制：
- 服务范围、接触点和修改边界：
- 客户责任、验收和退出：
- 价格、成本、容量和有效时薪变量：
- 标准流程与例外：
- 结果证据和案例授权：
- 进入标准化或停止条件：
```

## 课程最小内测规格

```markdown
# 课程最小内测
- 目标学员、基线和不适用人群：
- 学习结果和可观察进展：
- 结果—模块—练习—反馈—验收映射：
- 最小内测范围：
- 作业、反馈、答疑和退出边界：
- 招募、付款和退款假设：
- 学习行为、完成、结果和访谈证据：
- 交付成本和维护责任：
- 下一版只调整的变量：
```

## 产品知识库规格

```markdown
# 产品知识库规格
- 产品目录与只读源知识库边界：
- 目标用户任务和检索场景：
- 信息架构、入口、标签和导航：
- 知识单元格式、来源、类型和更新时间：
- 模板、案例、快速路径和失败路径：
- 搜索/导航/套用任务测试：
- 权限、版本、更新和下架规则：
- 用户任务成功证据：
- 维护成本和负责人：
```

## Web 应用验证规格

```markdown
# Web 应用验证规格
- 高频用户任务和现有替代：
- 人工版本的结果与重复证据：
- 用户、输入、处理、输出、边界和非目标：
- 规则稳定性和主要例外：
- 数据字典、权限、隐私、安全和日志：
- 原型与可用性测试：
- 核心路径验收、失败保底和人工回退：
- MVP 功能和明确不做功能：
- 开发、维护、支持和部署成本：
- 使用、付费、留存和停止假设：
- 公开部署审批与核验：
```

## 实验复盘与阶段决策

```markdown
# 实验复盘
- 原决策、关键假设和当时证据：
- 预期信号、护栏、最大损失和停止条件：
- 实际执行与外部动作核验：
- 结果、工时、成本、退款、客户反馈和生活影响：
- 事实 / 解释 / 新假设：
- 支持或推翻了什么：
- 决策：iterate / stop / scale
- 回退阶段或下一阶段：
- 下一轮只调整的一个变量：
- 沉淀的案例、模板、SOP、客户语言或产品资产：
- 状态、handoff 和产物清单是否已更新：
```

## 暂停/停止交接

```markdown
# 暂停或停止交接
- 类型：paused / stopped
- 原因和证据：
- 当前阶段与最后完成动作：
- 已验收产物：
- 未完成产物和待输入：
- 外部动作状态及需撤回/履行事项：
- 客户通知、退款、售后或合同责任：
- 已投入资源和可复用资产：
- 恢复条件或永久停止依据：
- 下一次检查日期：
```
