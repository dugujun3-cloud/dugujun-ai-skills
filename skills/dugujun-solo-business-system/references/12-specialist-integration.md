# 专项 Skill 集成与主控收口

## 总原则

主控负责商业目标、运行状态、写入边界、阶段闸门、产物清单和用户验收；专项 Skill 负责其专业领域内的分析或产物。专项工作完成后必须回到主控，不得让专项流程自行宣告整个一人公司项目完成。

主控不复制专项 Skill 的完整方法论，不绕开专项质量闸门，也不把“已路由”当作“已完成”。

## 路由前检查

只有以下信息足以约束专项任务时才路由：

- 当前项目、阶段和本轮唯一目标。
- 目标客户、具体问题、Offer 或需要验证的假设。
- 可用输入文件和已验收上游产物。
- 写入目录、只读来源和禁止修改范围。
- 期望产物、验收标准、截止边界和失败保底。
- 是否涉及当前平台数据、敏感数据或外部动作。

信息不全时先完成可做部分，只询问会改变专项方向的问题。

## 标准专项 brief

```markdown
# Specialist Request
- request_id:
- controller_project_id:
- current_phase:
- specialist_skill:
- business_objective:
- target_customer_and_problem:
- validated_facts:
- hypotheses_to_preserve:
- input_files:
- output_directory:
- expected_artifacts:
- acceptance_criteria:
- current_data_or_web_verification_needed:
- write_boundary:
- forbidden_actions:
- external_action_policy:
- failure_fallback:
```

禁止把真实客户隐私、凭据、无关原始数据整包传递给专项 Skill。先做最小化、匿名化和必要字段提取。

## 标准回传契约

专项 Skill 应返回：

```markdown
# Specialist Result
- request_id:
- status: completed / partial / failed / awaiting_user / awaiting_external
- artifacts: 绝对路径列表
- checks_performed:
- evidence_added:
- assumptions_and_unknowns:
- unresolved_issues:
- user_action_needed:
- external_action_needed:
- publication_or_execution_state:
- recommended_controller_next_action:
```

主控收回后必须：检查文件存在、核对专项自检、确认没有越过写入/发布边界、登记新增证据和产物、处理未解决问题、执行当前阶段验收，再更新主状态。

## 用户运营衔接

出现以下问题时路由 `user-operations-playbook`：

- 用户分层、标签、生命周期、激活、留存、流失和召回。
- 会员、权益、复购、LTV、推荐、私域、CRM 或用户运营指标体系。
- 已有产品需要设计可衡量的用户运营实验或运营 SOP。

主控提供：业务阶段、产品和目标用户、基线证据、当前漏斗、需要解决的一个运营问题、可用数据、资源约束和期望决策。

专项返回：诊断、分层/生命周期/实验方案、指标口径、数据缺口、实施边界和产物路径。主控负责把它映射回 `30_offer_mvp`、`50_pilot_delivery`、`60_pricing_economics`、`70_acquisition_trust` 或 `90_scale_transition_review`，不让用户运营专项擅自改变产品定位、价格、外部承诺或发布状态。

## 小红书衔接

在 `40_market_validation` 需要最小招募内容，或在 `70_acquisition_trust` 建设可重复获客时，路由 `dugujun-xhs-operating-workflow`，再由其调用 `dugujun-xiaohongshu` 等执行层。

路由前主控必须确认：

- 这条内容服务哪个客户问题、哪一类信任和哪个商业下一步。
- Offer、CTA 和承接点已通过当前商业阶段验收。
- 当前平台趋势和分发状态由小红书专项判断，主控不凭通用商业知识替代。
- 内容草稿、图片验收、视频验收和实际发布分别记录。

专项完成后，主控只检查商业一致性、产物路径、平台自检和发布状态；不得绕过小红书图数、尺寸、内容源、数据闸门或人工发布边界。

## 知乎衔接

- 知乎想法、文章写作与平台表达：路由 `dugujun-zhihu-writing`。
- 搜索问题并形成 Markdown 回答：路由 `dugujun-zhihu-answer`。
- 渠道数据诊断：路由 `dugujun-zhihu-analytics`。

主控提供目标客户、商业问题、原始内容/案例、产品承接和需要建立的信任。知乎专项不得自动填入回答框或发布，除非用户明确授权对应动作；主控分别登记草稿、问题链接、用户验收和真实发布状态。

## 公众号与跨平台内容衔接

公众号文章正文写作不由本 Skill 接管。已有文章需要形成跨平台资产时，路由现有文章工作流；主控只定义其商业角色、客户问题、Offer 关系和预期下一步，并把专项产物纳入当前项目的资产和实验记录。

内容曝光、阅读或点赞只作为弱信号，不得直接升级为产品验证、成交或客户结果。

## 咨询与交付衔接

本 Skill 可生成咨询产品的准入、诊断、范围、交付 SOP 和验收框架。涉及深度用户运营诊断时路由 `user-operations-playbook`；涉及法律、税务、合同或专业责任时只准备问题和材料，交由有资质人士处理。

给真实客户发送问卷、方案、合同或交付物属于外部动作，必须使用审批状态机。

## 课程、产品知识库与 Web 应用衔接

- 课程分支需要内容/教学设计专项时，下发学习目标、目标学员、结果证据、内测范围和验收标准；主控保留产品承诺与商业闸门。
- 产品知识库只能写当前工作区的“产品知识库”，不得把产品化内容写回只读源知识库。
- Web 应用只在任务高频、输入结构化、规则稳定、输出可验收且人工交付已验证后路由产品设计和开发能力。先 PRD/原型/可用性测试，再决定开发；部署公开服务属于外部动作。

## 专项并行

只有两个以上任务写入边界清楚、互不依赖、可独立验收时才并行。主控在分发前指定不同输出目录或不同文件，防止覆盖；并行结果全部返回后统一检查商业口径、版本、重复和冲突。

不能并行的典型关系：先定 Offer 再写销售内容、先确认客户问题再设计课程、先验证人工流程再开发 Web 应用。

## 失败与保底

- `partial`：登记已完成产物和缺口，主控决定补做、降级或等待。
- `failed`：记录错误、输入、是否产生文件和安全状态；不把失败产物送审或发布。
- 专项不可用：使用最小本地模板形成可继续的 brief/草稿，但明确未经过专项质量闸门。
- 专项结果冲突：以更强证据、用户已验收上游决策和当前平台/官方信息为准；无法判断时回到主控提出一个会改变决策的问题。
- 专项越界：停止采用其外部动作或未授权修改，保留可验证产物并记录风险。

## 专项完成条件

专项 Skill 返回完成不等于主控阶段完成。只有以下条件同时满足才可收口：

1. 约定产物存在且可读取。
2. 专项质量检查通过或缺口已明确接受。
3. 没有越过知识库只读、写入、隐私和外部动作边界。
4. 产物与当前客户、问题、Offer 和阶段目标一致。
5. 用户完成所需的产物或阶段验收。
6. 主状态、产物清单、证据和 handoff 已更新。
