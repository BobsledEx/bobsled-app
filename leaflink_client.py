import datetime as dt
from decimal import Decimal, InvalidOperation
import requests
from config import LEAFLINK_API_KEY

COMPANY_OR = 10270
COMPANY_NM = 25354
URL = "https://app.leaflink.com/api/v2/orders-received/"

def _decimal(value):
    if isinstance(value, dict):
        value = value.get("amount")
    try:
        return Decimal(str(value or 0))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")

def _parse_date(value):
    if not value:
        return None
    if isinstance(value, dict):
        value = value.get("date") or value.get("value")
    try:
        return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return dt.date.fromisoformat(str(value)[:10])
        except ValueError:
            return None

def _as_bool(value):
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"true", "1", "yes"}

def _orders_all():
    if not LEAFLINK_API_KEY:
        raise RuntimeError("Missing LEAFLINK_API_KEY")
    headers = {"Authorization": f"Token {LEAFLINK_API_KEY}", "Accept": "application/json"}
    url, params, output = URL, {"page_size": 100}, []
    while url:
        r = requests.get(url, headers=headers, params=params, timeout=60)
        if not r.ok:
            raise RuntimeError(f"LeafLink {r.status_code}: {r.text[:1000]}")
        data = r.json()
        output.extend(data.get("results", []))
        url = data.get("next")
        params = None
    return output

def _seller_id(order):
    seller = order.get("seller")
    value = seller.get("id") if isinstance(seller, dict) else seller
    try:
        return int(value)
    except (TypeError, ValueError):
        return value

def _status(order):
    value = order.get("status") or order.get("order_status") or ""
    if isinstance(value, dict):
        value = value.get("name") or value.get("slug") or value.get("status") or ""
    return str(value).strip().lower()

def _summary(orders, start_date, end_date):
    completed_orders = 0
    completed_sales = Decimal("0")
    collected_orders = 0
    collected = Decimal("0")
    missing_ship_dates = 0

    for order in orders:
        ship_date = _parse_date(order.get("ship_date"))
        is_complete = _status(order) in {"complete", "completed"}
        if is_complete and ship_date and start_date <= ship_date < end_date:
            completed_orders += 1
            completed_sales += _decimal(order.get("total"))
        elif is_complete and not ship_date:
            missing_ship_dates += 1

        paid_date = _parse_date(order.get("paid_date"))
        if _as_bool(order.get("paid")) and paid_date and start_date <= paid_date < end_date:
            collected_orders += 1
            collected += _decimal(order.get("total"))

    notes = []
    if missing_ship_dates:
        notes.append(
            f"{missing_ship_dates} completed order(s) had no ship date and were excluded from the shipped-last-week total."
        )

    return {
        "completed_orders": completed_orders,
        "completed_sales": completed_sales,
        "collected_orders": collected_orders,
        "collected": collected,
        "notes": notes,
    }

def fetch_leaflink_data(start_dt, end_dt):
    orders = _orders_all()
    start_date, end_date = start_dt.date(), end_dt.date()
    orders_or = [o for o in orders if _seller_id(o) == COMPANY_OR]
    orders_nm = [o for o in orders if _seller_id(o) == COMPANY_NM]
    return _summary(orders_or, start_date, end_date), _summary(orders_nm, start_date, end_date)
