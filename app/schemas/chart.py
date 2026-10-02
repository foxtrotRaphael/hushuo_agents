# app/schemas/chart.py
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.birth import Gender


# ---------- 基础枚举 ----------
WuXing = Literal["木", "火", "土", "金", "水"]
YinYang = Literal["阳", "阴"]
ShiShen = Literal[
    "比肩", "劫财", "食神", "伤官", "偏财", "正财",
    "七杀", "正官", "偏印", "正印",
]
TwelveStage = Literal[
    "长生", "沐浴", "冠带", "临官", "帝旺",
    "衰", "病", "死", "墓", "绝", "胎", "养",
]
# 刑冲合害等关系类型
RelationType = Literal[
    "天干五合", "天干相冲",
    "地支六合", "地支三合", "地支三会",
    "地支相冲", "地支相刑", "地支相害", "地支相破",
]


# ---------- 单柱 ----------
class HiddenStem(BaseModel):
    """地支藏干。"""
    model_config = ConfigDict(extra="forbid")

    stem: str = Field(..., description="藏干天干，如 甲、乙。")
    wuxing: WuXing
    ten_god: Optional[ShiShen] = Field(
        default=None,
        description="该藏干相对日主的十神。日柱本身可为空。",
    )
    is_primary: bool = Field(
        default=False,
        description="是否为本气（主气）。",
    )


class Pillar(BaseModel):
    """一柱：天干 + 地支。"""
    model_config = ConfigDict(extra="forbid")

    stem: str = Field(..., description="天干")
    branch: str = Field(..., description="地支")
    stem_wuxing: WuXing
    branch_wuxing: WuXing
    stem_yin_yang: YinYang
    branch_yin_yang: YinYang
    hidden_stems: list[HiddenStem] = Field(default_factory=list)
    ten_god_stem: Optional[ShiShen] = Field(
        default=None,
        description="天干相对日主的十神。日柱天干为日主本身，可为空。",
    )
    na_yin: Optional[str] = Field(default=None, description="纳音")
    twelve_stage: Optional[TwelveStage] = Field(
        default=None,
        description="该柱地支相对日主的长生十二宫。",
    )


# ---------- 五行统计 ----------
class WuXingCount(BaseModel):
    """五行数量统计。"""
    model_config = ConfigDict(extra="forbid")

    raw: dict[WuXing, int] = Field(
        default_factory=dict,
        description="仅按天干 + 地支本气统计的数量。",
    )
    weighted: dict[WuXing, float] = Field(
        default_factory=dict,
        description="按藏干加权后的数量，权重由 core 层决定。",
    )
    missing: list[WuXing] = Field(
        default_factory=list,
        description="完全缺失的五行。",
    )


# ---------- 刑冲合害 ----------
class Relation(BaseModel):
    """地支/天干之间的关系。"""
    model_config = ConfigDict(extra="forbid")

    type: RelationType
    members: list[str] = Field(..., description="参与关系的干支，如 ['子','丑']。")
    positions: list[str] = Field(
        default_factory=list,
        description="所在柱位，如 ['year','month']。",
    )
    note: Optional[str] = None


# ---------- 大运流年 ----------
class LuckPillar(BaseModel):
    """大运或流年的一柱。"""
    model_config = ConfigDict(extra="forbid")

    index: int = Field(..., description="第几步，从 1 开始。")
    stem: str
    branch: str
    start_age: Optional[float] = Field(
        default=None,
        description="起运年龄（虚岁或周岁由 options 决定），仅大运有。",
    )
    start_year: Optional[int] = Field(
        default=None,
        description="该步大运起始公历年，仅大运有。",
    )
    ten_god_stem: Optional[ShiShen] = None
    ten_god_branch: Optional[ShiShen] = Field(
        default=None,
        description="地支本气相对日主的十神。",
    )


class DaYun(BaseModel):
    """大运序列。"""
    model_config = ConfigDict(extra="forbid")

    direction: Literal["顺行", "逆行"]
    start_age: float = Field(..., description="起运年龄。")
    start_year: int = Field(..., description="起运公历年。")
    pillars: list[LuckPillar] = Field(default_factory=list)


# ---------- 主盘 ----------
class BaziChart(BaseModel):
    """完整八字盘。

    只承载“排盘结果”，不含吉凶、用神等解释性结论。
    """

    model_config = ConfigDict(extra="forbid")

    # 元信息
    gender: Gender
    solar_datetime: datetime = Field(..., description="排盘所用公历时间。")
    lunar_date: str = Field(..., description="农历日期文本，如 '甲辰年正月初一'。")
    timezone: str
    true_solar_time_applied: bool = False

    # 四柱
    year: Pillar
    month: Pillar
    day: Pillar
    hour: Pillar

    # 日主
    day_master: str = Field(..., description="日柱天干，即日主。")
    day_master_wuxing: WuXing

    # 月令 / 节气
    month_branch: str = Field(..., description="月支，即月令。")
    solar_term: Optional[str] = Field(
        default=None,
        description="出生所处节气，如 '立春'。",
    )

    # 五行统计
    wuxing: WuXingCount

    # 关系
    relations: list[Relation] = Field(default_factory=list)

    # 大运（可选，取决于是否传入起运所需信息）
    da_yun: Optional[DaYun] = None

    # 空亡、神煞等可扩展
    kong_wang: list[str] = Field(default_factory=list)
    shen_sha: dict[str, list[str]] = Field(default_factory=dict)


# ---------- 排盘选项 ----------
class PaipanOptions(BaseModel):
    """排盘规则选项，避免流派差异写死在内核。"""
    model_config = ConfigDict(extra="forbid")

    zi_shi_rule: Literal["早子时换日", "晚子时换日", "子时不换日"] = "早子时换日"
    year_boundary: Literal["立春", "正月初一"] = "立春"
    month_boundary: Literal["节气", "农历月"] = "节气"
    use_true_solar_time: bool = False
    day_master_strength_method: Literal["月令+通根+生扶", "简化计数"] = "月令+通根+生扶"