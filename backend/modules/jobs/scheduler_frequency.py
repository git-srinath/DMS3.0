from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger


def _sanitize_int(value: Optional[Any], default: Optional[int] = None) -> Optional[int]:
    if value in (None, "", "null"):
        return default
    return int(value)


def _sanitize_weekday(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return value.strip().lower()


def build_trigger(schedule_row: Dict[str, Any], timezone: str):
    frqcd = schedule_row.get("FRQCD")
    frqdd = schedule_row.get("FRQDD")
    frqhh = _sanitize_int(schedule_row.get("FRQHH"), 0)
    frqmi = _sanitize_int(schedule_row.get("FRQMI"), 0)
    strtdt: Optional[datetime] = schedule_row.get("STRTDT")
    enddt: Optional[datetime] = schedule_row.get("ENDDT")

    if frqcd == "YR":
        return CronTrigger(
            month="1",
            day=str(frqdd or 1),
            hour=frqhh,
            minute=frqmi,
            timezone=timezone,
            start_date=strtdt,
            end_date=enddt,
        )
    if frqcd == "HY":
        return CronTrigger(
            month="1,7",
            day=str(frqdd or 1),
            hour=frqhh,
            minute=frqmi,
            timezone=timezone,
            start_date=strtdt,
            end_date=enddt,
        )
    if frqcd == "MN":
        return CronTrigger(
            day=str(frqdd or 1),
            hour=frqhh,
            minute=frqmi,
            timezone=timezone,
            start_date=strtdt,
            end_date=enddt,
        )
    if frqcd == "FN":
        weekday = _sanitize_weekday(frqdd) or "mon"
        return CronTrigger(
            day_of_week=weekday,
            hour=frqhh,
            minute=frqmi,
            timezone=timezone,
            start_date=strtdt,
            end_date=enddt,
        )
    if frqcd == "WK":
        weekday = _sanitize_weekday(frqdd) or "mon"
        return CronTrigger(
            day_of_week=weekday,
            hour=frqhh,
            minute=frqmi,
            timezone=timezone,
            start_date=strtdt,
            end_date=enddt,
        )
    if frqcd == "DL":
        return CronTrigger(
            hour=frqhh,
            minute=frqmi,
            timezone=timezone,
            start_date=strtdt,
            end_date=enddt,
        )
    if frqcd == "ID":
        if schedule_row.get("FRQHH") is not None:
            minute = frqmi if frqmi is not None else 0
            return CronTrigger(
                minute=minute,
                timezone=timezone,
                start_date=strtdt,
                end_date=enddt,
            )
        interval_minutes = frqmi or 15
        return IntervalTrigger(
            minutes=interval_minutes,
            timezone=timezone,
            start_date=strtdt,
            end_date=enddt,
        )
    return IntervalTrigger(
        minutes=60,
        timezone=timezone,
        start_date=strtdt,
        end_date=enddt,
    )

