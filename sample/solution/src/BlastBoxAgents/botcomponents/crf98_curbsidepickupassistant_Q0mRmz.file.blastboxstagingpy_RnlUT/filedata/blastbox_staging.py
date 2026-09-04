#!/usr/bin/env python3
"""BlastBox Curb Delivery staging-window calculator.

Bundled skill script: the agent supplies the customer ETA, physical item count,
Metric weather values, store, membership tier, and conditions source as CLI
flags. The script applies policy, selects a bay, and prints a deterministic
staging breakdown.

Usage:
    python3 blastbox_staging.py stage \\
        --eta-minutes 20 --item-count 3 \\
        --store "Springfield, IL" --store-timezone America/Chicago \\
        --bays-json '{"location":"Springfield, IL","timezone_id":"America/Chicago","bays":[...]}' \\
        --cap "Rain showers" --wx RA --temp 30 --feels 33 \\
        --wind-spd 12 --wind-gust 20 --wind-dir 180 --rain-chance 70 \\
        --now 2026-09-02T15:40:00-05:00 \\
        --sunset 2026-09-02T19:20:00-05:00 \\
        --tier-code mega --conditions-source live
"""

import argparse
from datetime import datetime, time, timedelta, timezone, tzinfo
import json
import re
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


# --- BlastBox Curb Delivery staging policy --------------------------------
# These are store policy values, not measurements. Change here, nowhere else.

HOT_FEELS_C          = 38.0   # apparent temp at or above -> HOT band
COLD_TEMP_C          = 2.0    # actual temp at or below   -> COLD band
WINDY_GUST_KMH       = 40.0   # gust at or above          -> WINDY band
RAIN_CHANCE_PCT      = 60     # forecast rain chance at or above -> treat as WET
DARK_BUFFER_MIN      = 20     # minutes before sunset that counts as dark

PICK_MINUTES_PER_ITEM = 2.0   # base pick time per physical unit
HANDOFF_BUFFER_MIN    = 3.0   # slack so the order is ready as customer arrives

# Band-specific staging adjustment (minutes). Positive = stage LATER.
BAND_STAGE_ADJUST = {
    "WET":    4.0,   # keep goods indoors longer
    "HOT":    5.0,   # do not let electronics bake
    "COLD":   3.0,   # battery cold-soak
    "WINDY":  2.0,   # loose packaging
    "DARK":   0.0,   # timing unaffected; bay choice changes
    "BENIGN": -2.0,  # safe to stage early, fastest handoff
}

# METAR / caption tokens that indicate wet conditions.
WET_CAPTION_TOKENS = (
    "rain", "drizzle", "shower", "thunderstorm", "sleet", "snow", "hail",
    "wintry", "freezing precipitation",
)
WET_WX_CODES = ("RA", "DZ", "SN", "SG", "PL", "GR", "GS", "UP")


def detect_band(cap, wx, temp, feels, wind_gust, rain_chance, is_dark):
    """Return one of WET/HOT/COLD/WINDY/DARK/BENIGN.

    Priority order is fixed and MUST NOT be reordered:
        WET > HOT > COLD > WINDY > DARK > BENIGN
    Rationale: bands are ordered by risk to the goods. Precipitation is the
    only condition that can damage boxed electronics in seconds.
    """
    caption = (cap or "").lower()
    weather_code = re.sub(r"[^A-Z]", "", (wx or "").upper())
    if (
        any(token in caption for token in WET_CAPTION_TOKENS)
        or any(code in weather_code for code in WET_WX_CODES)
        or rain_chance >= RAIN_CHANCE_PCT
    ):
        return "WET"
    if feels >= HOT_FEELS_C:
        return "HOT"
    if temp <= COLD_TEMP_C:
        return "COLD"
    if wind_gust >= WINDY_GUST_KMH:
        return "WINDY"
    if is_dark:
        return "DARK"
    return "BENIGN"


