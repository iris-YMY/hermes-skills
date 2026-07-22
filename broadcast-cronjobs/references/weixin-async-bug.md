# Weixin aiohttp Timeout Context Bug

## Error
```
delivery error: Weixin send failed: Timeout context manager should be used inside a task
```

## Full Call Chain
```
cron/scheduler.py: tick() → _process_job() → _deliver_result()
  → tools/send_message_tool.py: _send_to_platform()
    → _send_weixin()
      → gateway/platforms/weixin.py: send_weixin_direct()
        → adapter.send() → _send_text_chunk()
          → _send_message() → _api_post()
            → aiohttp session.post()
              → aiohttp TimerContext.__enter__()  💥
```

## Root Cause
In aiohttp 3.13.5, `TimerContext.__enter__()` (in `aiohttp/helpers.py:676`) calls:
```python
task = asyncio.current_task(loop=self._loop)
if task is None:
    raise RuntimeError("Timeout context manager should be used inside a task")
```

When the cron scheduler sends a weixin message via `asyncio.run_coroutine_threadsafe()` (line 439-444 of scheduler.py), the coroutine is scheduled onto the gateway's event loop. However, aiohttp's internal timer context (`TimerContext`) is created during `ClientSession.post()` and its `__enter__` method tries to find the current task via `asyncio.current_task()`. In certain thread-crossing scenarios, this returns None, causing the RuntimeError.

## Why Other Platforms Work
- **Feishu**: Uses lark-oapi SDK with different HTTP client
- **Telegram**: Uses python-telegram-bot (different HTTP library)
- **Discord**: Different aiohttp usage pattern

## Fix Options

### Option A: Retry in _send_text_chunk / send_weixin_direct (Minimal change)
In `gateway/platforms/weixin.py`, wrap `_api_post` calls with a retry that catches this specific RuntimeError and recreates the session. Also applies to `send_weixin_direct()` fallback path.

### Option B: Use asyncio.wait_for instead of aiohttp timeout (Recommended ✅)
Replace `aiohttp.ClientTimeout(total=X)` with wrapping the call in `asyncio.wait_for(coro, timeout=X)`. This uses Python's native task-based timeout instead of aiohttp's TimerContext, which avoids the `current_task()` issue entirely.

**Why Option B over A**: The bug affects both the live adapter path AND the standalone `send_weixin_direct()` path (confirmed 2026-06-03). A retry workaround is fragile; using `asyncio.wait_for` is a proper fix that works in all contexts.

### Option C: Skip weixin live adapter in cron (Partial fix)
In `cron/scheduler.py:_deliver_result()`, force weixin to standalone path. **Note**: This alone won't fix it — the standalone `send_weixin_direct()` also creates an aiohttp session and hits the same bug. Only useful as a temporary diagnostic step.

## Reproduction Log (2026-06-03)
- **Scheduled run** (08:00): Failed with `Timeout context manager should be used inside a task`
- **Manual run** (10:05): Same error — confirms it's not a transient race condition
- **Gateway status**: Running (PID 2467855), live adapter available
- **Both paths affected**: Live adapter (`run_coroutine_threadsafe`) AND standalone (`send_weixin_direct`) fail
- **aiohttp version**: 3.13.5
