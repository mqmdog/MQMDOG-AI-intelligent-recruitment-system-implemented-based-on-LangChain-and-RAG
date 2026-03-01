from datetime import datetime, timezone, timedelta
import re


def datetime_to_iso8601_beijing(dt: datetime) -> str:
    """将 datetime 对象转换为 ISO-8601 格式字符串（北京时间 UTC+8）"""
    beijing_tz = timezone(timedelta(hours=8))

    if dt.tzinfo is None:
        dt_beijing = dt.replace(tzinfo=beijing_tz)
    else:
        dt_beijing = dt.astimezone(beijing_tz)

    return dt_beijing.replace(microsecond=0).isoformat()


def iso8601_to_datetime_beijing(iso_str: str) -> datetime:
    """
    将 ISO-8601 格式字符串转换为北京时间（UTC+8）的 datetime 对象

    支持格式:
        - 带时区偏移: "2022-11-27T08:30:00+08:00"
        - UTC 标记: "2022-11-27T00:30:00Z"
        - 无时区（naive）: "2022-11-27T08:30:00"（视为北京时间）

    Raises:
        ValueError: 输入字符串格式无效时抛出
    """
    normalized_str = iso_str.strip()
    if normalized_str.endswith("Z"):
        normalized_str = normalized_str[:-1] + "+00:00"

    # 处理微秒部分不足 6 位的补零
    normalized_str = re.sub(
        r"(\.\d{1,6})(?![\d:])",
        lambda m: m.group(1) + "0" * (6 - len(m.group(1)) + 1),
        normalized_str,
    )

    try:
        dt = datetime.fromisoformat(normalized_str)
    except ValueError as e:
        try:
            if " " in normalized_str and "T" not in normalized_str:
                normalized_str = normalized_str.replace(" ", "T", 1)
            dt = datetime.fromisoformat(normalized_str)
        except Exception:
            raise ValueError(f"无法解析ISO 8601字符串: '{iso_str}'。错误: {e}")

    beijing_tz = timezone(timedelta(hours=8))

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=beijing_tz)
    else:
        dt = dt.astimezone(beijing_tz)

    return dt
