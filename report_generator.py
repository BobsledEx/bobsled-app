from html import escape
import datetime as dt

def _money(value):
    return f"${float(value):,.2f}"

def _activity_rows(reps):
    return "".join(
        f"<tr><td>{escape(r['name'])}</td><td>{r['calls']}</td><td>{r['meetings']}</td></tr>"
        for r in reps
    )

def _state_section(name, hubspot, leaflink, include_vendor=False):
    vendor_html = ""
    if include_vendor and hubspot.get("vendor") is not None:
        v = hubspot["vendor"]
        check = ""
        if v["difference"]:
            check = (
                f'<p style="color:#a33"><b>Check needed:</b> entered total differs from '
                f'product-field total by {v["difference"]} units.</p>'
            )
        vendor_html = f"""
        <h3>Brand Ambassador Vendor Days: {escape(v['name'])}</h3>
        <ul>
          <li>Vendor days: <b>{v['vendor_days']}</b></li>
          <li>Carts sold: <b>{v['carts']}</b></li>
          <li>Dabs sold: <b>{v['dabs']}</b></li>
          <li>Tinctures sold: <b>{v['tinctures']}</b></li>
          <li>Total units sold: <b>{v['total_units']}</b></li>
        </ul>{check}
        """

    notes = "".join(f"<li>{escape(n)}</li>" for n in leaflink.get("notes", []))
    notes_html = f'<ul style="color:#7a4b00">{notes}</ul>' if notes else ""
    return f"""
    <h2>{name}</h2>
    <h3>HubSpot Sales Team Activity</h3>
    <table><thead><tr><th>Rep</th><th>Calls</th><th>Meetings Logged</th></tr></thead>
    <tbody>{_activity_rows(hubspot['reps'])}</tbody></table>
    {vendor_html}
    <h3>LeafLink</h3>
    <ul>
      <li>Completed orders shipped last week: <b>{leaflink['completed_orders']}</b></li>
      <li>Completed-order sales shipped last week: <b>{_money(leaflink['completed_sales'])}</b></li>
      <li>Orders marked paid last week: <b>{leaflink['collected_orders']}</b></li>
      <li>Payments collected last week: <b>{_money(leaflink['collected_orders'])}</b></li>
    </ul>{notes_html}
    """
def generate_report(
    hubspot_or,
    hubspot_nm,
    leaflink_or,
    leaflink_nm,
    mtd_leaflink_or,
    mtd_leaflink_nm,
    start_dt,
    end_dt,
):
    display_end = (end_dt - dt.timedelta(days=1)).date()
    total_sales = leaflink_or["completed_sales"] + leaflink_nm["completed_sales"]
    total_collected = leaflink_or["collected_orders"] + leaflink_nm["collected_orders"]
    mtd_or_sold = mtd_leaflink_or["sold_sales"]
    mtd_nm_sold = mtd_leaflink_nm["sold_sales"]
    mtd_total_sold = mtd_or_sold + mtd_nm_sold

    mtd_or_completed = mtd_leaflink_or["completed_sales"]
    mtd_nm_completed = mtd_leaflink_nm["completed_sales"]
    mtd_total_completed = mtd_or_completed + mtd_nm_completed
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
      body{{font-family:Arial,sans-serif;color:#222;line-height:1.35;max-width:760px;margin:auto;padding:16px}}
      table{{border-collapse:collapse;width:100%;margin-bottom:18px}}
      th,td{{border:1px solid #ddd;padding:8px;text-align:left}}
      th{{background:#f2f2f2}} h2{{border-bottom:2px solid #333;padding-bottom:4px}}
    </style></head><body>
    <h1>Bobsled Weekly Sales &amp; Activity Report</h1>
    <p><b>Reporting period:</b> {start_dt.date():%B %d, %Y} through {display_end:%B %d, %Y}</p>
    {_state_section('Oregon', hubspot_or, leaflink_or, True)}
    {_state_section('New Mexico', hubspot_nm, leaflink_nm, False)}
    <h2>Month-to-Date Orders Sold</h2>
<ul>
    <li>Oregon orders sold: <b>{_money(mtd_or_sold)}</b></li>
    <li>New Mexico orders sold: <b>{_money(mtd_nm_sold)}</b></li>
    <li>Total orders sold MTD: <b>{_money(mtd_total_sold)}</b></li>
</ul>

<h2>Month-to-Date Completed/Shipped Sales</h2>
<ul>
    <li>Oregon completed/shipped: <b>{_money(mtd_or_completed)}</b></li>
    <li>New Mexico completed/shipped: <b>{_money(mtd_nm_completed)}</b></li>
    <li>Total completed/shipped MTD: <b>{_money(mtd_total_completed)}</b></li>
</ul>
 
    </body></html>"""
