import requests
import base64
from bs4 import BeautifulSoup
import pandas as pd

#reported to github

NIMBLE_USER = "scraping_engineer_home_test@nimbleway.com"
NIMBLE_PASSWORD = "s8dc7ucb"

# encode and decode back into normal string
CREDENTIALS = base64.b64encode(f"{NIMBLE_USER}:{NIMBLE_PASSWORD}".encode()).decode()

# as documented in nimble authorization page
headers = {
    "Authorization": f"Basic {CREDENTIALS}",
    "Content-Type": "application/json"
}

NIMBLE_API_URL = "https://api.webit.live/api/v1/realtime/web"

# Given search page with applied filters (single-family homes ,monthly rental price between 1000-2000$,zip code 61761 )
SEARCH_URL = "https://www.zillow.com/bloomington-il-61761/rentals/?searchQueryState=%7B%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22north%22%3A40.636718508366414%2C%22south%22%3A40.43345579864026%2C%22east%22%3A-88.85417987207032%2C%22west%22%3A-89.1054921279297%7D%2C%22filterState%22%3A%7B%22fr%22%3A%7B%22value%22%3Atrue%7D%2C%22fsba%22%3A%7B%22value%22%3Afalse%7D%2C%22fsbo%22%3A%7B%22value%22%3Afalse%7D%2C%22nc%22%3A%7B%22value%22%3Afalse%7D%2C%22cmsn%22%3A%7B%22value%22%3Afalse%7D%2C%22auc%22%3A%7B%22value%22%3Afalse%7D%2C%22fore%22%3A%7B%22value%22%3Afalse%7D%2C%22mp%22%3A%7B%22min%22%3A1000%2C%22max%22%3A2000%7D%2C%22tow%22%3A%7B%22value%22%3Afalse%7D%2C%22mf%22%3A%7B%22value%22%3Afalse%7D%2C%22con%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22apa%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse%7D%2C%22apco%22%3A%7B%22value%22%3Afalse%7D%2C%22r4r%22%3A%7B%22value%22%3Atrue%7D%7D%2C%22isListVisible%22%3Atrue%2C%22mapZoom%22%3A12%2C%22usersSearchTerm%22%3A%2261761%22%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A85145%2C%22regionType%22%3A7%7D%5D%7D"



def nimble_fetch_html(url):
    payload = {
        "url": url,
        "render": True,
        "format": "json",
        "country": "US",
        "render_flow": [
            {
                "wait": {
                    "delay": 1000,
                    "required": False
                }
            }
        ]

    }
    response = requests.post(NIMBLE_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["html_content"]


def parse_search_page():
    html = nimble_fetch_html(SEARCH_URL)
    soup = BeautifulSoup(html, 'html.parser')
    # print(soup.prettify())
    results_urls = []
    for tag in soup.select('a.property-card-link'):
        href = tag.get("href")
        if href:
            full_url = "https://www.zillow.com" + href if href.startswith("/") else href  # adjust to full path
            results_urls.append(full_url)
    return list(set(results_urls))


def parse_house_page(html):
    soup = BeautifulSoup(html, 'html.parser')

    def get_tag_text(selector):
        tag = soup.select_one(selector)
        return tag.text.strip() if tag else ''

    def get_price():
        price_text = get_tag_text("span[data-testid='price'] span")
        return price_text.split("/")[0].strip() if price_text else ''

    def get_area():
        for li in soup.select("ul li span"):
            text = li.text.strip()
            if "Total interior livable area" in text:
                return text.split(":")[-1].strip().replace(' sqft', '').replace(',', '')

    def get_rooms_num():
        bedrooms, bathrooms, full_bathrooms = 0, 0, 0
        for li in soup.select("ul li span"):
            text = li.text.strip()
            if text.startswith("Bedrooms"):
                bedrooms = text.split(":")[-1].strip()
            elif text.startswith("Bathrooms"):
                bathrooms = int(text.split(":")[-1].strip())
            elif text.startswith("Full bathrooms"):
                full_bathrooms = int(text.split(":")[-1].strip())
        bathrooms_total = bathrooms + full_bathrooms
        return bedrooms, full_bathrooms, bathrooms_total

    rooms = get_rooms_num()

    def get_description():
        article = soup.find("article")
        if article:
            div = article.find("div", class_=lambda c: c and "Text-c11n" in c)
            if div:
                return div.get_text(strip=True)
        return ""

    def get_address():
        return get_tag_text("h1.Text-c11n-8-109-3__sc-aiai24-0").split(",")[0]

    return {
        "Address": get_address(),
        "City": "Normal",
        "State": "Illinois",  # this ziocode is for Illinois and not Michigan as stated in the HE doc
        "Zipcode": "61761",
        "Price monthly": get_price(),
        "Bedrooms": rooms[0],
        "Full Bathrooms": rooms[1],
        "Bathrooms": rooms[2],
        "Area_sqft": get_area(),
        "Description": get_description(),
    }


def main():
    print("Navigating to the search page and extracting all results")
    found_results_urls = parse_search_page()

    data = []
    for url in found_results_urls:
        try:
            print(f"Fetching Result: {url}")
            house_page_html = nimble_fetch_html(url)
            dict = parse_house_page(house_page_html)
            dict["url"] = f'=HYPERLINK("{url}", "{url}")'
            data.append(dict)
        except Exception as e:
            print(f"failed to parse house page {url}: {e}")

    df = pd.DataFrame(data)
    df.to_csv("sample_data_zillow.csv", index=False)


if __name__ == "__main__":
    main()