def is_leeward(bay_facing, wind_dir):
    """A bay is leeward when it faces away from the wind.

    Wind direction is the direction the wind comes FROM.
    Sheltered when the angular difference is > 90 degrees.
    """
    diff = abs(((bay_facing - wind_dir + 180) % 360) - 180)
    return diff > 90


def _choose_by_tier(candidates, tier_code):
    ordered = sorted(candidates, key=lambda bay: bay["bay_id"])
    tier = (tier_code or "").lower()
    if tier in ("mega", "extra"):
        priority = [bay for bay in ordered if bay.get("priority")]
        return priority[0] if priority else ordered[0]
    non_priority = [bay for bay in ordered if not bay.get("priority")]
    return non_priority[0] if non_priority else ordered[0]


def select_bay(band, bays, occupancy, wind_dir, tier_code):
    """Choose a bay. Returns (bay_id, handoff_mode, note).

    handoff_mode: COVERED | SHADED | LIT | LEEWARD | STANDARD | EXPOSED
    """
    available = sorted(
        [
            bay for bay in bays
            if not occupancy.get(str(bay["bay_id"]))
        ],
        key=lambda bay: bay["bay_id"],
    )
    if not available:
        return None, "NONE", "No free bay"

    filters = {
        "WET": (lambda bay: bay["covered"], "COVERED"),
        "HOT": (lambda bay: bay["covered"], "SHADED"),
        "COLD": (lambda bay: bay["covered"], "COVERED"),
        "DARK": (lambda bay: bay["lit"], "LIT"),
        "WINDY": (lambda bay: is_leeward(bay["facing"], wind_dir), "LEEWARD"),
        "BENIGN": (lambda bay: True, "STANDARD"),
    }
    preferred_filter, handoff_mode = filters[band]
    candidates = [bay for bay in available if preferred_filter(bay)]
    note = ""

    if not candidates:
        candidates = available
        if band == "WET":
            handoff_mode = "EXPOSED"
            note = (
                "No covered bay available - keep goods indoors until the customer "
                "has stopped, bag before bringing out"
            )
        elif band == "HOT":
            handoff_mode = "EXPOSED"
            note = "No shade available - bring out only on arrival"
        elif band == "COLD":
            handoff_mode = "EXPOSED"
            note = (
                "No covered bay available - minimize outdoor exposure in cold "
                "conditions"
            )
        elif band == "DARK":
            handoff_mode = "EXPOSED"
            note = "No lit bay free - associate will carry a torch"
        elif band == "WINDY":
            handoff_mode = "EXPOSED"
            note = "No sheltered bay free"

    selected = _choose_by_tier(candidates, tier_code)
    return selected["bay_id"], handoff_mode, note


def compute_stage_at(eta_minutes, item_count, band):
    """Return non-negative whole minutes from now at which staging should start."""
    pick = PICK_MINUTES_PER_ITEM * item_count
    adjust = BAND_STAGE_ADJUST[band]
    stage_at = eta_minutes - pick - HANDOFF_BUFFER_MIN + adjust
    return max(0, round(stage_at))


