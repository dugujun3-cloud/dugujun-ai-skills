---
name: getnote-blogger-batch-import
description: 将得到大脑知识库中的单个博主内容批量提取为独立 Markdown 笔记，并通过官方 ZIP 导入保留原标题。用于用户要求整理、还原、迁移或批量创建得到大脑博主内容，尤其是需要先做一条试样、断点续跑、跳过已完成条目、修正特殊标题和核验最终数量时。
---

# 得到大脑博主批量转写

把一个得到大脑博主来源转换为独立笔记。默认先试样、验收后全量；用户明确授权直接全量时可跳过试样。

## 边界

- 只用得到大脑官方 `getnote` CLI 读取，以及得到大脑官方 Markdown/ZIP 导入界面写入。
- 不读取或复用私有 Cookie、本地数据库、内部接口和明文 API Key。
- 不删除原博主来源，不覆盖已有笔记；先确定需要跳过的 `post_id_alias`。
- 不用 `post_summary` 代替正文。视频取 `post_media_text`；无逐字稿的图文动态取原始 `post_name`。
- 通过 Computer Use 操作应用导入。上传 ZIP 属外部写入：已有明确预授权才直接执行，否则在点击“开始导入”前确认。

## 前置检查

1. 运行 `getnote auth status`，确认已经登录。
2. 获取目标知识库 `topic_id` 和博主 `follow_id`。
3. 读取博主列表并记录总数、顺序、已完成条目及用户要求排除的内容。
4. 在当前工作区创建独立运行目录，不写入用户的只读知识库目录。

脚本位置：`scripts/export_blogger_transcripts.py`。

## 执行

先审计标题：

```bash
python3 scripts/export_blogger_transcripts.py audit \
  --topic-id TOPIC_ID \
  --follow-id FOLLOW_ID \
  --output-root RUN_DIR
```

审计 `logs/title_filename_audit.json`。斜杠、超长标题或重复标题可能无法直接通过文件名精确保留；记录这些条目，导入后逐条改回原标题。

生成一条试样：

```bash
python3 scripts/export_blogger_transcripts.py pilot \
  --topic-id TOPIC_ID \
  --follow-id FOLLOW_ID \
  --pilot-id POST_ID \
  --output-root RUN_DIR
```

核验试样：

- ZIP 只包含一个 `.md`。
- 文件名去扩展名后等于原标题。
- 正文不含标题行，只含逐字稿或原始动态文字。
- 正文字数与 SHA-256 匹配 manifest。

通过得到大脑“导入 Markdown → ZIP 压缩包”导入试样。用户验收后生成全量包：

```bash
python3 scripts/export_blogger_transcripts.py remaining \
  --topic-id TOPIC_ID \
  --follow-id FOLLOW_ID \
  --skip-post-id DONE_ID_1 \
  --skip-post-id DONE_ID_2 \
  --workers 6 \
  --output-root RUN_DIR
```

每个已完成或已验收条目都传一次 `--skip-post-id`。脚本会复用 manifest 中已成功生成的文件，只补抓未完成条目。

## 导入与核验

1. 核验 manifest：错误数为 0、记录数等于目标数、ZIP 条目唯一、正文哈希全部一致。
2. 通过官方 ZIP 入口导入，记录界面返回的成功/失败数量。
3. 按标题审计清单修正特殊标题。
4. 运行只读终检：

```bash
python3 scripts/export_blogger_transcripts.py verify \
  --topic-id TOPIC_ID \
  --follow-id FOLLOW_ID \
  --expected-notes-total EXPECTED_TOTAL \
  --output-root RUN_DIR
```

5. 报告笔记总数、匹配标题数、正文精确匹配数、仅排版差异数和内容差异数。

## 交付

- 保留 ZIP、pilot/remaining manifest、标题审计和导入校验报告。
- 写入 `workflow_status.json` 与 `handoff.md`，区分已生成、已导入、已验收。
- 用户说“验收”后，将状态改为 `completed`，执行工作区规定的任务结束回调。

## 当前轻量版限制

- 一次只处理一个博主和一个目标知识库。
- 依赖本机已安装并登录的 `getnote` CLI。
- 特殊标题仍需通过应用界面人工修正。
- 暂未覆盖多个博主编排、自动分批导入和跨设备恢复；后续真实使用后再扩展。
