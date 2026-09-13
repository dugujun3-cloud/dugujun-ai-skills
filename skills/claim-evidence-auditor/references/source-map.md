# 来源映射
## direct_source
| source_ref | location | distilled_method | short_evidence |
|---|---|---|---|
| M01 | 作者内部方法笔记 | 事实/结论/价值拆分、五级核验、推理链审计 | “这些事实能否推出当前结论” |
## paraphrase
| rule_id | source_ref | faithful_restating |
|---|---|---|
| R-01 | M01 | 把复合说法拆为可分别检验的主张。 |
| R-02 | M01 | 事实可信度与推理有效性分别判断。 |
## extension
| rule_id | design_decision | why_needed | validation_needed |
|---|---|---|---|
| E-01 | 默认只读 | 核查不等于获准改稿或执行方案 | 改稿混合意图用例 |
| E-02 | 明确访问限制 | 防止把未联网内容写成核实 | 离线场景用例 |
