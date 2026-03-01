from datetime import datetime, timedelta, time
from typing import List, Tuple, Optional


def find_available_slot(
    busy_slots: List[Tuple[datetime, datetime]],
    hour_interval: float = 1.0,
    start_date: Optional[datetime] = None,
    max_days_to_search: int = 7,
) -> List[Tuple[datetime, datetime]]:
    """
    查找指定天数内所有可用的连续时间段用于面试

    Args:
        busy_slots: 已占用时间段列表，每个元素为 (start, end)
        hour_interval: 需要的连续时长（小时），默认 1.0
        start_date: 开始查找的日期，默认为明天
        max_days_to_search: 最大搜索天数，默认 7 天

    Returns:
        可用时间段列表 [(start, end), ...]

    时间窗口: 上午 09:00-12:00, 下午 14:00-18:00
    """
    if start_date is None:
        tomorrow = datetime.now().date() + timedelta(days=1)
        current_search_date = datetime.combine(tomorrow, time.min)
    else:
        current_search_date = datetime.combine(start_date.date(), time.min)

    daily_windows = [
        (time(9, 0), time(12, 0)),
        (time(14, 0), time(18, 0)),
    ]

    # 预处理：修正结束时间早于开始时间的错误数据
    normalized_busy = []
    for start, end in busy_slots:
        if end < start:
            start, end = end, start
        normalized_busy.append((start, end))

    available_slots: List[Tuple[datetime, datetime]] = []
    interval_delta = timedelta(hours=hour_interval)

    for day_offset in range(max_days_to_search):
        search_date = current_search_date + timedelta(days=day_offset)

        for win_start_time, win_end_time in daily_windows:
            window_start = datetime.combine(search_date.date(), win_start_time)
            window_end = datetime.combine(search_date.date(), win_end_time)

            # 收集与当前窗口重叠的忙碌时段
            conflicts = []
            for busy_start, busy_end in normalized_busy:
                if busy_end > window_start and busy_start < window_end:
                    actual_start = max(busy_start, window_start)
                    actual_end = min(busy_end, window_end)
                    if actual_end > actual_start:
                        conflicts.append((actual_start, actual_end))

            conflicts.sort(key=lambda x: x[0])

            # 在空闲间隙中切出可用时段
            current_time = window_start
            for conflict_start, conflict_end in conflicts:
                while conflict_start - current_time >= interval_delta:
                    available_slots.append(
                        (current_time, current_time + interval_delta))
                    current_time += interval_delta
                current_time = max(current_time, conflict_end)

            # 检查最后一个冲突后的剩余空间
            while window_end - current_time >= interval_delta:
                available_slots.append(
                    (current_time, current_time + interval_delta))
                current_time += interval_delta

    return available_slots
