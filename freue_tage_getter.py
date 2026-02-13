import requests

def get_austrian_holidays(year: int):
    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/AT"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


holidays_2026 = get_austrian_holidays(2026)

for h in holidays_2026:
    print(h["date"], "-", h["localName"])