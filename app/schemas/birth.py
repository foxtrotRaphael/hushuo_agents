# app/schemas/birth.py
from __future__ import annotations

from datetime import date, time
from typing import Literal, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


Gender = Literal["男", "女"]
CalendarType = Literal["公历", "农历"]
# 农历闰月标记：None 表示非闰月；数字表示闰几月
LeapMonth = Optional[int]


class BirthInput(BaseModel):
    """出生信息输入。
    该模型只承载“原始出生信息”，不包含任何排盘结果。
    排盘逻辑（四柱、十神、旺衰、用神）一律放到 core 层。
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    # ---------- 基本信息 ----------
    gender: Gender = Field(
        ...,
        description="性别，仅支持 男 / 女。",
    )

    calendar: CalendarType = Field(
        default="公历",
        description="历法类型：公历 或 农历。",
    )

    # ---------- 出生日期时间 ----------
    birth_date: date = Field(
        ...,
        description="出生日期。公历时为公历年月日；农历时为农历年月日。",
    )

    birth_time: time = Field(
        ...,
        description="出生时刻（24 小时制）。传统排盘通常需要精确到时辰。",
    )

    # ---------- 农历专用 ----------
    is_leap_month: bool = Field(
        default=False,
        description="当 calendar='农历' 时，该月是否为闰月。",
    )

    # ---------- 地理 / 时区 ----------
    timezone: str = Field(
        default="Asia/Shanghai",
        description="IANA 时区名，例如 Asia/Shanghai、Asia/Tokyo。",
    )

    location: Optional[str] = Field(
        default=None,
        description="出生地名称，可选。用于真太阳时校正或记录。",
    )

    longitude: Optional[float] = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description="出生地经度，东经为正，西经为负。真太阳时校正需要。",
    )

    latitude: Optional[float] = Field(
        default=None,
        ge=-90.0,
        le=90.0,
        description="出生地纬度，北纬为正，南纬为负。可选。",
    )

    true_solar_time: bool = Field(
        default=False,
        description="是否将输入时间视为已经过真太阳时校正的时间。",
    )

    # ---------- 校验 ----------
    @field_validator("timezone")
    @classmethod
    def _check_timezone(cls, v: str) -> str:
        try:
            ZoneInfo(v)
        except ZoneInfoNotFoundError as e:
            raise ValueError(f"无效的 IANA 时区名: {v}") from e
        return v

    @model_validator(mode="after")
    def _check_consistency(self) -> "BirthInput":
        # 农历闰月只在农历下有意义
        if self.calendar == "公历" and self.is_leap_month:
            raise ValueError("公历输入不应设置 is_leap_month=True。")

        # 真太阳时校正需要经度
        if self.true_solar_time and self.longitude is None:
            raise ValueError("启用 true_solar_time 时必须提供 longitude。")

        return self


class BirthInfo(BaseModel):
    """排盘内部使用的规范化出生信息。

    与 BirthInput 的区别：
    - BirthInput 是“用户/LLM 传入的原始信息”；
    - BirthInfo 是历法转换后的“公历 + 时区 + 校正后时刻”，供 core.paipan 使用。
    """

    model_config = ConfigDict(extra="forbid")

    gender: Gender
    # 统一转换为公历
    solar_datetime_utc: "datetime"  # noqa: F821  # 运行期由 pydantic 解析
    timezone: str
    location: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    true_solar_time_applied: bool = False


# 放在文件末尾，避免前向引用问题
from datetime import datetime  # noqa: E402

BirthInfo.model_rebuild()