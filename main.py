import os
import requests
import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# ENV VARS
HUBSPOT_OR = os.getenv("HUBSPOT_API_KEY_OR")
HUBSPOT_NM = os.getenv("HUBSPOT_API_KEY_NM")
SENDGRID_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_TO = os.getenv("EMAIL_TO", "crystal@bobsledextracts.com")

# Date range (last 12 months)
today = datetime.date.today()
one_year_ago = today - datetime.timedelta(days=365)

def get_hubspot_data(api_key, region_name):
    url = "https://api.hubapi.com/crm/v3/objects/contacts"
    params = {
        "hapikey": api_key,
        "limit": 100,
        "properties": "firstname,lastname,email,createdate,lastmodifieddate"
    }

    r = requests.get(url, params=params)
    data = r.json()

    new_accounts = []
    updated_accounts = []

    for item in data.get("results", []):
        created = item.get("properties", {}).get("createdate")
        updated = item.get("properties", {}).get("lastmodifieddate")

        if created:
            created_date = datetime.datetime.fromisoformat(created.replace("Z", "+00:00")).date()
            if created_date >= one_year_ago:
                new_accounts.append(item)

        if updated:
            updated_date = datetime.datetime.fromisoformat(updated.replace("Z", "+00:00")).date()
            if updated_date >= one_year_ago:
                updated_accounts.append(item)

    return {
        "region": region_name,
        "new_accounts": len(new_accounts),
        "updated_accounts": len(updated_accounts)
    }

def build_email(or_data, nm_data):
    html = f"""
    <h2>Bobsled Weekly Report – Last 12 Months</h2>

    <h3>Oregon</h3>
    <p><b>New Accounts:</b> {or_data['new_accounts']}</p>
    <p><b>Updated Accounts:</b> {or_data['updated_accounts']}</p>

    <hr>

    <h3>New Mexico</h3>
    <p><b>New Accounts:</b> {nm_data['new_accounts']}</p>
    <p><b>Updated Accounts:</b> {nm_data['updated_accounts']}</p>

    <br><br>
    <p>This report was generated automatically by your Bobsled HubSpot Bot.</p>
    """

    return html

def send_email(html_content):
    message = Mail(
        from_email="reports@bobsledextracts.com",
        to_emails=EMAIL_TO,
        subject="Bobsled – Weekly HubSpot Report",
        html_content=html_content
    )

    try:
        sg = SendGridAPIClient(SENDGRID_KEY)
        sg.send(message)
        print("Email sent successfully.")
    except Exception as e:
        print("Error sending email:", e)

def main():
    print("Fetching HubSpot data...")

    or_data = get_hubspot_data(HUBSPOT_OR, "Oregon")
    nm_data = get_hubspot_data(HUBSPOT_NM, "New Mexico")

    email_html = build_email(or_data, nm_data)

    print("Sending email...")
    send_email(email_html)

    print("Done.")

if __name__ == "__main__":
    main()