def build_guidance(band, handoff_mode, bay, note, tier_code):
    """Return deterministic customer-facing weather and delivery guidance."""
    guidance = {
        "WET": (
            "Rain or precipitation risk requires a covered handoff and keeps "
            "the order indoors longer.",
            "Keep the order indoors until the vehicle is parked, then use "
            "weather-protective bagging for the handoff.",
            "Remain in your vehicle and keep the trunk accessible; use caution "
            "if you must step onto wet pavement.",
        ),
        "HOT": (
            "High apparent temperature requires shade and delays outdoor staging.",
            "Keep the order indoors until arrival and move it directly to the vehicle.",
            "Remain in your vehicle and avoid standing on hot pavement.",
        ),
        "COLD": (
            "Cold conditions require covered handling and minimal outdoor exposure.",
            "Keep the order indoors until arrival and complete the handoff promptly.",
            "Remain in your vehicle and use caution if the pavement is slippery.",
        ),
        "WINDY": (
            "Strong gusts require a sheltered bay and secured packaging.",
            "Secure loose packaging before taking the order outside.",
            "Remain in your vehicle and use caution when opening doors or the trunk.",
        ),
        "DARK": (
            "Arrival near or after sunset requires a well-lit bay.",
            "Bring the order directly to the vehicle after it is parked in the lit bay.",
            "Remain in your vehicle and use caution if you need to step outside.",
        ),
        "BENIGN": (
            "Current conditions require no special weather accommodation.",
            "Stage the order normally and bring it directly to the parked vehicle.",
            "Remain in your vehicle until the associate begins the handoff.",
        ),
    }
    weather_reason, delivery_instruction, customer_precaution = guidance[band]

    if bay is None:
        bay_reason = "No bay is currently available."
    elif handoff_mode == "EXPOSED":
        bay_reason = (
            f"No bay meeting the {band.lower()} weather preference was free; "
            f"bay {bay['bay_id']} was selected as the available fallback."
        )
    else:
        traits = []
        if bay["covered"]:
            traits.append("covered")
        if bay["lit"]:
            traits.append("well-lit")
        if handoff_mode == "LEEWARD":
            traits.append("sheltered from the wind")
        trait_text = ", ".join(traits) if traits else "available"
        requirement = {
            "WET": "covered-weather",
            "HOT": "shaded",
            "COLD": "covered cold-weather",
            "WINDY": "wind-sheltered",
            "DARK": "after-dark",
            "BENIGN": "standard",
        }[band]
        tier_reason = ""
        if (tier_code or "").lower() in ("mega", "extra") and bay["priority"]:
            tier_reason = " It also satisfies the verified membership priority."
        elif (tier_code or "").lower() not in ("mega", "extra") and not bay["priority"]:
            tier_reason = " The priority bay remains available for eligible members."
        bay_reason = (
            f"Bay {bay['bay_id']} is currently free and {trait_text}, matching "
            f"the {requirement} handoff requirement.{tier_reason}"
        )

    if note:
        delivery_instruction = f"{delivery_instruction} {note}"

    return {
        "weather_reason": weather_reason,
        "bay_reason": bay_reason,
        "delivery_instruction": delivery_instruction,
        "customer_precaution": customer_precaution,
    }


