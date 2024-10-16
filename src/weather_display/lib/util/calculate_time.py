from datetime import datetime, timedelta


def get_record_time_diff(curr: datetime, record_time: datetime):
    time_difference: timedelta = curr - record_time
    total_minutes: float = time_difference.total_seconds() // 60

    return total_minutes
