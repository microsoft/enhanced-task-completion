import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path


STAGING_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "BlastBoxAgents"
    / "botcomponents"
    / "crf98_curbsidepickupassistant_Q0mRmz.file.blastboxstagingpy_RnlUT"
    / "filedata"
    / "blastbox_staging.py"
)
SPEC = importlib.util.spec_from_file_location("blastbox_staging", STAGING_SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load staging skill from {STAGING_SCRIPT}")
staging = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(staging)


STORE_BAYS = {
    "Springfield, IL": [
        {"bay_id": 1, "covered": True, "lit": True, "facing": 90, "priority": True},
        {"bay_id": 2, "covered": True, "lit": True, "facing": 180, "priority": False},
        {"bay_id": 3, "covered": False, "lit": False, "facing": 270, "priority": False},
    ],
    "Los Angeles, CA": [
        {"bay_id": 1, "covered": False, "lit": True, "facing": 0, "priority": True},
        {"bay_id": 2, "covered": False, "lit": True, "facing": 45, "priority": False},
    ],
    "Seattle, WA": [
        {"bay_id": 1, "covered": False, "lit": True, "facing": 0, "priority": False},
        {"bay_id": 2, "covered": False, "lit": True, "facing": 90, "priority": False},
        {"bay_id": 3, "covered": True, "lit": True, "facing": 180, "priority": True},
        {"bay_id": 4, "covered": False, "lit": False, "facing": 270, "priority": False},
    ],
}

BAY_OCCUPANCY = {
    "Springfield, IL": {"1": None, "2": None, "3": None},
    "Los Angeles, CA": {"1": None, "2": None},
    "Seattle, WA": {"1": None, "2": None, "3": "ORD-10478", "4": None},
}

SPRINGFIELD_BAYS_JSON = (
    '{"location":"Springfield, IL","timezone_id":"America/Chicago","bays":['
    '{"bay_id":1,"covered":true,"lit":true,"facing":90,'
    '"priority":true,"occupied":false,"occupied_by":null},'
    '{"bay_id":2,"covered":true,"lit":true,"facing":180,'
    '"priority":false,"occupied":false,"occupied_by":null},'
    '{"bay_id":3,"covered":false,"lit":false,"facing":270,'
    '"priority":false,"occupied":false,"occupied_by":null}]}'
)


class BandDetectionTests(unittest.TestCase):
    def band(self, **overrides):
        values = {
            "cap": "Clear",
            "wx": "",
            "temp": 20.0,
            "feels": 20.0,
            "wind_gust": 10.0,
            "rain_chance": 0.0,
            "is_dark": False,
        }
        values.update(overrides)
        return staging.detect_band(**values)

    def test_each_band_individually(self):
        self.assertEqual(self.band(cap="Rain showers"), "WET")
        self.assertEqual(self.band(feels=38.0), "HOT")
        self.assertEqual(self.band(temp=2.0), "COLD")
        self.assertEqual(self.band(wind_gust=40.0), "WINDY")
        self.assertEqual(self.band(is_dark=True), "DARK")
        self.assertEqual(self.band(), "BENIGN")

    def test_priority_wet_beats_hot(self):
        self.assertEqual(self.band(cap="Rain", feels=45.0), "WET")

    def test_priority_hot_beats_dark(self):
        self.assertEqual(self.band(feels=38.0, is_dark=True), "HOT")

    def test_feels_boundary(self):
        self.assertEqual(self.band(feels=37.9), "BENIGN")
        self.assertEqual(self.band(feels=38.0), "HOT")

    def test_gust_boundary(self):
        self.assertEqual(self.band(wind_gust=39.9), "BENIGN")
        self.assertEqual(self.band(wind_gust=40.0), "WINDY")

    def test_rain_boundary(self):
        self.assertEqual(self.band(rain_chance=59), "BENIGN")
        self.assertEqual(self.band(rain_chance=60), "WET")

    def test_empty_wx_still_uses_wet_caption(self):
        self.assertEqual(self.band(cap="Light drizzle", wx=""), "WET")

    def test_precipitation_code_triggers_wet(self):
        self.assertEqual(self.band(cap="Cloudy", wx="RA"), "WET")
        self.assertEqual(self.band(cap="Cloudy", wx="TSRA"), "WET")

    def test_dry_storm_caption_is_not_wet(self):
        self.assertEqual(self.band(cap="Sandstorm"), "BENIGN")
        self.assertEqual(self.band(cap="Dust storm"), "BENIGN")


class BaySelectionTests(unittest.TestCase):
    def test_los_angeles_rain_degrades_to_exposed_bay(self):
        result = staging.compute_staging(
            eta_minutes=20,
            item_count=1,
            cap="Rain",
            wx="",
            temp=30,
            feels=35,
            wind_spd=10,
            wind_gust=18,
            wind_dir=315,
            rain_chance=70,
            now_iso="2026-09-02T15:40:00-07:00",
            store_timezone="America/Los_Angeles",
            sunset_iso="2026-09-02T19:05:00-07:00",
            bays=STORE_BAYS["Los Angeles, CA"],
            occupancy=BAY_OCCUPANCY["Los Angeles, CA"],
            tier_code="standard",
            conditions_source="live",
        )
        self.assertEqual(result["band"], "WET")
        self.assertIsNotNone(result["bay_id"])
        self.assertEqual(result["handoff_mode"], "EXPOSED")
        self.assertEqual(
            result["note"],
            "No covered bay available - keep goods indoors until the customer "
            "has stopped, bag before bringing out",
        )
        self.assertIn("available fallback", result["bay_reason"])
        self.assertIn("wet pavement", result["customer_precaution"])

    def test_seattle_wet_occupied_covered_bay_uses_fallback_note(self):
        result = staging.compute_staging(
            eta_minutes=20,
            item_count=1,
            cap="Light rain",
            wx="",
            temp=9,
            feels=6,
            wind_spd=15,
            wind_gust=28,
            wind_dir=225,
            rain_chance=65,
            now_iso="2026-09-02T15:40:00-07:00",
            store_timezone="America/Los_Angeles",
            sunset_iso="2026-09-02T16:25:00-07:00",
            bays=STORE_BAYS["Seattle, WA"],
            occupancy=BAY_OCCUPANCY["Seattle, WA"],
            tier_code="mega",
            conditions_source="live",
        )
        self.assertEqual(result["band"], "WET")
        self.assertEqual(result["bay_id"], 1)
        self.assertEqual(result["handoff_mode"], "EXPOSED")
        self.assertIn("No covered bay available", result["note"])

    def test_mega_and_plus_choose_different_springfield_wet_bays(self):
        args = (
            "WET",
            STORE_BAYS["Springfield, IL"],
            BAY_OCCUPANCY["Springfield, IL"],
            180,
        )
        self.assertEqual(staging.select_bay(*args, "mega")[0], 1)
        self.assertEqual(staging.select_bay(*args, "plus")[0], 2)

    def test_cold_without_cover_has_explicit_exposed_note(self):
        bay_id, mode, note = staging.select_bay(
            "COLD",
            STORE_BAYS["Los Angeles, CA"],
            BAY_OCCUPANCY["Los Angeles, CA"],
            wind_dir=315,
            tier_code="standard",
        )
        self.assertIsNotNone(bay_id)
        self.assertEqual(mode, "EXPOSED")
        self.assertIn("cold conditions", note)

    def test_all_occupied_returns_none(self):
        occupancy = {"1": "A", "2": "B", "3": "C"}
        self.assertEqual(
            staging.select_bay(
                "BENIGN",
                STORE_BAYS["Springfield, IL"],
                occupancy,
                wind_dir=180,
                tier_code="mega",
            ),
            (None, "NONE", "No free bay"),
        )

    def test_leeward_formula(self):
        self.assertTrue(staging.is_leeward(180, 0))
        self.assertFalse(staging.is_leeward(90, 0))


class StagingCalculationTests(unittest.TestCase):
    def compute(self, **overrides):
        values = {
            "eta_minutes": 20,
            "item_count": 3,
            "cap": "Rain showers",
            "wx": "RA",
            "temp": 30.0,
            "feels": 33.0,
            "wind_spd": 12.0,
            "wind_gust": 20.0,
            "wind_dir": 180.0,
            "rain_chance": 70.0,
            "now_iso": "2026-09-02T15:40:00-05:00",
            "store_timezone": "America/Chicago",
            "sunset_iso": "2026-09-02T19:20:00-05:00",
            "bays": STORE_BAYS["Springfield, IL"],
            "occupancy": BAY_OCCUPANCY["Springfield, IL"],
            "tier_code": "mega",
            "conditions_source": "live",
        }
        values.update(overrides)
        return staging.compute_staging(**values)

    def test_corrected_springfield_worked_example(self):
        result = self.compute()
        self.assertEqual(result["band"], "WET")
        self.assertEqual(result["bay_id"], 1)
        self.assertEqual(result["stage_at_minutes"], 15)
        self.assertEqual(result["stage_at_clock"], "15:55")
        self.assertEqual(result["arrival_clock"], "16:00")
        self.assertEqual(result["pick_minutes"], 6.0)
        self.assertTrue(result["bay_details"]["covered"])
        self.assertIn("precipitation risk", result["weather_reason"])
        self.assertIn("weather-protective bagging", result["delivery_instruction"])
        self.assertTrue(
            any(line.startswith("Operational facts:") for line in result["lines"])
        )
        self.assertTrue(
            any(line.startswith("Weather facts:") for line in result["lines"])
        )
        self.assertIn(
            "Conditions source: live (MSN Weather)",
            result["lines"],
        )

    def test_seattle_dst_transition_preserves_current_offset(self):
        result = self.compute(
            eta_minutes=20,
            item_count=1,
            cap="Clear",
            wx="",
            temp=10,
            feels=10,
            wind_gust=10,
            rain_chance=0,
            now_iso="2026-11-01T01:30:00-07:00",
            store_timezone="America/Los_Angeles",
            sunset_iso="2026-11-01T16:45:00-08:00",
        )
        self.assertEqual(result["stage_at_clock"], "01:43")

    def test_seattle_fall_transition_uses_elapsed_time(self):
        result = self.compute(
            eta_minutes=50,
            item_count=1,
            cap="Clear",
            wx="",
            temp=10,
            feels=10,
            wind_gust=10,
            rain_chance=0,
            now_iso="2026-11-01T01:30:00-07:00",
            store_timezone="America/Los_Angeles",
            sunset_iso="2026-11-01T16:45:00-08:00",
        )
        self.assertEqual(result["stage_at_minutes"], 43)
        self.assertEqual(result["stage_at_clock"], "01:13")

    def test_seattle_spring_transition_uses_elapsed_time(self):
        result = self.compute(
            eta_minutes=50,
            item_count=1,
            cap="Clear",
            wx="",
            temp=10,
            feels=10,
            wind_gust=10,
            rain_chance=0,
            now_iso="2026-03-08T01:50:00-08:00",
            store_timezone="America/Los_Angeles",
            sunset_iso="2026-03-08T18:00:00-07:00",
        )
        self.assertEqual(result["stage_at_minutes"], 43)
        self.assertEqual(result["stage_at_clock"], "03:33")

    def test_mega_vs_plus_changes_only_bay_not_band_or_time(self):
        mega = self.compute(tier_code="mega")
        plus = self.compute(tier_code="plus")
        self.assertEqual(mega["bay_id"], 1)
        self.assertEqual(plus["bay_id"], 2)
        self.assertEqual(mega["band"], plus["band"])
        self.assertEqual(mega["stage_at_minutes"], plus["stage_at_minutes"])
        self.assertEqual(mega["stage_at_clock"], plus["stage_at_clock"])

    def test_fallback_source_passes_through(self):
        result = self.compute(conditions_source="fallback")
        self.assertEqual(result["conditions_source"], "fallback")
        self.assertTrue(
            any("typical for this store, not current" in line for line in result["lines"])
        )

    def test_dark_band_returns_lit_bay_precaution(self):
        result = self.compute(
            item_count=1,
            cap="Clear",
            wx="",
            temp=13,
            feels=12,
            wind_gust=20,
            rain_chance=0,
            now_iso="2026-09-02T21:39:00-05:00",
            tier_code="standard",
        )
        self.assertEqual(result["band"], "DARK")
        self.assertTrue(result["bay_details"]["lit"])
        self.assertIn("after sunset", result["weather_reason"])
        self.assertIn("caution", result["customer_precaution"])

    def test_arrival_inside_dark_buffer_selects_lit_bay(self):
        result = self.compute(
            eta_minutes=20,
            item_count=1,
            cap="Clear",
            wx="",
            temp=17,
            feels=17,
            wind_gust=10,
            rain_chance=0,
            now_iso="2026-09-02T18:50:00-05:00",
            sunset_iso="2026-09-02T19:20:00-05:00",
            tier_code="standard",
        )
        self.assertEqual(result["arrival_clock"], "19:10")
        self.assertEqual(result["band"], "DARK")
        self.assertTrue(result["bay_details"]["lit"])
        self.assertIn("near or after sunset", result["weather_reason"])

    def test_short_eta_many_items_clamps_to_zero(self):
        result = self.compute(
            eta_minutes=2,
            item_count=5,
            cap="Clear",
            wx="",
            rain_chance=0,
        )
        self.assertEqual(result["stage_at_minutes"], 0)

    def test_all_occupied_output_has_none_mode(self):
        result = self.compute(
            occupancy={"1": "A", "2": "B", "3": "C"},
        )
        self.assertIsNone(result["bay_id"])
        self.assertEqual(result["handoff_mode"], "NONE")

    def test_timezone_aware_values_are_required(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            self.compute(now_iso="2026-09-02T15:40:00")
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            self.compute(sunset_iso="2026-09-02T19:10:00")

    def test_now_is_converted_to_store_offset_for_clock(self):
        result = self.compute(now_iso="2026-09-02T20:40:00+00:00")
        self.assertEqual(result["stage_at_clock"], "15:55")

    def test_fallback_local_sunset_uses_mcp_offset(self):
        result = self.compute(
            conditions_source="fallback",
            sunset_iso=None,
            sunset_local="19:20",
        )
        self.assertEqual(result["stage_at_clock"], "15:55")

    def test_seattle_fallback_preserves_summer_store_offset(self):
        result = self.compute(
            conditions_source="fallback",
            now_iso="2026-09-02T15:40:00-07:00",
            store_timezone="America/Los_Angeles",
            sunset_iso=None,
            sunset_local="19:45",
        )
        self.assertEqual(result["stage_at_clock"], "15:55")

    def test_exact_result_keys(self):
        self.assertEqual(
            set(self.compute()),
            {
                "band",
                "bay_id",
                "handoff_mode",
                "stage_at_minutes",
                "stage_at_clock",
                "arrival_clock",
                "pick_minutes",
                "conditions_source",
                "note",
                "bay_details",
                "weather_reason",
                "bay_reason",
                "delivery_instruction",
                "customer_precaution",
                "lines",
            },
        )


class McpInputTests(unittest.TestCase):
    def test_bays_json_accepts_full_state_name(self):
        bays, occupancy = staging.parse_bays_json(
            SPRINGFIELD_BAYS_JSON,
            "BlastBox Springfield, Illinois store",
            "America/Chicago",
        )
        self.assertEqual(len(bays), 3)
        self.assertEqual(occupancy, {"1": None, "2": None, "3": None})

    def test_bays_json_rejects_wrong_store(self):
        with self.assertRaisesRegex(ValueError, "must match"):
            staging.parse_bays_json(
                SPRINGFIELD_BAYS_JSON, "Seattle, WA", "America/Los_Angeles"
            )

    def test_bays_json_rejects_bare_array(self):
        with self.assertRaisesRegex(ValueError, "complete list_bays"):
            staging.parse_bays_json("[]", "Springfield, IL", "America/Chicago")

    def test_pacific_fallback_handles_transition_sides(self):
        fallback = staging._PacificFallbackTimezone()
        after_fall = staging.datetime.fromisoformat(
            "2026-11-01T01:30:00-08:00"
        ).astimezone(fallback)
        after_spring = staging.datetime.fromisoformat(
            "2026-03-08T03:30:00-07:00"
        ).astimezone(fallback)
        self.assertEqual(after_fall.strftime("%H:%M %z"), "01:30 -0800")
        self.assertEqual(after_fall.fold, 1)
        self.assertEqual(after_spring.strftime("%H:%M %z"), "03:30 -0700")


class CliTests(unittest.TestCase):
    def test_identical_cli_inputs_produce_byte_identical_output(self):
        script = STAGING_SCRIPT
        command = [
            sys.executable,
            str(script),
            "stage",
            "--eta-minutes",
            "20",
            "--item-count",
            "3",
            "--store",
            "Springfield, IL",
            "--store-timezone",
            "America/Chicago",
            "--bays-json",
            SPRINGFIELD_BAYS_JSON,
            "--cap",
            "Rain showers",
            "--wx",
            "RA",
            "--temp",
            "30",
            "--feels",
            "33",
            "--wind-spd",
            "12",
            "--wind-gust",
            "20",
            "--wind-dir",
            "180",
            "--rain-chance",
            "70",
            "--now",
            "2026-09-02T15:40:00-05:00",
            "--sunset",
            "2026-09-02T19:20:00-05:00",
            "--tier-code",
            "mega",
            "--conditions-source",
            "live",
        ]
        first = subprocess.run(command, check=True, capture_output=True).stdout
        second = subprocess.run(command, check=True, capture_output=True).stdout
        self.assertEqual(first, second)
        self.assertIn(
            b"STAGE AT: 15:55 (T+15) | BAY 1 | COVERED | band=WET | source=live",
            first,
        )

    def test_cli_uses_current_mcp_occupancy(self):
        occupied = SPRINGFIELD_BAYS_JSON.replace(
            '"occupied":false,"occupied_by":null',
            '"occupied":true,"occupied_by":"ORD-OTHER"',
            1,
        )
        command = [
            sys.executable,
            str(STAGING_SCRIPT),
            "stage",
            "--eta-minutes", "20",
            "--item-count", "3",
            "--store", "Springfield, IL",
            "--store-timezone", "America/Chicago",
            "--bays-json", occupied,
            "--cap", "Rain showers",
            "--temp", "30",
            "--feels", "33",
            "--wind-spd", "12",
            "--wind-gust", "20",
            "--wind-dir", "180",
            "--rain-chance", "70",
            "--now", "2026-09-02T15:40:00-05:00",
            "--sunset", "2026-09-02T19:20:00-05:00",
            "--tier-code", "mega",
            "--conditions-source", "live",
        ]
        output = subprocess.run(command, check=True, capture_output=True).stdout
        self.assertIn(b"| BAY 2 | COVERED |", output)

    def test_cli_fallback_uses_store_local_now_offset(self):
        command = [
            sys.executable,
            str(STAGING_SCRIPT),
            "stage",
            "--eta-minutes", "20",
            "--item-count", "3",
            "--store", "Springfield, IL",
            "--store-timezone", "America/Chicago",
            "--bays-json", SPRINGFIELD_BAYS_JSON,
            "--cap", "Rain showers",
            "--temp", "30",
            "--feels", "36",
            "--wind-spd", "12",
            "--wind-gust", "20",
            "--wind-dir", "180",
            "--rain-chance", "70",
            "--now", "2026-09-02T15:40:00-05:00",
            "--sunset-local", "19:20",
            "--tier-code", "mega",
            "--conditions-source", "fallback",
        ]
        output = subprocess.run(command, check=True, capture_output=True).stdout
        self.assertIn(
            b"STAGE AT: 15:55 (T+15) | BAY 1 | COVERED | "
            b"band=WET | source=fallback",
            output,
        )


if __name__ == "__main__":
    unittest.main()
