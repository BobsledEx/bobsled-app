import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
from config import REPORT_TIMEZONE, DRY_RUN
from hubspot_client import fetch_hubspot_data
from leaflink_client import fetch_leaflink_data
from report_generator import generate_report
from email_sender import send_email

def previous_week_window():
    tz = ZoneInfo(REPORT_TIMEZONE)
    now = dt.datetime.now(tz)
    this_monday = (now - dt.timedelta(days=now.weekday())).date()
    start_date = this_monday - dt.timedelta(days=7)
    end_date = this_monday
    start_dt = dt.datetime.combine(start_date, dt.time.min, tzinfo=tz)
    end_dt = dt.datetime.combine(end_date, dt.time.min, tzinfo=tz)
    return start_dt, end_dt
def month_to_date_window(end_dt):
    start_date = end_dt.date().replace(day=1)
    start_dt = dt.datetime.combine(start_date, dt.time.min, tzinfo=end_dt.tzinfo)
    return start_dt, end_dt
def main():
    start_dt, end_dt = previous_week_window()
    mtd_start_dt, mtd_end_dt = month_to_date_window(end_dt)
    print(f"Reporting window: {start_dt.isoformat()} through {end_dt.isoformat()} (exclusive)")

    print("Fetching Oregon HubSpot activity...")
    hubspot_or = fetch_hubspot_data("OR", start_dt, end_dt)
    print("Fetching New Mexico HubSpot activity...")
    hubspot_nm = fetch_hubspot_data("NM", start_dt, end_dt)

    print("Fetching LeafLink data...")
    leaflink_or, leaflink_nm = fetch_leaflink_data(start_dt, end_dt)

    
    print("Fetching month-to-date LeafLink data...")
    mtd_leaflink_or, mtd_leaflink_nm = fetch_leaflink_data(mtd_start_dt, mtd_end_dt)
    html = generate_report(
    hubspot_or,
    hubspot_nm,
    leaflink_or,
    leaflink_nm,
    mtd_leaflink_or,
    mtd_leaflink_nm,
    start_dt,
    end_dt,
)
    preview = Path("report_preview.html")
    preview.write_text(html, encoding="utf-8")
    print(f"Preview written to {preview.resolve()}")

    subject_end = (end_dt - dt.timedelta(days=1)).date()
    subject = f"Bobsled Weekly Sales & Activity Report | {start_dt.date():%b %d} - {subject_end:%b %d, %Y}"

    if DRY_RUN:
        print(html)
        print("DRY_RUN=true, so no email was sent.")
    else:
        send_email(html, subject)
        print("Email sent.")

if __name__ == "__main__":
    main()
