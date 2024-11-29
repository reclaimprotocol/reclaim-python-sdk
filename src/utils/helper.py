import asyncio
from typing import Callable, Dict
from asyncio import Task

def clear_interval(intervals: Dict[str, Task], session_id: str) -> None:
    """Clear the interval for a session."""
    if session_id in intervals:
        intervals[session_id].cancel()
        del intervals[session_id]

async def schedule_interval_ending(
    intervals: Dict[str, Task],
    session_id: str,
    on_error: Callable[[Exception], None]
) -> None:
    """Schedule the ending of intervals."""
    await asyncio.sleep(10)
    if session_id in intervals:
        await on_error(Exception("Session timed out"))
        clear_interval(intervals, session_id)
