---
name: ai-interview-copilot
description: Evidence-based AI interview preparation and post-interview review workflow. Use when a user wants to analyze a job description, match experience to a role, predict interview questions, build truthful answer scripts, practice one-question-at-a-time mock interviews, review an interview transcript, diagnose communication problems, estimate outcome uncertainty, or turn repeated interviews into a reusable learning system.
---

# AI Interview Copilot

把面试当作一个可迭代的证据系统：事实底稿、岗位拆解、硬门槛审计、风险预判、问题预测、回答工程、压力追问、真实复盘、结果校准。

## 固定原则

- 只使用用户提供或可核验的事实，不编造履历、数据、项目和公司信息。
- 先站在招聘方视角判断岗位要解决什么，再讨论候选人想获得什么。
- 不批量堆通用题库。问题必须来自岗位、候选人经历和风险点。
- 不把 STAR 当万能模板。重点呈现判断依据、决策逻辑、行动细节、结果和复用价值。
- 不用综合匹配分掩盖一票否决项。硬门槛必须分成已证明、相邻能力、明确不具备。
- 模拟面试一次只问一个问题，根据回答继续追问。
- 固定结构只用于备课，不要求候选人口头背模板。训练必须包含15秒、60秒、180秒三个版本和被打断恢复。
- 复盘必须区分事实、推断和未知变量。通过概率只能给区间、依据和置信度，不能假装确定。
- 高风险结论可做双模型独立复核：第二个模型不能先看到第一个模型的结论，最终比较证据分歧，不平均两个概率数字。
- 默认保护隐私。公开输出前删除姓名、联系方式、证件、薪酬、公司内部数据和可识别履历。

## 路由

根据用户当前阶段选择入口：

1. 只有 JD：执行岗位拆解、硬门槛识别和理想候选人建模。
2. 有 JD + 经历材料：建立事实底稿、项目证据卡、匹配矩阵、风险地图和问题预测。
3. 即将面试：按轮次生成准备简报、答案卡、连续追问树并进入压力模拟。
4. 有面试录音或逐字稿：先校正说话人和问题口径，再执行逐题复盘和结果校准。
5. 有多场历史面试：按“涉及场次数”识别模式，更新个人题库、失败模式和概率校准记录。

完整流程见 [workflow.md](references/workflow.md)。

## 输入检查

开始前列出已获得与缺失的材料：

- 岗位 JD、面试轮次、公司和业务信息。
- 候选人经历摘要或简历。
- 可核验项目案例和数字。
- 历史面试问题、逐字稿或复盘。
- 已知结果：通过、未通过、待定及真实反馈。
- 明确的硬技能边界，例如SQL、外语、管理人数和行业经验。

材料缺失时继续完成可完成部分，但显式标记假设，不替用户补事实。不要把尚未执行阶段的空模板当成交付完成。

## 核心工作流

### 1. 建立事实底稿与岗位拆解

先建立候选人的事实时间线和项目证据卡，再从 JD 提炼：业务目标、工作对象、核心指标、关键场景、能力证据、协作关系、硬门槛、加分项、风险项。

不要逐句改写 JD。输出「招聘方真正想解决的 3—5 个问题」。

每张项目证据卡至少包含：业务基线、目标来源、指标口径与周期、本人职责边界、关键判断、动作、资源依赖、结果相对目标、负面结果、可核验来源和公开边界。详见 [evidence-cards-and-followups.md](references/evidence-cards-and-followups.md)。

### 2. 硬门槛与候选人风险地图

找出招聘方最可能追问的特殊点：经历跳跃、行业切换、空窗期、项目数据、职责边界、管理范围、失败经历、离职动机和稳定性。

风险问题的优先级通常高于通用问题。每个风险点都要准备事实版回答，不粉饰、不自我攻击。

把硬门槛逐项标记为「已证明 / 相邻能力 / 明确不具备」。明确不具备时，直说边界，再给实际做过的相邻工作、协作边界、可验证案例和补强计划。不得编造SQL、管理或行业经验。

空窗、创业探索、回归职场、离职动机与稳定性必须共用一条时间线，至少连续追问三轮，检查因果是否一致。管理能力必须区分正式带人、项目负责人、辅导新人、跨部门影响和个人贡献者。

轮次差异、风险叙事、管理证据阶梯和现场训练见 [risk-narratives-and-rounds.md](references/risk-narratives-and-rounds.md)。

### 3. 问题预测

默认用「70% 训练时间和追问深度用于过往经历与个人风险 + 30% 用于 JD、业务和其他变量」分配准备精力；不是机械按题目数量切分，再根据岗位性质调整。

至少覆盖：自我介绍、代表项目、业务场景题、为什么公司和岗位、行业理解、优势与短板、职业规划、候选人反问，以及风险地图中的定制问题。

### 4. 回答工程与追问树

经历题使用：

