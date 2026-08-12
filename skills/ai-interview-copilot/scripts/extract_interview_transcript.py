#!/usr/bin/env python3
"""Extract role-aware interview questions and exchanges from TXT or DOCX."""

from __future__ import annotations

import argparse
import json
import re
import statistics
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree


SPEAKER = re.compile(r"^说话人\s*(?P<speaker>[^\s]+)\s+(?P<time>\d{1,2}:\d{2}(?::\d{2})?)(?:\s+(?P<inline>.*))?\s*$")
PREP_QUESTION = re.compile(r"问题\s*\d+\s*[:：]\s*(.+?)(?=\n\s*问题\s*\d+\s*[:：]|\Z)", re.S)
QUESTION_OPENERS = (
    "为什么", "怎么", "如何", "什么", "是否", "能否", "哪", "多少", "几", "有没有",
    "请介绍", "介绍一下", "自我介绍", "做个介绍", "想了解", "想问", "说一下", "谈一下", "讲一下", "展开一下", "举个例子",
)
INTERVIEWER_CUES = QUESTION_OPENERS + ("你", "您", "负责", "指标", "结果", "岗位", "离职", "团队")
CANDIDATE_CUES = ("我在", "我的", "我们当时", "我负责", "我做", "我的经历", "我的理解")
LOGISTICS = re.compile(r"(能听到|听得清|可以看到|开.*视频|摄像头|耳机|声音|网络|稍等|等我几分钟|准备好了吗|现在开始|开始吧|我是.*面试官|面试主要会有|面试.*几个部分|不好意思.*耽误)")

QUESTION_TYPES = {
    "自我介绍": ("自我介绍", "介绍一下自己", "介绍自己", "个人介绍", "过往经历"),
    "求职动机与稳定性": ("为什么离职", "离职原因", "空窗", "待业", "创业", "回归职场", "职业规划", "为什么选择"),
    "岗位与公司动机": ("为什么应聘", "为什么是", "了解我们", "了解这个岗位", "为什么录用"),
    "项目与个人贡献": ("项目", "案例", "你负责", "本人", "主导", "贡献", "最有效"),
    "指标与数据": ("指标", "数据", "口径", "目标", "结果", "SQL", "实验", "A/B"),
    "落地与协作": ("落地", "协同", "跨部门", "资源", "冲突", "推进", "团队"),
    "失败与复盘": ("失败", "没达到", "不及预期", "复盘", "挑战", "难点"),
    "业务与行业": ("业务", "行业", "竞品", "商业模式", "用户路径", "核心逻辑"),
    "场景题": ("如果让你", "如果入职", "前三个月", "30/60/90", "假如", "会怎么做", "怎么提升", "如何提升", "方案"),
    "管理与领导力": ("管理", "带人", "下属", "绩效", "组织架构", "分工"),
    "反向提问": ("有什么问题", "想问", "需要了解"),
}


def read_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    return "\n".join(
        text
        for paragraph in root.iter(ns + "p")
        if (text := "".join(node.text or "" for node in paragraph.iter(ns + "t")).strip())
    )


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        return read_docx(path)
    return path.read_text(encoding="utf-8", errors="replace")


def parse(text: str) -> list[dict[str, str]]:
    turns: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal current, buffer
        if current and buffer:
            current["text"] = " ".join(buffer).strip()
            turns.append(current)
        current, buffer = None, []

    for raw in text.splitlines():
        line = raw.strip()
        match = SPEAKER.match(line)
        if match:
            flush()
            current = {"speaker": match.group("speaker"), "time": match.group("time")}
            if match.group("inline"):
                buffer.append(match.group("inline").strip())
        elif line:
            current = current or {"speaker": "unknown", "time": ""}
            buffer.append(line)
    flush()
    return turns


def question_like(text: str) -> bool:
    compact = re.sub(r"\s+", "", text)
    if len(compact) < 4:
        return False
    if "？" in compact or "?" in compact:
        return True
    if re.search(r"请.{0,8}(介绍|说明|讲|谈)", compact[:80]):
        return True
    return any(opener in compact[:80] for opener in QUESTION_OPENERS)


