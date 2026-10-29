import datetime as dt
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin
import requests
from config import LEAFLINK_API_KEY

COMPANY_OR = 10270
COMPANY_NM = 25354
URL = "https://app.leaflink.com/api/v2/orders-received/"
MAX_PAGES = 250


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
    text = str(value)
    try:
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return dt.date.fromisoformat(text[:10])
        except ValueError:
            return None


def _seller_id(order):
    seller = order.get("seller")
    return seller.get("id") if isinstance(seller, dict) else seller


def _status(order):
    value = order.get("status") or order.get("order_status") or ""
    if isinstance(value, dict):
        value = value.get("name") or value.get("slug") or value.get("status") or ""
    return str(value).strip().lower()


def _is_paid(order):
    value = order.get("paid")
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _orders_recent(start_date):
    """Fetch recently modified orders instead of the entire LeafLink history."""
    if not LEAFLINK_API_KEY:
        raise RuntimeError("Missing LEAFLINK_API_KEY")

    headers = {
        "Authorization": f"Token {LEAFLINK_API_KEY}",
        "Accept": "application/json",
    }
    params = {
        "page_size": 100,
        "modified__gte": start_date.isoformat(),
    }

    url = URL
    output = []
    seen_urls = set()
    page = 0

    while url:
        page += 1
        if page > MAX_PAGES:
            raise RuntimeError(f"LeafLink pagination exceeded {MAX_PAGES} pages; stopping safely.")
        if url in seen_urls:
            raise RuntimeError("LeafLink pagination repeated the same URL; stopping safely.")
        seen_urls.add(url)

        print(f"LeafLink page {page}: fetching...")
        response = requests.get(url, headers=headers, params=params, timeout=60)
        if not response.ok:
            raise RuntimeError(f"LeafLink {response.status_code}: {response.text[:1000]}")

        data = response.json()
        page_results = data.get("results", [])
        output.extend(page_results)
        print(f"LeafLink page {page}: {len(page_results)} orders; {len(output)} total so far.")

        next_url = data.get("next")
        url = urljoin(URL, next_url) if next_url else None
        params = None

    print(f"LeafLink fetch finished after {page} page(s), {len(output)} order(s).")
    return output


def _summary(orders, start_date, end_date):
    completed_orders = 0
    completed_sales = Decimal("0")
    collected = Decimal("0")

    for order in orders:
        ship_date = _parse_date(order.get("ship_date"))
        if (
            _status(order) in {"complete", "completed"}
            and ship_date
            and start_date <= ship_date < end_date
        ):
            completed_orders += 1
            completed_sales += _decimal(order.get("total"))

        paid_date = _parse_date(order.get("paid_date"))
        if _is_paid(order) and paid_date and start_date <= paid_date < end_date:
            collected += _decimal(order.get("total"))

    return {
        "completed_orders": completed_orders,
        "completed_sales": completed_sales,
        "collected_orders": collected,
        "notes": [],
    }


def fetch_leaflink_data(start_dt, end_dt):
    start_date = start_dt.date()
    end_date = end_dt.date()

    orders = _orders_recent(start_date)
    orders_or = [order for order in orders if _seller_id(order) == COMPANY_OR]
    orders_nm = [order for order in orders if _seller_id(order) == COMPANY_NM]

    print(f"LeafLink state split: Oregon={len(orders_or)}, New Mexico={len(orders_nm)}")
    return (
        _summary(orders_or, start_date, end_date),
        _summary(orders_nm, start_date, end_date),
    )
