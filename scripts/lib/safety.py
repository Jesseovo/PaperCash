#!/usr/bin/env python3
"""安全与伦理检查模块"""

from typing import Literal
import random
import sys
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path

# 功能风险等级定义
RiskLevel = Literal["safe", "caution", "high"]

RISK_WARNINGS = {
    "humanize": {
        "level": "high",
        "warning": """
⚠️  表达修改建议 - 使用须知
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 本功能提供有限的表达修改建议，不预测或保证任何AI检测结果
2. 改写可能导致语义漂移，必须人工逐句审核
3. 以下内容禁止使用本功能改写：
   • 医学数据、剂量、统计结果
   • 法律条文、案号、判决要点
   • 技术参数、实验数据、公式推导
4. 最终文本应体现您本人的思考和理解
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """.strip(),
    },
    "check": {
        "level": "caution",
        "warning": """
ℹ️  查重预检 - 重要说明
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 本工具使用句子级学术检索，与知网/维普/Turnitin算法完全不同
2. 检索范围有限；没有找到相似论文不代表原创
3. 建议用途：定位相似句 → 核对原文与引用 → 学校正式查重
4. 正式查重请使用学校指定系统
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """.strip(),
    },
    "expand": {
        "level": "caution",
        "warning": """
ℹ️  段落扩写 - 使用建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 扩写内容需要您的润色和个性化调整
2. 避免直接提交扩写结果，可能被识别为AI生成
3. 建议用途：获取写作思路 → 融入自己观点 → 重新表达
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """.strip(),
    },
}


def show_risk_warning(feature: str) -> None:
    """显示功能风险警告（仅显示，不强制确认）"""
    if feature in RISK_WARNINGS:
        print(RISK_WARNINGS[feature]["warning"], file=sys.stderr)
        print(file=sys.stderr)


def identify_high_risk_segments(text: str) -> dict:
    """识别文本中的高风险段落（不应AI改写的内容）"""
    import re

    patterns = {
        "medical_data": {
            "regex": r"\d+\.?\d*\s?(mg|毫克|ml|毫升|mmol|μg|微克|kg|千克|公斤|g|克|例|人|名|位|患者|受试者|病人|志愿者|%|cm|厘米|mm|毫米)",
            "description": "医学数据/剂量",
        },
        "legal_clause": {
            "regex": r"(第[0-9一二三四五六七八九十百千]+条|[0-9]+\.[0-9]+\.[0-9]+|《.{2,20}》第)",
            "description": "法律条文/条款号",
        },
        "statistics": {
            "regex": r"(p\s?[<>=]\s?0\.\d+|r\s?=\s?[0-9-]\.\d+|t\s?=\s?[0-9-]\.\d+|F\s?=\s?\d+)",
            "description": "统计结果",
        },
        "citations": {
            "regex": r"(\[\d+[-,\d]*\]|\(\w+,?\s?\d{4}\))",
            "description": "文献引用",
        },
        "formulas": {
            "regex": r"([a-zA-Z]\s?[=±+\-*/]\s?[a-zA-Z0-9\.\(\)]+|[∫∑∏√])",
            "description": "数学公式",
        },
    }

    findings = {}
    for category, config in patterns.items():
        matches = re.finditer(config["regex"], text)
        positions = [(m.start(), m.end(), m.group()) for m in matches]
        if positions:
            findings[category] = {
                "description": config["description"],
                "count": len(positions),
                "examples": [pos[2] for pos in positions[:3]],
            }

    return findings


def get_academic_integrity_notice() -> str:
    """学术诚信总声明"""
    return """
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  PaperCash 学术诚信声明                              ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃  1. 本工具旨在辅助学术写作，不鼓励任何学术不端行为   ┃
┃  2. 所有生成内容需经用户审核、修改、融入个人思考     ┃
┃  3. 引用的真实性、数据的准确性由用户最终负责         ┃
┃  4. 建议用途：获取灵感 → 理解消化 → 独立表达         ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    """.strip()


# ==================== 强制确认与审计机制 (v2.0) ====================

AUDIT_DIR = Path.home() / ".papercash" / "audit"


def require_explicit_confirmation(feature: str) -> dict:
    """强制确认机制 - 显示警告并要求输入随机确认码"""
    print(RISK_WARNINGS[feature]["warning"], file=sys.stderr)
    print(file=sys.stderr)

    code = f"{random.randint(1000, 9999)}"
    print(f"⚠️  为确保已阅读上述内容，请输入确认码: {code}", file=sys.stderr)
    print("确认码: ", end="", file=sys.stderr, flush=True)
    try:
        user_input = input().strip()
    except EOFError:
        print("需要交互式确认，操作已取消", file=sys.stderr)
        return {"confirmed": False}

    if user_input != code:
        print("❌ 确认码错误，操作已取消", file=sys.stderr)
        return {"confirmed": False}

    print("\n📋 使用目的:", file=sys.stderr)
    print("1. 学习改进写作", file=sys.stderr)
    print("2. 测试工具效果", file=sys.stderr)
    print("3. 其他正当用途", file=sys.stderr)
    print("请选择 (1-3): ", end="", file=sys.stderr, flush=True)
    try:
        purpose = input().strip()
    except EOFError:
        print("需要交互式确认，操作已取消", file=sys.stderr)
        return {"confirmed": False}

    purpose_map = {"1": "学习", "2": "测试", "3": "其他"}
    if purpose not in purpose_map:
        print("❌ 无效选择，操作已取消", file=sys.stderr)
        return {"confirmed": False}

    return {"confirmed": True, "purpose": purpose_map[purpose], "code": code}


def log_operation(command: str, input_text: str, purpose: str = None) -> None:
    """记录操作到审计日志（仅存储hash，不存储原文）"""
    log_file = AUDIT_DIR / f"{datetime.now():%Y-%m}.jsonl"
    entry = {
        "time": datetime.now().isoformat(),
        "cmd": command,
        "hash": hashlib.sha256(input_text.encode()).hexdigest()[:16],
        "len": len(input_text),
        "purpose": purpose
    }

    try:
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"⚠️  审计日志写入失败: {e}", file=sys.stderr)


def check_abuse() -> None:
    """检测异常使用模式（24小时内超过100次调用）"""
    log_file = AUDIT_DIR / f"{datetime.now():%Y-%m}.jsonl"
    if not log_file.exists():
        return

    cutoff = datetime.now() - timedelta(hours=24)
    recent = []

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if datetime.fromisoformat(entry["time"]) >= cutoff:
                        recent.append(entry)
                except:
                    pass

        if len(recent) > 100:
            print("⚠️  检测到高频使用 (24小时内 >100次)")
            print("   请确保您在正当地使用本工具\n")
    except Exception:
        pass