def _parse_aware_iso(value, flag_name):
    normalized = value[:-1] + "+00:00" if value.endswith(("Z", "z")) else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(
            f"{flag_name} must be a timezone-aware ISO-8601 value with a UTC offset"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(
            f"{flag_name} must be a timezone-aware ISO-8601 value with a UTC offset"
        )
    return parsed


def _normalize_location(value):
    normalized = (value or "").casefold()
    for source, replacement in (
        ("illinois", "il"),
        ("california", "ca"),
        ("washington", "wa"),
        ("blastbox", ""),
        ("store", ""),
    ):
        normalized = normalized.replace(source, replacement)
    return "".join(character for character in normalized if character.isalnum())


def parse_bays_json(value, expected_location, expected_timezone):
    """Parse the current list_bays MCP response into layout and occupancy."""
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError("--bays-json must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("--bays-json must be the complete list_bays JSON object")
    location = payload.get("location")
    if (
        not isinstance(location, str)
        or _normalize_location(location) != _normalize_location(expected_location)
    ):
        raise ValueError("--bays-json location must match --store")
    timezone_id = payload.get("timezone_id")
    if timezone_id != expected_timezone:
        raise ValueError("--bays-json timezone_id must match --store-timezone")
    records = payload.get("bays")
    if not isinstance(records, list) or not records:
        raise ValueError("--bays-json must contain a non-empty bays array")

    bays = []
    occupancy = {}
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("--bays-json bay entries must be JSON objects")
        bay_id = record.get("bay_id")
        if isinstance(bay_id, bool) or not isinstance(bay_id, int) or bay_id <= 0:
            raise ValueError("--bays-json bay_id values must be positive integers")
        if bay_id in seen:
            raise ValueError("--bays-json bay_id values must be unique")
        seen.add(bay_id)
        for field in ("covered", "lit", "priority", "occupied"):
            if not isinstance(record.get(field), bool):
                raise ValueError(f"--bays-json {field} values must be boolean")
        facing = record.get("facing")
        if isinstance(facing, bool) or not isinstance(facing, (int, float)):
            raise ValueError("--bays-json facing values must be numeric")
        bays.append(
            {
                "bay_id": bay_id,
                "covered": record["covered"],
                "lit": record["lit"],
                "facing": float(facing) % 360,
                "priority": record["priority"],
            }
        )
        occupancy[str(bay_id)] = (
            record.get("occupied_by") or "occupied"
            if record["occupied"]
            else None
        )
    return bays, occupancy


def _first_sunday_on_or_after(value):
    return value + timedelta(days=(6 - value.weekday()) % 7)


class _PacificFallbackTimezone(tzinfo):
    """US Pacific rules used only when the host has no IANA timezone database."""

    _standard = timedelta(hours=-8)
    _daylight = timedelta(hours=-7)

    def utcoffset(self, value):
        return self._daylight if self.dst(value) else self._standard

    def dst(self, value):
        if value is None:
            return timedelta(0)
        naive = value.replace(tzinfo=None)
        start = _first_sunday_on_or_after(datetime(value.year, 3, 8, 2))
        end = _first_sunday_on_or_after(datetime(value.year, 11, 1, 2))
        if start <= naive < start + timedelta(hours=1):
            return timedelta(hours=1) if value.fold else timedelta(0)
        if end - timedelta(hours=1) <= naive < end:
            return timedelta(0) if value.fold else timedelta(hours=1)
        if start + timedelta(hours=1) <= naive < end - timedelta(hours=1):
            return timedelta(hours=1)
        return timedelta(0)

    def tzname(self, value):
        return "PDT" if self.dst(value) else "PST"

    def fromutc(self, value):
        start = _first_sunday_on_or_after(
            datetime(value.year, 3, 8, 2, tzinfo=self)
        )
        end = _first_sunday_on_or_after(
            datetime(value.year, 11, 1, 2, tzinfo=self)
        )
        standard_time = value + self._standard
        daylight_time = standard_time + timedelta(hours=1)
        if end <= daylight_time < end + timedelta(hours=1):
            return standard_time.replace(fold=1)
        if standard_time < start or daylight_time >= end:
            return standard_time
        if start <= standard_time < end - timedelta(hours=1):
            return daylight_time
        return standard_time


class _CentralFallbackTimezone(_PacificFallbackTimezone):
    """US Central rules used only when the host has no IANA timezone database."""

    _standard = timedelta(hours=-6)
    _daylight = timedelta(hours=-5)

    def tzname(self, value):
        return "CDT" if self.dst(value) else "CST"


FALLBACK_TIMEZONES = {
    "America/Chicago": _CentralFallbackTimezone(),
    "America/Los_Angeles": _PacificFallbackTimezone(),
}


def _resolve_timezone(timezone_id):
    try:
        return ZoneInfo(timezone_id)
    except ZoneInfoNotFoundError:
        fallback = FALLBACK_TIMEZONES.get(timezone_id)
        if fallback is None:
            raise ValueError(f"unsupported --store-timezone: {timezone_id}")
        return fallback


def _parse_sunset(sunset_iso, sunset_local, local_now, store_tz):
    if sunset_iso:
        return _parse_aware_iso(sunset_iso, "--sunset").astimezone(store_tz)
    if not sunset_local:
        raise ValueError("provide --sunset or --sunset-local")
    try:
        parsed_time = time.fromisoformat(sunset_local)
    except ValueError as exc:
        raise ValueError("--sunset-local must use HH:MM or HH:MM:SS") from exc
    return datetime.combine(local_now.date(), parsed_time, tzinfo=store_tz)


def compute_staging(
    *,
    eta_minutes,
    item_count,
    cap,
    wx,
    temp,
    feels,
    wind_spd,
    wind_gust,
    wind_dir,
    rain_chance,
    now_iso,
    store_timezone,
    sunset_iso=None,
    sunset_local=None,
    bays,
    occupancy,
    tier_code,
    conditions_source,
):
    """Deterministically combine supplied operational and weather facts."""
    now = _parse_aware_iso(now_iso, "--now")
    store_tz = _resolve_timezone(store_timezone)
    local_now = now.astimezone(store_tz)
    local_sunset = _parse_sunset(sunset_iso, sunset_local, local_now, store_tz)
    expected_arrival = (
        local_now.astimezone(timezone.utc) + timedelta(minutes=eta_minutes)
    ).astimezone(store_tz)
    is_dark = expected_arrival >= local_sunset - timedelta(
        minutes=DARK_BUFFER_MIN
    )

    band = detect_band(
        cap, wx, temp, feels, wind_gust, rain_chance, is_dark
    )
    bay_id, handoff_mode, note = select_bay(
        band, bays, occupancy, wind_dir, tier_code
    )
    selected_bay = next(
        (bay for bay in bays if bay["bay_id"] == bay_id),
        None,
    )
    guidance = build_guidance(
        band, handoff_mode, selected_bay, note, tier_code
    )
    pick_minutes = PICK_MINUTES_PER_ITEM * item_count
    stage_at_minutes = compute_stage_at(eta_minutes, item_count, band)
    stage_at_clock = (
        local_now.astimezone(timezone.utc)
        + timedelta(minutes=stage_at_minutes)
    ).astimezone(store_tz).strftime("%H:%M")
    arrival_clock = expected_arrival.strftime("%H:%M")

    bay_text = "NONE" if bay_id is None else str(bay_id)
    adjust = BAND_STAGE_ADJUST[band]
    lines = [
        f"Customer ETA: {eta_minutes} minutes",
        (
            f"Operational facts: {item_count} physical units, "
            f"{len(bays)} configured bays, tier={tier_code or 'standard'}"
        ),
        (
            f"Weather facts: cap={cap or 'none'}, temp={temp:.1f}C, "
            f"feels={feels:.1f}C, wind={wind_spd:.1f}km/h, "
            f"gust={wind_gust:.1f}km/h, rain_chance={rain_chance:g}%, "
            f"sunset={local_sunset.strftime('%H:%M %z')}"
        ),
        (
            f"Pick time: {item_count} physical units x "
            f"{PICK_MINUTES_PER_ITEM:.1f} = {pick_minutes:.1f} minutes"
        ),
        f"Conditions band: {band} (stage adjustment {adjust:+.1f} minutes)",
        f"Bay selection: {bay_text} ({handoff_mode})",
    ]
    if note:
        lines.append(f"Bay note: {note}")
    lines.extend(
        [
            f"Weather impact: {guidance['weather_reason']}",
            f"Bay reason: {guidance['bay_reason']}",
            f"Delivery handling: {guidance['delivery_instruction']}",
            f"Customer precaution: {guidance['customer_precaution']}",
        ]
    )
    if conditions_source == "fallback":
        lines.append(
            "Conditions source: fallback - typical for this store, not current"
        )
    else:
        lines.append("Conditions source: live (MSN Weather)")
    lines.append(
        f"Stage timing: T+{stage_at_minutes} at {stage_at_clock} store local time"
    )
    lines.append(
        f"Customer arrival estimate: T+{eta_minutes} at {arrival_clock} "
        "store local time"
    )

    return {
        "band": band,
        "bay_id": bay_id,
        "handoff_mode": handoff_mode,
        "stage_at_minutes": stage_at_minutes,
        "stage_at_clock": stage_at_clock,
        "arrival_clock": arrival_clock,
        "pick_minutes": pick_minutes,
        "conditions_source": conditions_source,
        "note": note,
        "bay_details": selected_bay,
        **guidance,
        "lines": lines,
    }


def _print_lines(lines):
    print("\n".join(lines))
    print("-" * 36)


def _non_negative_int(value):
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return parsed


def main(argv):
    parser = argparse.ArgumentParser(
        description=(
            "Calculate a deterministic BlastBox Curb Delivery staging plan. "
            "All weather inputs are Metric: Celsius, km/h, and percent."
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)
    stage = sub.add_parser(
        "stage",
        help="Calculate the conditions band, bay, and staging time.",
        description=(
            "Calculate a Curb Delivery staging plan. Weather values must use "
            "Metric units: Celsius, km/h, and percent."
        ),
    )
    stage.add_argument("--eta-minutes", type=_non_negative_int, required=True)
    stage.add_argument(
        "--item-count",
        type=_non_negative_int,
        required=True,
        help="Total physical units (sum of order quantities), not product lines.",
    )
    stage.add_argument(
        "--store",
        required=True,
        help="Pickup store city and state returned by Curb Delivery MCP.",
    )
    stage.add_argument(
        "--store-timezone",
        required=True,
        help="IANA timezone_id returned by Curb Delivery MCP.",
    )
    stage.add_argument(
        "--bays-json",
        required=True,
        help="Exact JSON object returned by Curb Delivery MCP list_bays.",
    )
    stage.add_argument("--cap", required=True, help="Weather caption.")
    stage.add_argument("--wx", default="", help="Weather code reinforcement.")
    stage.add_argument("--temp", type=float, required=True, help="Temperature in C.")
    stage.add_argument(
        "--feels", type=float, required=True, help="Feels-like temperature in C."
    )
    stage.add_argument(
        "--wind-spd", type=float, required=True, help="Wind speed in km/h."
    )
    stage.add_argument(
        "--wind-gust", type=float, required=True, help="Wind gust in km/h."
    )
    stage.add_argument(
        "--wind-dir", type=float, required=True, help="Wind-from direction in degrees."
    )
    stage.add_argument(
        "--rain-chance", type=float, required=True, help="Rain chance in percent."
    )
    stage.add_argument(
        "--now",
        required=True,
        help="Timezone-aware ISO-8601 current time with UTC offset.",
    )
    sunset = stage.add_mutually_exclusive_group(required=True)
    sunset.add_argument(
        "--sunset",
        help="Timezone-aware ISO-8601 store-local sunset with UTC offset.",
    )
    sunset.add_argument(
        "--sunset-local",
        help="Fallback local sunset time from Curb Delivery MCP (HH:MM).",
    )
    stage.add_argument("--tier-code", default="standard")
    stage.add_argument(
        "--conditions-source", choices=("live", "fallback"), required=True
    )

    args = parser.parse_args(argv[1:])
    try:
        bays, occupancy = parse_bays_json(
            args.bays_json, args.store, args.store_timezone
        )
        result = compute_staging(
            eta_minutes=args.eta_minutes,
            item_count=args.item_count,
            cap=args.cap,
            wx=args.wx,
            temp=args.temp,
            feels=args.feels,
            wind_spd=args.wind_spd,
            wind_gust=args.wind_gust,
            wind_dir=args.wind_dir,
            rain_chance=args.rain_chance,
            now_iso=args.now,
            store_timezone=args.store_timezone,
            sunset_iso=args.sunset,
            sunset_local=args.sunset_local,
            bays=bays,
            occupancy=occupancy,
            tier_code=args.tier_code,
            conditions_source=args.conditions_source,
        )
    except ValueError as exc:
        parser.error(str(exc))

    _print_lines(result["lines"])
    bay_text = "NONE" if result["bay_id"] is None else result["bay_id"]
    print(
        f"STAGE AT: {result['stage_at_clock']} "
        f"(T+{result['stage_at_minutes']}) | BAY {bay_text} | "
        f"{result['handoff_mode']} | band={result['band']} | "
        f"source={result['conditions_source']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