```text
结论 → 必要背景 → 核心判断 → 关键行动 → 数据结果 → 可复用方法 → 与岗位的关系
```

场景题使用：

```text
诊断假设 → 数据验证 → 根因判断 → 小范围测试 → 分阶段落地 → 指标与风险
```

动机题优先回答「我能解决什么」，再回答「为什么选择这里」。

业务研究选择一条路径：全面扫清业务全貌，或选一个关键点做深度拆解。只做表面信息汇总不算准备完成。

每个核心项目至少压力追问五层：指标谁定、目标和口径是什么、本人到底做了什么、为什么采用这个动作、结果如何归因与复验。失败案例另用「预期—实际—异常信号—根因—本人责任—止损—机制修正—后续验证」。

跨行业回答使用「同类问题经验—关键行业差异—入职后的首个验证动作」。需要工作规划时输出30/60/90天计划，每阶段写清输入、动作、产出、指标、依赖和风险。

面试前最低答案覆盖：自我介绍、三张最强项目证据卡、全部硬门槛、全部高风险叙事、为什么公司与岗位、一个失败案例、两个岗位场景题、30/60/90天计划和分轮次反问。证据不足的项目不写成完整答案，只保留结构与待补项。

### 5. 模拟面试

一次只问一个问题。每轮记录：原回答、追问链、证据缺口、表达问题、改写建议和下一题。

不要在用户回答前给标准答案。评分标准见 [scoring-rubric.md](references/scoring-rubric.md)。

训练三种长度：15秒结论、60秒主答、180秒完整案例。至少进行一次随机打断；被打断后执行「停下—确认真正问题—一句结论—补一个证据」。检查背稿感、自问自答、连续模糊词和所有答案结构雷同。

### 6. 真实面试复盘

从逐字稿中还原全部问题，逐题检查：是否直接回答、证据是否充分、是否展示决策逻辑、是否匹配岗位、哪里被打断或追问。先区分真实面试、准备稿、面试官、候选人、现场沟通和业务介绍；不能把疑似问句数当真实问题数。

面试官的客套结束语不能单独作为通过信号。概率判断必须列出可控因素、不可控因素和证据强度。

### 7. 迭代沉淀

把结果写回个人系统：新增问题、暴露风险、有效案例、无效话术、真实结果和下次动作。连续多场出现的问题，按涉及场次数升级为核心训练项。

记录面试前预测区间、证据强度、实际结果、真实反馈、曾高估或低估的信号和下一场是否复现。反问不是礼节：每个反问必须说明要验证的假设，并把面试官答案回写到岗位理解、隐性要求和下一轮准备。

### 8. 双模型复核（可选）

用于通过概率、关键短板和重大职业判断。把同一份脱敏材料分别交给两个模型，要求各自列出事实、推断、未知和反证。第二轮再比较：共同证据、冲突证据、遗漏证据和需要人工判断的地方。

如果两个模型结论冲突，回到原始逐字稿找证据；不要选择更好听的答案，也不要把两个概率取平均。

AI 本身也要被审计：禁止臆造数据、把公司文化刻板印象当淘汰依据、迎合用户、因用户质疑机械改概率、把相关性当因果。详细协议见 [ai-review-guardrails.md](references/ai-review-guardrails.md)。

## 交付物

按任务生成必要文件，不要求每次全部生成：

- `00-input-and-truth-ledger.md`
- `01-job-deconstruction.md`
- `02-project-evidence-cards.md`
- `03-hard-gates-and-risk-map.md`
- `04-question-and-followup-bank.md`
- `05-answer-and-90-day-plan.md`
- `06-mock-interview-log.md`
- `07-interview-preflight.md`
- `08-interview-postmortem.md`
- `09-interviewer-intelligence.md`
- `10-result-calibration.md`
- `11-learning-log.md`

可运行 [init_interview_workspace.py](scripts/init_interview_workspace.py) 创建工作目录。

处理逐字稿时可运行 [extract_interview_transcript.py](scripts/extract_interview_transcript.py)，先检查自动识别的面试官说话人；聚合多场结果时运行 [analyze_interview_corpus.py](scripts/analyze_interview_corpus.py)，按涉及场次数排序。公开前运行 [redact_interview_text.py](scripts/redact_interview_text.py)。

提示词模板见 [prompt-templates.md](references/prompt-templates.md)，经验来源与适用边界见 [evidence-base.md](references/evidence-base.md)，隐私规则见 [privacy-and-redaction.md](references/privacy-and-redaction.md)。用户增长、会员、复购与LTV岗位可按需读取 [user-growth-interview-patterns.md](references/user-growth-interview-patterns.md)。

## 输出要求

- 先给结论和下一步动作，再给分析。
- 引用候选人原话时只截取必要片段。
- 明确标注「事实」「推断」「未知」。
- 不用讨好式评价，不因用户质疑就机械修改概率。
- 标准答案必须能追溯到真实经历；无法追溯时输出回答结构和待补证据。
