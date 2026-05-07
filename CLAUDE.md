# Running Log — Claude Context

## Running the app
```
uv run races.py          # starts on http://0.0.0.0:8080
uv run python -m unittest test_bug_fixes   # 175 tests
```

## Environment variables
| Variable | Purpose |
|---|---|
| `RUNNING_DB` | Path to SQLite DB (default: `~/Dropbox/Databases/RunningLog/races.sqlite`) |
| `GARMIN_EMAIL` | Garmin Connect login |
| `GARMIN_PASSWORD` | Garmin Connect password (backslash at end: use `"password\\"`) |

Garmin OAuth tokens are cached in `~/.garth/` — pre-authenticate locally to avoid MFA prompts.

## Key files
- `races.py` — all Flask routes
- `sql.py` — all DB queries and matplotlib chart generation
- `garmin.py` — Garmin Connect sync (fetch activities, format lap notes, map to form)
- `config.py` — env var reads
- `test_bug_fixes.py` — test suite (run after every change)
- `pyproject.toml` — declared dependencies

## Conventions
- Always run the test suite after changes; it should stay green
- Commit only when explicitly asked
- PRG pattern: POST success redirects to the list view (not re-renders)
- Bootstrap 3 throughout
- No authentication — personal local-only tool

## Garmin sync notes
- `get_activities_by_date` and `get_activity_details` have different response structures — the route passes summary data as URL params to avoid calling `get_activity_details`
- Lap duration field is `elapsedDuration` (not `duration`) — `_lap_secs()` in garmin.py handles this
- Garmin's Cloudflare blocks cloud datacenter IPs — sync only works from a home IP

## Weight chart
- `/PlotWeight` renders the page with range/goal controls
- `/WeightChart?range=365&goal=80` returns a PNG stream directly (no static file)
- `sql.get_weight_chart(cur, days, goal_weight)` generates the chart
