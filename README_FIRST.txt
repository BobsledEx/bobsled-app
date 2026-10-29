Bobsled Weekly Report - corrected test package

IMPORTANT
- This is a test package. Do not replace the production main branch yet.
- DRY_RUN defaults to true. The first Railway deployment will create report_preview.html and will not send an email.
- Keep the existing Railway secret values. No new secret values are required.

REPORTING WINDOW
- Previous Monday through Sunday in America/Los_Angeles.

HUBSPOT
Oregon sales reps shown every week, even with zero activity:
- Andy Conrad
- Doug Fadich
- James Notman
- Kyle Giltz

New Mexico sales rep shown every week, even with zero activity:
- Savannah Jacobs

Oregon Vendor Day tickets are limited to:
- MaryGrace Francone

Vendor Day fields:
- event_date
- black_carts
- blendz_cart
- cured_carts
- live_cart
- cured_resin_1g
- cured_resin_2g
- live_resin_1g
- live_resin_2g
- tincture
- total_units_sold

LEAFLINK
- One API connection is preserved.
- Oregon seller ID: 10270
- New Mexico seller ID: 25354
- Completed sales metric: current status is Complete and ship_date is in the prior week.
- Collections metric: paid is true and paid_date is in the prior week.
- Individual order numbers are not included.

SAFE TEST ORDER
1. Keep your current production files unchanged.
2. Upload these files to a GitHub test branch, not main.
3. Confirm Railway does not auto-deploy the test branch to the production service.
4. Run with DRY_RUN=true.
5. Review Railway logs and report_preview.html.
6. Confirm all five sales reps appear and Oregon Vendor Days show MaryGrace Francone only.
7. Compare LeafLink totals against the LeafLink reports for the same Monday-Sunday dates.
8. Only after totals match, set DRY_RUN=false and manually run one test email.
9. Do not change the Monday schedule until the test email is approved.

EXPECTED RAILWAY VARIABLES
- HUBSPOT_KEY_OR or HUBSPOT_API_KEY_OR
- HUBSPOT_KEY_NM or HUBSPOT_API_KEY_NM
- LEAFLINK_API_KEY
- SENDGRID_API_KEY
Optional:
- EMAIL_FROM
- EMAIL_TO
- REPORT_TIMEZONE
- DRY_RUN
