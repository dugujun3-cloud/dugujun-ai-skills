#!/usr/bin/env python3
"""Create a private-by-default interview preparation workspace."""

from __future__ import annotations

import argparse
from pathlib import Path


FILES = {
    "00-input-and-truth-ledger.md": "# 输入与事实底稿\n\n## 已获得材料\n\n## 缺失材料\n\n## 事实时间线\n\n| 时间 | 事实 | 状态：已确认/待确认/不可公开 | 来源 |\n| --- | --- | --- | --- |\n",
    "01-job-deconstruction.md": "# 岗位拆解\n\n## 招聘方真正要解决的3—5个问题\n\n## 业务链路与核心指标\n\n## 明示要求与隐性要求\n\n## 匹配矩阵\n\n| 岗位要求 | 真实证据 | 缺失证据 | 补救方式 |\n| --- | --- | --- | --- |\n",
    "02-project-evidence-cards.md": "# 项目证据卡\n\n## 项目一\n\n| 字段 | 内容 |\n| --- | --- |\n| 业务基线与目标来源 | |\n| 指标口径与周期 | |\n| 本人职责边界 | |\n| 核心判断与取舍 | |\n| 动作与资源依赖 | |\n| 结果、归因与复验 | |\n| 负面结果与公开边界 | |\n",
    "03-hard-gates-and-risk-map.md": "# 硬门槛与风险地图\n\n## 硬门槛\n\n| 要求 | 已证明/相邻能力/不具备 | 证据 | 淘汰风险 | 诚实应答 |\n| --- | --- | --- | --- | --- |\n\n## 风险叙事\n\n| 风险点 | 招聘方担心什么 | 事实时间线 | 三层追问 | 回答边界 |\n| --- | --- | --- | --- | --- |\n",
    "04-question-and-followup-bank.md": "# 问题与追问库\n\n| 优先级 | 轮次 | 问题 | 面试目的 | 所需证据 | 连续追问 |\n| --- | --- | --- | --- | --- | --- |\n",
    "05-answer-and-90-day-plan.md": "# 答案与入职计划\n\n## 自我介绍：15秒/60秒\n\n## 核心项目：15秒/60秒/180秒\n\n## 风险问题\n\n## 失败案例\n\n## 30/60/90天计划\n\n| 阶段 | 目标 | 动作 | 产出 | 指标 | 依赖 | 风险 |\n| --- | --- | --- | --- | --- | --- | --- |\n",
    "06-mock-interview-log.md": "# 模拟面试记录\n\n执行状态：未执行\n\n| 问题 | 原回答 | 追问链 | 证据缺口 | 表达问题 | 改进 |\n| --- | --- | --- | --- | --- | --- |\n\n## 打断恢复训练\n",
    "07-interview-preflight.md": "# 面试前检查\n\n- [ ] 音频、视频、网络和备用设备\n- [ ] JD、轮次和面试官信息\n- [ ] 三张项目证据卡、风险卡、反问卡\n- [ ] 15秒和60秒自我介绍\n- [ ] 硬技能与保密边界\n",
    "08-interview-postmortem.md": "# 面试复盘\n\n执行状态：未执行\n\n## 来源类型与说话人确认\n\n## 确认问题、回答、追问和打断\n\n## 事实\n\n## 推断\n\n## 未知变量\n\n## 决定性问题与关键改进项\n",
    "09-interviewer-intelligence.md": "# 面试现场情报\n\n| 反问/面试官信息 | 想验证的假设 | 得到的答案 | 岗位判断变化 | 下一轮动作 |\n| --- | --- | --- | --- | --- |\n",
    "10-result-calibration.md": "# 结果校准\n\n| 日期 | 岗位/轮次 | 预测区间 | 置信度与证据 | 实际结果 | 真实反馈 | 高估/低估信号 | 不可控变量 | 是否复现 |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n",
    "11-learning-log.md": "# 迭代记录\n\n| 日期 | 岗位 | 轮次 | 结果 | 新问题 | 新证据 | 无效话术 | 下次训练 |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    private_dir = args.output / "private"
    private_dir.mkdir(exist_ok=True)
    (args.output / ".gitignore").write_text("private/\n*.raw.txt\n*.raw.json\n", encoding="utf-8")
    for name, content in FILES.items():
        target = args.output / name
        if not target.exists():
            target.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
