# 生命周期与转化适配模块

本模块是对九个公开营销 Skill 任务边界的原创压缩适配，统一服从本 Playbook 的证据、增量、隐私和频控规则。它不复制上游案例、数字、模板或具体实现。

## 路由

- `onboarding`：围绕首次价值时刻设计步骤、空状态、提示和触达，不把“完成注册”当激活。
- `churn-prevention`：先区分主动流失、被动流失、低价值用户和服务失败，再决定预警、挽回或停止触达。
- `referrals`：明确推荐者、被推荐者、双边价值、增量口径、作弊风险和奖励成本。
- `emails`：把邮件视为生命周期触点；每封只承担一个状态迁移，不用发送量替代效果。
- `paywalls`：根据用户价值感知与使用阶段决定展示时机、权益差异和恢复路径，不用黑暗模式阻止退出。
- `marketing-psychology`：只作为假设生成器；稀缺、社会证明、损失厌恶等必须真实、可解释且不过度操纵。
- `ab-testing`：先写假设、主指标、护栏、随机化单位、污染风险、停止规则和样本可行性。
- `analytics`：先定义事件、实体、口径、观察窗和数据质量，再建看板；可视化不替代验证。
- `cro`：从漏斗证据定位最高价值阻力，先改一个关键环节；不同时更改多项后把结果归因给单一因素。

## 最小实验卡

```text
决策问题：
目标用户与生命周期状态：
当前障碍与证据：
假设：如果做 X，因为 Y，指标 Z 会变化：
主要指标 / 护栏 / 观察窗：
对照或反事实：
实施成本与风险：
停止、继续、放大条件：
```

## 来源与许可边界

任务范围参考 Corey Haines 的 [`coreyhaines31/marketingskills`](https://github.com/coreyhaines31/marketingskills) 中 `churn-prevention`、`referrals`、`onboarding`、`emails`、`paywalls`、`marketing-psychology`、`ab-testing`、`analytics`、`cro`，上游采用 MIT License。

本模块只保留可迁移的问题分类，并用独孤菌 Playbook 的证据、反事实、隐私、频控、责任人与停止条件重新组织。原 Skill 不再独立路由，避免与生命周期、实验和度量模块重复。完整版权与许可声明见 [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)。
