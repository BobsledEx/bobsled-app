import datetime as dt
from collections import defaultdict
import requests
from config import HUBSPOT_KEY_OR, HUBSPOT_KEY_NM

BASE = "https://api.hubapi.com"
EXPECTED_REPS = {
    "OR": ["Andy Conrad", "Doug Fadich", "James Notman", "Kyle Giltz"],
    "NM": ["Savannah Jacobs"],
}
BRAND_AMBASSADOR = "MaryGrace Francone"
VENDOR_PROPERTIES = [
    "event_date", "black_carts", "blendz_cart", "cured_carts", "live_cart",
    "cured_resin_1g", "cured_resin_2g", "live_resin_1g", "live_resin_2g",
    "tincture", "total_units_sold", "hubspot_owner_id"
]

def _headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def _request(method, url, token, **kwargs):
    r = requests.request(method, url, headers=_headers(token), timeout=45, **kwargs)
    if not r.ok:
        raise RuntimeError(f"HubSpot {r.status_code}: {r.text[:1000]}")
    return r.json()

def _search_all(token, object_type, filters, properties):
    url = f"{BASE}/crm/v3/objects/{object_type}/search"
    results, after = [], None
    while True:
        body = {"filterGroups": [{"filters": filters}], "properties": properties, "limit": 100}
        if after:
            body["after"] = after
        data = _request("POST", url, token, json=body)
        results.extend(data.get("results", []))
        after = data.get("paging", {}).get("next", {}).get("after")
        if not after:
            return results

def _owners(token):
    url = f"{BASE}/crm/v3/owners/"
    output, after = [], None
    while True:
        params = {"limit": 500, "archived": "false"}
        if after:
            params["after"] = after
        data = _request("GET", url, token, params=params)
        output.extend(data.get("results", []))
        after = data.get("paging", {}).get("next", {}).get("after")
        if not after:
            break
    return {
        str(x["id"]): (f"{x.get('firstName', '')} {x.get('lastName', '')}".strip()
                       or x.get("email") or str(x["id"]))
        for x in output
    }

def _normalize(value):
    return " ".join(str(value or "").strip().lower().split())

def _as_int(value):
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0

def _ms(value):
    return str(int(value.timestamp() * 1000))

def fetch_hubspot_data(region, start_dt, end_dt):
    token = HUBSPOT_KEY_OR if region == "OR" else HUBSPOT_KEY_NM
    if not token:
        raise RuntimeError(f"Missing HubSpot token for {region}")

    owner_names = _owners(token)
    allowed = {_normalize(name): name for name in EXPECTED_REPS[region]}
    start_ms, end_ms = _ms(start_dt), _ms(end_dt)
    activity = defaultdict(lambda: {"calls": 0, "meetings": 0})

    date_filters = [
        {"propertyName": "hs_timestamp", "operator": "GTE", "value": start_ms},
        {"propertyName": "hs_timestamp", "operator": "LT", "value": end_ms},
    ]

    calls = _search_all(token, "calls", date_filters, ["hubspot_owner_id", "hs_timestamp"])
    for item in calls:
        owner_id = str(item.get("properties", {}).get("hubspot_owner_id") or "")
        owner_name = owner_names.get(owner_id, owner_id)
        key = _normalize(owner_name)
        if key in allowed:
            activity[allowed[key]]["calls"] += 1

    meeting_filters = date_filters
    meetings = _search_all(
        token, "meetings", meeting_filters,
        ["hubspot_owner_id", "hs_timestamp", "hs_meeting_outcome"]
    )
    for item in meetings:
        owner_id = str(item.get("properties", {}).get("hubspot_owner_id") or "")
        owner_name = owner_names.get(owner_id, owner_id)
        key = _normalize(owner_name)
        if key in allowed:
            activity[allowed[key]]["meetings"] += 1

    reps = [
        {"name": name, "calls": activity[name]["calls"], "meetings": activity[name]["meetings"]}
        for name in EXPECTED_REPS[region]
    ]

    vendor = None
    if region == "OR":
        start_day = dt.datetime.combine(start_dt.date(), dt.time.min, tzinfo=dt.timezone.utc)
        end_day = dt.datetime.combine(end_dt.date(), dt.time.min, tzinfo=dt.timezone.utc)
        ticket_filters = [
            {"propertyName": "event_date", "operator": "GTE", "value": _ms(start_day)},
            {"propertyName": "event_date", "operator": "LT", "value": _ms(end_day)},
        ]
        tickets = _search_all(token, "tickets", ticket_filters, VENDOR_PROPERTIES)

        marygrace_tickets = []
        for item in tickets:
            owner_id = str(item.get("properties", {}).get("hubspot_owner_id") or "")
            if _normalize(owner_names.get(owner_id, owner_id)) == _normalize(BRAND_AMBASSADOR):
                marygrace_tickets.append(item)

        vendor = {
            "name": BRAND_AMBASSADOR,
            "vendor_days": len(marygrace_tickets),
            "carts": 0,
            "dabs": 0,
            "tinctures": 0,
            "total_units": 0,
            "calculated_units": 0,
            "difference": 0,
        }
        for item in marygrace_tickets:
            p = item.get("properties", {})
            carts = sum(_as_int(p.get(k)) for k in [
                "black_carts", "blendz_cart", "cured_carts", "live_cart"
            ])
            dabs = sum(_as_int(p.get(k)) for k in [
                "cured_resin_1g", "cured_resin_2g", "live_resin_1g", "live_resin_2g"
            ])
            tinctures = _as_int(p.get("tincture"))
            calculated = carts + dabs + tinctures
            entered = _as_int(p.get("total_units_sold"))
            vendor["carts"] += carts
            vendor["dabs"] += dabs
            vendor["tinctures"] += tinctures
            vendor["calculated_units"] += calculated
            vendor["total_units"] += entered if entered else calculated
        vendor["difference"] = vendor["total_units"] - vendor["calculated_units"]

    return {
        "region": region,
        "reps": reps,
        "vendor": vendor,
        "call_records_examined": len(calls),
        "meeting_records_examined": len(meetings),
    }
