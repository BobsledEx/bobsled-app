import os

HUBSPOT_KEY_OR = os.getenv("HUBSPOT_KEY_OR") or os.getenv("HUBSPOT_API_KEY_OR")
HUBSPOT_KEY_NM = os.getenv("HUBSPOT_KEY_NM") or os.getenv("HUBSPOT_API_KEY_NM")
LEAFLINK_API_KEY = os.getenv("LEAFLINK_API_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

EMAIL_FROM = os.getenv("EMAIL_FROM", "reports@bobsledextracts.com")
EMAIL_TO = os.getenv("EMAIL_TO", "crystal@bobsledextracts.com")
REPORT_TIMEZONE = os.getenv("REPORT_TIMEZONE", "America/Los_Angeles")
DRY_RUN = os.getenv("DRY_RUN", "true").strip().lower() not in {"false", "0", "no"}
