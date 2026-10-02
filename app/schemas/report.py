# app/schemas/report.py
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.chart import WuXing, ShiShen


# ---------- 基础：规则命中与依据 ----------
class RuleHit(BaseModel):
    """一条被触发的规则，是结论的最小依据单元。"""
    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(..., description="规则唯一 ID，对应 data/rules 中的记录。")
    source: str = Field(..., description="来源，如 '书A/第三章/第2节'。")
    text: str = Field(..., description="规则原文或整理后的说明。")
    school: str = Field(..., description="流派，如 扶抑派、调候派、盲派。")
    weight: float = Field(default=1.0, ge=0.0, description="该规则在本次结论中的权重。")
    matched_on: list[str] = Field(
        default_factory=list,
        description="命中的盘面要素，如 ['日主偏弱','月令为印']。",
    )


class Evidence(BaseModel):
    """一组支撑某结论的依据。"""
    model_config = ConfigDict(extra="forbid")

    hits: list[RuleHit] = Field(default_factory=list)
    conflicts: list[RuleHit] = Field(
        default_factory=list,
        description="与其他流派/规则冲突的依据，需在输出时说明。",
    )


# ---------- 旺衰 ----------
StrengthLevel = Literal["极弱", "偏弱", "中和", "偏旺", "极旺"]


class StrengthReport(BaseModel):
    """日主强弱判断。"""
    model_config = ConfigDict(extra="forbid")

    level: StrengthLevel
    score: float = Field(..., description="强弱评分，范围与算法约定，如 0-100。")
    method: str = Field(..., description="所用方法，如 '月令+通根+生扶'。")
    school: str = Field(..., description="流派。")
    evidence: Evidence
    notes: list[str] = Field(default_factory=list)


# ---------- 用神 ----------
YongshenMethod = Literal["扶抑", "调候", "通关", "病药", "专旺", "综合"]


class YongshenReport(BaseModel):
    """喜用忌仇闲判断。"""
    model_config = ConfigDict(extra="forbid")

    method: YongshenMethod
    school: str

    yong_shen: list[WuXing] = Field(default_factory=list, description="用神")
    xi_shen: list[WuXing] = Field(default_factory=list, description="喜神")
    ji_shen: list[WuXing] = Field(default_factory=list, description="忌神")
    chou_shen: list[WuXing] = Field(default_factory=list, description="仇神")
    xian_shen: list[WuXing] = Field(default_factory=list, description="闲神")

    # 可选：神煞/十神层面的喜忌
    favorable_ten_gods: list[ShiShen] = Field(default_factory=list)
    unfavorable_ten_gods: list[ShiShen] = Field(default_factory=list)

    evidence: Evidence
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    notes: list[str] = Field(default_factory=list)


# ---------- 格局 ----------
class GejuReport(BaseModel):
    """格局判断。"""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="格局名，如 正官格、食神制杀格。")
    category: Optional[str] = Field(default=None, description="格局大类，如 八正格、外格。")
    is_successful: Optional[bool] = Field(
        default=None,
        description="成格/破格判断，None 表示未判。",
    )
    school: str
    evidence: Evidence
    notes: list[str] = Field(default_factory=list)


# ---------- 大运流年吉凶 ----------
LuckLevel = Literal["大吉", "吉", "平", "凶", "大凶"]


class LuckItemReport(BaseModel):
    """某一步大运或某一流年的吉凶判断。"""
    model_config = ConfigDict(extra="forbid")

    index: int = Field(..., description="第几步大运，或年份。")
    label: str = Field(..., description="显示文本，如 '第3步大运 甲子' 或 '2026 丙午'。")
    stem: str
    branch: str
    level: LuckLevel
    related_wuxing: list[WuXing] = Field(default_factory=list)
    related_ten_gods: list[ShiShen] = Field(default_factory=list)
    evidence: Evidence
    notes: list[str] = Field(default_factory=list)


class LuckReport(BaseModel):
    """大运流年整体判断。"""
    model_config = ConfigDict(extra="forbid")

    da_yun_items: list[LuckItemReport] = Field(default_factory=list)
    liu_nian_items: list[LuckItemReport] = Field(default_factory=list)
    summary: Optional[str] = Field(default=None, description="总体趋势的简短说明。")
    school: str
    notes: list[str] = Field(default_factory=list)


# ---------- 主题推断 ----------
Topic = Literal["事业", "财运", "感情", "婚姻", "健康", "学业", "六亲", "性格"]


class TopicReport(BaseModel):
    """某一主题的命理推断。"""
    model_config = ConfigDict(extra="forbid")

    topic: Topic
    conclusion: str = Field(..., description="结论文本。")
    key_points: list[str] = Field(default_factory=list)
    evidence: Evidence
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    school: str
    notes: list[str] = Field(default_factory=list)


# ---------- 总报告 ----------
class MingliReport(BaseModel):
    """一次命理推断的完整结果。

    该模型是 agent 汇总输出的主要来源。
    所有结论均带 evidence，便于 LLM 解释、也便于人工复核。
    """
    model_config = ConfigDict(extra="forbid")

    # 可选：回填本次所用的输入摘要
    birth_summary: Optional[str] = Field(
        default=None,
        description="出生信息摘要，便于报告独立阅读。",
    )

    strength: Optional[StrengthReport] = None
    yongshen: Optional[YongshenReport] = None
    geju: Optional[GejuReport] = None
    luck: Optional[LuckReport] = None
    topics: list[TopicReport] = Field(default_factory=list)

    # 元信息
    schools_used: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(
        default_factory=list,
        description="如流派冲突、数据缺失、置信度低等提示。",
    )
    disclaimer: str = Field(
        default="本结果基于传统八字文化规则整理，仅供传统文化研究与娱乐参考，不构成现实决策建议。",
    )