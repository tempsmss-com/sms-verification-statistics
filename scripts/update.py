#!/usr/bin/env python3
"""Append the latest TempSMSS statistics snapshot to the CSV files in data/.

Reads the JSON the statistics page publishes (or a local file given as the
first argument), adds one snapshot to each CSV unless that snapshot's
period_end is already there, writes data/latest.json and refreshes the
"Latest snapshot" block in README.md. Standard library only.

    python3 scripts/update.py                 # fetch from tempsmss.com
    python3 scripts/update.py snapshot.json   # use a saved copy
"""

import csv
import json
import os
import sys
import urllib.request
from datetime import datetime

SOURCE = "https://tempsmss.com/wp-json/tempsmss/v1/sms-stats"
USER_AGENT = "tempsmss-dataset-updater/1.0 (+https://github.com/tempsmss-com/sms-verification-statistics)"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
README = os.path.join(ROOT, "README.md")
START, END = "<!-- latest:start -->", "<!-- latest:end -->"

FILES = {
    "summary.csv": ["period_start", "period_end", "sms", "sms_previous_30d", "change_pct", "numbers",
                    "countries", "apps_identified", "top_app", "top_app_sms", "top_app_share_pct"],
    "apps.csv": ["period_start", "period_end", "rank", "app", "sms", "share_pct", "sms_previous_30d", "numbers"],
    "countries.csv": ["period_start", "period_end", "country", "sms", "share_pct", "sms_previous_30d", "numbers"],
    "country_apps.csv": ["period_start", "period_end", "country", "rank", "app", "sms"],
    "hours.csv": ["period_start", "period_end", "hour_utc", "sms", "share_pct"],
}


def load(argv):
    if len(argv) > 1:
        with open(argv[1], encoding="utf-8") as f:
            return json.load(f)
    req = urllib.request.Request(SOURCE, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


def cell(v):
    """A CSV cell a spreadsheet will not run: text starting like a formula gets a leading apostrophe.
    App names come from SMS sender IDs, which whoever sends the SMS chooses."""
    if isinstance(v, str) and v.startswith(FORMULA_START):
        return "'" + v
    return v


def md(v):
    """Text for a Markdown table cell: no pipes, markup or line breaks."""
    s = " ".join(str(v).split())
    for ch in "\\`*_[]<>|#":
        s = s.replace(ch, "\\" + ch)
    return s


def pct(v):
    return "" if v is None else f"{float(v):.1f}"


def rows_for(s):
    span = [s["period_start"], s["period_end"]]
    top = s["apps"][0] if s["apps"] else {}
    before = s.get("sms_previous_30d") or 0
    change = round((s["sms"] - before) * 100 / before, 1) if before >= 20 else None
    return {
        "summary.csv": [span + [s["sms"], before, pct(change), s["numbers"], s["countries_count"],
                                s["apps_identified"], top.get("app", ""), top.get("sms", ""), pct(top.get("share_pct"))]],
        "apps.csv": [span + [a["rank"], a["app"], a["sms"], pct(a["share_pct"]), a["sms_previous_30d"], a["numbers"]]
                     for a in s["apps"]],
        "countries.csv": [span + [c["country"], c["sms"], pct(c["share_pct"]),
                                  "" if c.get("sms_previous_30d") is None else c["sms_previous_30d"], c["numbers"]]
                          for c in s["countries"]],
        "country_apps.csv": [span + [c["country"], c["rank"], c["app"], c["sms"]] for c in s["country_apps"]],
        "hours.csv": [span + [h["hour_utc"], h["sms"], pct(h["share_pct"])] for h in s["hours"]],
    }


def already_there(period_end):
    path = os.path.join(DATA, "summary.csv")
    if not os.path.exists(path):
        return False
    with open(path, newline="", encoding="utf-8") as f:
        return any(r["period_end"] == period_end for r in csv.DictReader(f))


def append(name, rows):
    path = os.path.join(DATA, name)
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        if new:
            w.writerow(FILES[name])
        w.writerows([[cell(v) for v in row] for row in rows])


def day(iso):
    return datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").strftime("%-d %B %Y")


def latest_block(s):
    top = s["apps"][0]
    lines = [
        START,
        f"In the 30 days to {day(s['period_end'])}, TempSMSS numbers received **{s['sms']:,}** verification SMS "
        f"on {s['numbers']:,} numbers in {s['countries_count']} countries. {s['apps_identified']:,} apps and services "
        f"were identified; {md(top['app'])} sent the most ({top['sms']:,} SMS, {float(top['share_pct']):.1f}%).",
        "",
        "| # | App | SMS | Share |",
        "|---|---|---:|---:|",
    ]
    lines += [f"| {a['rank']} | {md(a['app'])} | {a['sms']:,} | {float(a['share_pct']):.1f}% |" for a in s["apps"][:10]]
    lines += ["", "| Country | SMS | Share | Numbers |", "|---|---:|---:|---:|"]
    lines += [f"| {md(c['country'])} | {c['sms']:,} | {float(c['share_pct']):.1f}% | {c['numbers']:,} |" for c in s["countries"]]
    lines += ["", f"Window: {s['period_start']} to {s['period_end']} (UTC). Full tables in [`data/`](data/).", END]
    return "\n".join(lines)


def refresh_readme(s):
    with open(README, encoding="utf-8") as f:
        text = f.read()
    a, b = text.find(START), text.find(END)
    if a < 0 or b < 0:
        return
    with open(README, "w", encoding="utf-8") as f:
        f.write(text[:a] + latest_block(s) + text[b + len(END):])


def main(argv):
    s = load(argv)
    for key in ("period_start", "period_end", "sms", "apps", "countries", "country_apps", "hours"):
        if key not in s:
            sys.exit(f"snapshot has no '{key}': not the statistics feed?")
    if len(s["hours"]) != 24 or not s["apps"]:
        sys.exit("snapshot looks incomplete (needs 24 hours and at least one app); nothing written")

    os.makedirs(DATA, exist_ok=True)
    if already_there(s["period_end"]):
        print(f"snapshot {s['period_end']} is already in data/summary.csv; nothing to add")
        return
    for name, rows in rows_for(s).items():
        append(name, rows)
    with open(os.path.join(DATA, "latest.json"), "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
        f.write("\n")
    refresh_readme(s)
    print(f"added snapshot {s['period_start']} .. {s['period_end']}: {s['sms']:,} SMS, {len(s['apps'])} apps")


if __name__ == "__main__":
    main(sys.argv)
