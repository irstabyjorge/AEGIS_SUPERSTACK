import csv
import re
import urllib.parse
from playwright.sync_api import sync_playwright

NAME_VARIATIONS = [
    "Jorge Paredes",
    "Jorge Paredes Soria",
    "Jorge Francisco Paredes",
    "Francisco Paredes Soria",
    "Hugo Adrian Garcia",
]

RELATIVE_MATCHES = {
    "Logan Garcia",
    "Blanca Paredes",
    "Guadalupe Paredes",
    "Maria Paredes",
}

US_STATES = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY"
]

def parse_age(text: str):
    match = re.search(r"Age\s*(\d+)", text)
    if match:
        return int(match.group(1))
    return None

def scrape():
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for state in US_STATES:
            for name in NAME_VARIATIONS:
                query = urllib.parse.quote(name)
                url = f"https://www.truepeoplesearch.com/results?name={query}&citystatezip={state}"
                page.goto(url)
                page.wait_for_load_state('load')
                cards = page.query_selector_all("div.card")
                for card in cards:
                    age_text = card.inner_text()
                    age = parse_age(age_text)
                    if age is None or not (38 <= age <= 41):
                        continue
                    relative_elems = card.query_selector_all(".relatives a")
                    relatives = [e.inner_text().strip() for e in relative_elems]
                    if RELATIVE_MATCHES.intersection(relatives):
                        name_text = card.query_selector("a[href]").inner_text().strip()
                        address_elem = card.query_selector(".address")
                        address = address_elem.inner_text().strip() if address_elem else ''
                        results.append({
                            'name': name_text,
                            'age': age,
                            'state': state,
                            'address': address,
                            'relatives': ", ".join(relatives),
                            'search_url': url,
                        })
        browser.close()
    return results

def save_to_csv(rows, filename='results.csv'):
    fieldnames = ['name', 'age', 'state', 'address', 'relatives', 'search_url']
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

if __name__ == '__main__':
    data = scrape()
    save_to_csv(data)
    print(f"Saved {len(data)} results to results.csv")
