# 研究文件契约

## research_plan.yaml

```yaml
topic: 研究主题
decision_question: 要支持的决定
scope:
  time_range: 2025-01-01 至今
  geography: 中国
  include: []
  exclude: []
items:
  - id: stable-slug
    name: 对象名
execution:
  pilot_size: 3
  output_dir: results
```

## fields.yaml

每个字段至少包含 `name`、`description`、`required`、`evidence_level`。`evidence_level` 使用 `primary`、`authoritative_secondary`、`any_reliable`。

## 对象 JSON

```json
{
  "id": "stable-slug",
  "name": "对象名",
  "fields": {},
  "sources": [
    {
      "url": "https://example.com",
      "title": "来源标题",
      "published_at": "2026-01-01",
      "accessed_at": "2026-08-13",
      "supports": ["field_name"]
    }
  ],
  "uncertain": [],
  "checked_at": "2026-08-13T00:00:00+08:00"
}
```

## research_status.json

记录 `planned`、`in_progress`、`complete`、`needs_review`、`failed`，以及最后错误、重试次数和下一动作。只有结果文件通过校验才允许标记 `complete`。
