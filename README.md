# SMS verification statistics

Which apps and services send the most SMS verification codes, from which countries and at what time of day. The figures are counts of the SMS received by the public temporary phone numbers on [tempsmss.com](https://tempsmss.com/), published monthly as CSV.

The live version, recalculated every six hours, is at **https://tempsmss.com/sms-verification-statistics/**.

## Latest snapshot

<!-- latest:start -->
<!-- latest:end -->

## Files

All files are UTF-8 CSV with a header row. Every snapshot adds rows to each file. Each row carries the 30-day window it describes (`period_start`, `period_end`, ISO 8601, UTC).

| File | One row is | Columns |
|---|---|---|
| [`data/summary.csv`](data/summary.csv) | one snapshot | `sms`, `sms_previous_30d`, `change_pct`, `numbers`, `countries`, `apps_identified`, `top_app`, `top_app_sms`, `top_app_share_pct` |
| [`data/apps.csv`](data/apps.csv) | one of the 25 apps that sent the most SMS | `rank`, `app`, `sms`, `share_pct`, `sms_previous_30d`, `numbers` |
| [`data/countries.csv`](data/countries.csv) | one country | `country`, `sms`, `share_pct`, `sms_previous_30d`, `numbers` |
| [`data/country_apps.csv`](data/country_apps.csv) | one of the 8 busiest apps in a country | `country`, `rank`, `app`, `sms` |
| [`data/hours.csv`](data/hours.csv) | one hour of the day | `hour_utc` (0–23), `sms`, `share_pct` |
| [`data/latest.json`](data/latest.json) | the newest snapshot as JSON | as published by the site |

- `sms`: SMS received in the 30-day window.
- `sms_previous_30d`: SMS received in the 30 days before the window.
- `share_pct`: percentage of all SMS in the window (not of the 25 apps shown).
- `numbers`: how many different numbers received at least one SMS (from that app, or in that country).
- `change_pct` is left empty when the 30 days before had fewer than 20 SMS.

## How the figures are counted

- **Source:** every SMS received by the public numbers on tempsmss.com in the window, compared with the 30 days before.
- **Apps** are identified by the sender name. When the sender is only a number (a short code or a phone number), the app is read from the text, for example "Your Discord code is…". Generic names such as "Info" or "Verify" are not counted as apps.
- **Left out of the app tables, but included in the totals:** relay services that send other companies' codes under their own name, betting brands, and a few senders the site chooses not to name.
- **Countries** come from the number's country on the site, or from its calling code. A few SMS go to numbers with no country; they are in the totals but not in `countries.csv`, so the country rows can add up to slightly less than `sms`.
- **Only counts are published**, never the codes, the text of the messages or the phone numbers.

## Read these with care

- **The set of numbers changes.** Numbers are added and retired every month (for example, many US and Canadian numbers were added in November 2026). A rise in raw counts can mean more numbers, not more sign-ups. Compare `share_pct` between snapshots, not `sms`.
- **Public numbers attract particular sign-ups.** People use them for accounts they do not want to tie to their own phone. The mix of apps describes that use, not SMS verification in general.
- **Windows overlap at the start.** The first snapshot ends on 23 November 2026. From then on, a snapshot is taken on the 1st of each month.
- **Hours are UTC.**

## Updates

A GitHub Actions workflow ([`.github/workflows/update.yml`](.github/workflows/update.yml)) runs on the 1st of each month. It reads the site's public feed, `https://tempsmss.com/wp-json/tempsmss/v1/sms-stats`, and appends a snapshot with [`scripts/update.py`](scripts/update.py). The script uses only the Python standard library:

```sh
python3 scripts/update.py                # fetch the latest figures and append them
python3 scripts/update.py snapshot.json  # append from a saved copy of the feed
```

## Licence and citation

[CC BY 4.0](LICENSE). You may use, share and adapt the data, also commercially, if you credit the source. Suggested credit:

> TempSMSS SMS verification statistics, https://tempsmss.com/sms-verification-statistics/

Citation metadata is in [`CITATION.cff`](CITATION.cff). Questions or corrections: info@tempsmss.com.
