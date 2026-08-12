# 状态与恢复

## 何时建立状态

仅在任务跨多轮、包含多个阶段、等待用户决策、需要可恢复外部动作或用户明确要求续跑时建立状态。单轮问答和清晰的一步任务保持轻量。

## 推荐文件

- `work_brief.md`：当前目标、交付物、完成标准、资料范围和明确不做。
- `acceptance.md`：机器验证项、人工验收项和外部发布状态。
- `workflow_status.json`：机器可读的阶段、授权、产物和下一步。
- `handoff.md`：下一轮只需读取的简短交接。
- `skill_candidate.md`：仅在复用审计达到 `candidate` 后创建。

把这些文件放在当前业务任务的工作目录，不写入只读知识库，也不要散落到无关项目。

## `workflow_status.json` 最小结构

```json
{
  "schema_version": 1,
  "task_id": "stable-local-id",
  "status": "clarifying",
  "current_stage": "define_outcome",
  "updated_at": "ISO-8601 timestamp",
  "authorizations": [],
  "selected_inputs": [],
  "outputs": [],
  "validation": [],
  "external_effects": [],
  "reuse_maturity": "one_off",
  "next_action": "one concrete action"
}
```

`status` 只使用：`clarifying`、`ready_to_execute`、`executing`、`awaiting_user_decision`、`awaiting_acceptance`、`completed`、`blocked`。

每项授权至少记录动作、目标、范围和是否已使用。每项输出至少记录路径或交付位置、存在性验证和验收状态。每项外部影响明确记录 `not_attempted`、`attempted`、`succeeded` 或 `failed`；不要用本地准备状态代替外部成功。

## 更新顺序

1. 完成一个真实阶段后更新产物和验证证据。
2. 再更新 `workflow_status.json` 的阶段与下一步。
3. 最后更新 `handoff.md`，确保它与 JSON 一致。
4. 用户局部验收时只关闭对应阶段；没有待执行阶段时才设为 `completed`。

## 恢复顺序

1. 读取 `workflow_status.json` 和 `handoff.md`。
2. 检查下一步依赖的关键文件是否仍存在。
3. 回读最近产物或验证结果，不重新扫描全部资料。
4. 从 `next_action` 继续；若状态与事实冲突，以可验证事实为准并修正状态。
