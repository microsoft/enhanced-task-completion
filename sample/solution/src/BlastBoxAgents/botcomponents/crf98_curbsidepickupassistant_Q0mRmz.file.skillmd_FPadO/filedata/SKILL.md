---
name: staging-window-calculator
description: Calculate the exact Curb Delivery conditions band, collection bay, and staging time from the customer ETA, order quantities, store layout, and Metric weather conditions.
---

# Curb Delivery Staging Window Calculator

This skill applies the BlastBox Curb Delivery staging policy deterministically.
**Always run the bundled `blastbox_staging.py` script. Never compute the staging
window, band, or bay choice yourself, and never write your own code.**

## Data orchestration

The high point of this workflow is combining facts from distinct sources:

- **Order Management MCP** supplies the order, customer, item quantities, and
  shipping city/state used to identify the pickup store. Order status is
  informational and must not block this curbside workflow.
- **Curb Delivery MCP** supplies the store coordinates, bay layout, and current
  bay occupancy.
- **Membership MCP v2** supplies `tier_code` only when the customer provides a
  membership ID; otherwise use `standard`.
- **MSN Weather** `CurrentWeather` and `TodaysForecast` supply live Metric
  conditions and store-local sunset.
- The bundled Python script combines those supplied facts into the conditions
  band, staging time, and bay selection.

No connector or skill fetches weather itself. The agent must not invent,
reinterpret, or calculate policy thresholds in prose; every threshold and its
priority order live only in `blastbox_staging.py`.

## When to use

Use this skill after the order, store, customer ETA, weather conditions, and
optional membership tier are known. It decides the conditions band, best free bay, exact store-local staging time,
customer arrival estimate, weather impact, delivery handling, and customer
precaution. Do not use it to look up any input.

`stage_at` is when an already-picked order moves into curbside handoff staging.
It is not the start of picking or order preparation.

Order status is not an eligibility rule for this workflow. Do not reject, stop,
or skip the staging calculation because an existing order is processing,
shipped, delivered, or has another status.

## Workflow

### 1. Assemble the inputs

Source every value before running the script:

- `--eta-minutes` comes from the customer's own words.
- `--item-count` is the total number of physical units, summed from order
  quantities. It is not the number of product lines.
- `--bays-json` is the exact JSON object returned by Curb Delivery MCP
  `list_bays`, including current occupancy. Never reuse a previous response.
- `--store-timezone` is the `timezone_id` returned in that same MCP response.
- `--cap`, `--wx`, `--temp`, `--feels`, `--wind-spd`, `--wind-gust`,
  `--wind-dir`, and `--rain-chance` come from MSN Weather `CurrentWeather` and
  `TodaysForecast`. Weather values must be **Metric only**: Celsius, km/h, and
  percent.
- `--now` must be a timezone-aware ISO-8601 value using the destination store's
  current local UTC offset.
- For live conditions, `--sunset` must also be a timezone-aware ISO-8601 value
  using the destination store's local offset.
- For fallback conditions, pass the MCP value as `--sunset-local HH:MM` instead
  of `--sunset`. The script combines it with the store-local date and offset
  already supplied by `--now`. Curb Delivery also returns the authoritative
  `timezone_id` for DST-aware time calculation.
- `--store` is the pickup city and state, such as `Springfield, IL`.
- `--tier-code` comes from `get_membership` only when the customer supplies a
  membership ID. Otherwise use the default `standard` tier so normal,
  non-priority bay behavior applies.
- `--conditions-source` is `live` normally or `fallback` when live weather was
  unavailable.

The script contains the policy thresholds. It makes no API or network calls.
Do not reinterpret its result.

### Fallback disclosure

If the result has `conditions_source: fallback`, the reply **MUST say the
conditions are typical for that store, not current**. Never present fallback data
as live.

### 2. Run the bundled calculator

```bash
python3 blastbox_staging.py stage \
  --eta-minutes 20 --item-count 3 \
  --store "Springfield, IL" --store-timezone America/Chicago \
  --bays-json '{"location":"Springfield, IL","timezone_id":"America/Chicago","bays":[{"bay_id":1,"covered":true,"lit":true,"facing":90,"priority":true,"occupied":false,"occupied_by":null},{"bay_id":2,"covered":true,"lit":true,"facing":180,"priority":false,"occupied":false,"occupied_by":null},{"bay_id":3,"covered":false,"lit":false,"facing":270,"priority":false,"occupied":false,"occupied_by":null}]}' \
  --cap "Rain showers" --wx "RA" --temp 30 --feels 33 \
  --wind-spd 12 --wind-gust 20 --wind-dir 180 --rain-chance 70 \
  --now 2026-09-02T15:40:00-05:00 \
  --sunset 2026-09-02T19:20:00-05:00 \
  --tier-code mega --conditions-source live
```

For this Springfield wet-weather example, three physical units take 6 minutes
to pick. The script chooses priority covered **bay 1** for the
MEGA tier and prints:

```text
STAGE AT: 15:55 (T+15) | BAY 1 | COVERED | band=WET | source=live
```

### 3. Report the result

Use the returned `weather_reason`, `bay_reason`, `delivery_instruction`, and
`customer_precaution` in the customer response. Report the bay and customer
instruction first, followed by the staging time, arrival estimate, weather
impact, bay reason, delivery handling, and relevant safety precaution. Preserve
any fallback or degraded-bay note from the script.
