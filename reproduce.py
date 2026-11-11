"""Rebuild the browser's comparison table from pinned upstream commits."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

BASE = "9794b29e9d59d534a571361f9dd92018a5dc01c2"
PATCH = "ae2546825eeb5cf61c96bcb2b46317a57a9eafa1"
ROOT = Path(__file__).resolve().parent


def fixture(mask):
    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Calendar Recurrence Lab//EN",
        "BEGIN:VEVENT", "UID:hourly@example.invalid", "DTSTAMP:20251201T000000Z",
        "SUMMARY:Hourly meeting", "DTSTART:20251212T090000Z", "DURATION:PT30M",
        "RRULE:FREQ=HOURLY;COUNT=6",
    ]
    for i in range(6):
        if mask & (1 << i):
            lines.append(f"EXDATE:20251212T{9+i:02}0000Z")
    return "\r\n".join(lines + ["END:VEVENT", "END:VCALENDAR", ""])


def measure():
    from datetime import datetime, timezone
    from icalevents.icalevents import events

    start = datetime(2025, 12, 12, 8, tzinfo=timezone.utc)
    end = start.replace(hour=15)
    return [[e.start.strftime("%H:%M") for e in events(
        string_content=fixture(mask), start=start, end=end
    )] for mask in range(64)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["git", "init", "-q", tmp], check=True)
        results = []
        for ref in (BASE, PATCH):
            subprocess.run(["git", "-C", tmp, "fetch", "-q", "--depth=1",
                            "https://github.com/eigenmannmartin/icalevents.git", ref], check=True)
            subprocess.run(["git", "-C", tmp, "checkout", "-q", "--detach", "FETCH_HEAD"], check=True)
            output = subprocess.check_output([sys.executable, __file__, "--measure"],
                                             env={**os.environ, "PYTHONPATH": tmp}, cwd=tmp)
            results.append(json.loads(output))
    rows = []
    for mask in range(64):
        expected = [f"{9+i:02}:00" for i in range(6) if not mask & (1 << i)]
        row = dict(ics=fixture(mask), expected=expected, before=results[0][mask],
                   proposed=results[1][mask])
        if row["proposed"] != expected:
            raise ValueError(f"Unexpected proposed result for selection {mask}")
        rows.append(row)
    table = json.dumps(rows, separators=(",", ":")) + "\n"
    path = ROOT / "cases.json"
    if args.check:
        if table != path.read_text():
            raise SystemExit("Recorded results differ")
        print("Verified all 64 fixtures against both revisions.")
    else:
        path.write_text(table)


if __name__ == "__main__":
    if sys.argv[1:] == ["--measure"]:
        print(json.dumps(measure()))
    else:
        main()
