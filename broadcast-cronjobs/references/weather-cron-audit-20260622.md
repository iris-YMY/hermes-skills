# Weather Cron Job Audit (2026-06-22, updated 2026-06-24)

## Current Status (2026-06-24)
- **Weather broadcast job**: Active on data-master profile (ID: `844cde709d24`)
- **Pre-fetch script**: ⚠️ `weather_data_fetcher.py` NOT YET CREATED — job relies on LLM running tools directly
- **Manual workaround tested**: wttr.in + WAQI demo API both work reliably as data sources

## Cross-Validation Results

Compared Open-Meteo (current source) with wttr.in for Shanghai on 2026-06-22:

| Data Point | Open-Meteo (11:05) | wttr.in (11:05) | Cron Output (08:01) |
|-----------|-------------------|-----------------|---------------------|
| Temperature | 26.0°C | 23°C | 24.9°C |
| Feels Like | 30.4°C | 26°C | 29.1°C |
| Humidity | 88% | 100% | 89% |
| Max/Min | 26.8/22.6 | 24/22 | 26.5/22.4 |
| Weather | Overcast (code 3) | Light Rain + Mist | Thunderstorm |

**Verdict**: Open-Meteo data is real and API-driven. Discrepancies with wttr.in are normal (different stations/models). Cron output at 08:01 was consistent with Open-Meteo at that time.

## Identified Issues

### 1. No Pre-fetch Script (HIGH PRIORITY)
News broadcast uses `news_data_fetcher.py` to pre-fetch data before prompt injection. Weather relies on LLM running `curl` commands directly — risk of:
- Parse errors from JSON output
- LLM hallucinating data if curl fails silently
- Wasted turns on API failures

**Recommendation**: Create `weather_data_fetcher.py` following the news pre-fetch pattern.

### 2. Wind Direction Conversion Missing
API returns degrees (e.g., 104°), but prompt only provides 8 compass codes (N/NE/E/SE/S/SW/W/NW) without a degree-to-compass formula.

**Fix**: Add conversion table to prompt:
```
0-22.5°=N, 22.5-67.5°=NE, 67.5-112.5°=E, 112.5-157.5°=SE,
157.5-202.5°=S, 202.5-247.5°=SW, 247.5-292.5°=W, 292.5-337.5°=NW,
337.5-360°=N
```

### 3. Single-Day Forecast
`forecast_days=1` only shows today. No multi-day trend for trip planning.

**Fix**: Change to `forecast_days=3` and add a "未来两天趋势" section.

### 4. IP Geolocation Risk
Server IP may not be Shanghai. Current fallback is hardcoded Shanghai coordinates, which works but:
- If server moves to a different region, user still gets Shanghai weather
- No way for user to set a preferred city

**Fix**: Add a `WEATHER_DEFAULT_CITY` config or hardcode Shanghai as the only city (since user lives there).

## Proposed Template Updates

### Option A: Lightweight (optimize existing prompt)
- Add wind direction degree-to-compass conversion
- Add `forecast_days=3` for multi-day trend
- Add data validation rules (LLM must show raw API values)

### Option B: Pre-fetch Script (recommended)
- Create `weather_data_fetcher.py` following news pattern
- Fetch weather + air quality + 3-day forecast
- Inject structured data into prompt
- LLM only formats and generates advice
- Eliminates hallucination risk entirely

## Cron Job Config
- Job ID: `7cc3e2941131`
- Schedule: `0 8 * * *` (08:00 CST)
- Model: `qwen3.6-plus`
- Deliver: `feishu`
- Output log: `~/.hermes/cron/output/7cc3e2941131/`