def infer_interviewers(turns: list[dict[str, str]]) -> tuple[list[str], float, dict[str, dict[str, float]]]:
    by_speaker: dict[str, list[str]] = {}
    for turn in turns:
        if turn["speaker"] != "unknown":
            by_speaker.setdefault(turn["speaker"], []).append(turn["text"])
    scores: dict[str, dict[str, float]] = {}
    for speaker, texts in by_speaker.items():
        lengths = [len(text) for text in texts]
        q_ratio = sum(question_like(text) for text in texts) / max(len(texts), 1)
        interviewer_hits = sum(any(cue in text for cue in INTERVIEWER_CUES) for text in texts)
        candidate_hits = sum(any(cue in text for cue in CANDIDATE_CUES) for text in texts)
        avg_len = statistics.mean(lengths) if lengths else 0
        score = q_ratio * 8 + interviewer_hits / max(len(texts), 1) * 3 - candidate_hits / max(len(texts), 1) * 2 - min(avg_len, 400) / 400
        scores[speaker] = {"score": round(score, 3), "question_ratio": round(q_ratio, 3), "average_length": round(avg_len, 1)}
    ranked = sorted(scores, key=lambda item: scores[item]["score"], reverse=True)
    if not ranked:
        return [], 0.0, scores
    gap = scores[ranked[0]]["score"] - (scores[ranked[1]]["score"] if len(ranked) > 1 else 0)
    confidence = max(0.0, min(1.0, 0.5 + gap / 4))
    return [ranked[0]], round(confidence, 2), scores


def split_question_units(text: str) -> list[str]:
    units = [unit.strip() for unit in re.split(r"(?<=[。！？?])", text) if unit.strip()]
    matched = [unit for unit in units if question_like(unit)]
    return matched or ([text.strip()] if question_like(text) else [])


def classify(text: str) -> list[str]:
    labels = [
        label
        for label, keywords in QUESTION_TYPES.items()
        if any(keyword.lower() in text.lower() for keyword in keywords)
    ]
    return labels or ["其他追问"]


def extract_transcript(turns: list[dict[str, str]], interviewer_speakers: set[str]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, object]]]:
    questions: list[dict[str, str]] = []
    logistics: list[dict[str, str]] = []
    exchanges: list[dict[str, object]] = []
    for index, turn in enumerate(turns):
        if turn["speaker"] not in interviewer_speakers:
            continue
        units = split_question_units(turn["text"])
        if not units:
            continue
        answers: list[dict[str, str]] = []
        for following in turns[index + 1:]:
            if following["speaker"] in interviewer_speakers:
                break
            answers.append(following)
        for unit in units:
            item = {"speaker": turn["speaker"], "time": turn["time"], "text": unit}
            if LOGISTICS.search(unit):
                logistics.append(item)
                continue
            item["types"] = classify(unit)
            item["type"] = item["types"][0]
            questions.append(item)
            exchanges.append({"question": item, "answer_turns": answers})
    return questions, logistics, exchanges


def extract_prep_questions(text: str) -> list[dict[str, str]]:
    output = []
    for match in PREP_QUESTION.finditer(text):
        first_line = match.group(1).strip().splitlines()[0].strip()
        labels = classify(first_line)
        output.append({"speaker": "prepared", "time": "", "text": first_line, "types": labels, "type": labels[0]})
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source-type", choices=("auto", "transcript", "prep"), default="auto")
    parser.add_argument("--interviewer-speaker", action="append", default=[])
    args = parser.parse_args()

    text = read_text(args.input)
    turns = parse(text)
    speakers = sorted({turn["speaker"] for turn in turns if turn["speaker"] != "unknown"})
    source_type = args.source_type
    if source_type == "auto":
        source_type = "transcript" if len(speakers) >= 2 else "prep"

    inferred, confidence, role_scores = infer_interviewers(turns)
    interviewers = [re.sub(r"^说话人\s*", "", speaker) for speaker in args.interviewer_speaker] or inferred
    if source_type == "transcript":
        questions, logistics, exchanges = extract_transcript(turns, set(interviewers))
    else:
        questions, logistics, exchanges = extract_prep_questions(text), [], []

    result = {
        "source": args.input.name,
        "source_type": source_type,
        "role_detection": {
            "interviewer_speakers": interviewers,
            "manually_supplied": bool(args.interviewer_speaker),
            "confidence": confidence,
            "speaker_scores": role_scores,
            "needs_review": source_type == "transcript" and not args.interviewer_speaker and confidence < 0.8,
        },
        "summary": {
            "speaker_turn_count": len(turns),
            "role_filtered_question_count": len(questions),
            "logistics_count": len(logistics),
            "question_types": dict(Counter(label for item in questions for label in item["types"]).most_common()),
        },
        "questions": questions,
        "logistics": logistics,
        "exchanges": exchanges,
        "turns": turns,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
