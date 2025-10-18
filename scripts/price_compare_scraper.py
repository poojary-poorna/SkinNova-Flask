import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import urllib.parse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
}

SITES = {
    "nykaa": "https://www.nykaa.com/search/result?q={query}",
    "amazon": "https://www.amazon.in/s?k={query}",
    "flipkart": "https://www.flipkart.com/search?q={query}"
}

def get_soup(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print("Request failed:", e)
        return None

def parse_nykaa(soup):
    try:
        # Nykaa search result: find first product card
        card = soup.select_one("div.MerchantDesktop-productCard") or soup.select_one("div.product-card")
        if not card:
            card = soup.select_one("div[data-testid='product-card']")
        if not card:
            return None
        link_tag = card.select_one("a")
        product_url = "https://www.nykaa.com" + link_tag.get("href") if link_tag and link_tag.get("href") else None
        img = card.select_one("img")
        img_url = img.get("src") or img.get("data-src") if img else None
        price_tag = card.select_one(".post-card__content-price .price") or card.select_one(".price")
        price_text = price_tag.get_text(strip=True) if price_tag else None
        return product_url, img_url, price_text
    except Exception as e:
        return None

def parse_amazon(soup):
    try:
        card = soup.select_one("div.s-main-slot div[data-component-type='s-search-result']")
        if not card:
            return None
        link = card.select_one("a.a-link-normal.s-no-outline")
        product_url = "https://www.amazon.in" + link.get("href") if link else None
        img = card.select_one("img.s-image")
        img_url = img.get("src") if img else None
        price_whole = card.select_one("span.a-price-whole")
        price_frac = card.select_one("span.a-price-fraction")
        price_text = None
        if price_whole:
            price_text = (price_whole.get_text(strip=True) + (price_frac.get_text(strip=True) if price_frac else ""))
        return product_url, img_url, price_text
    except Exception as e:
        return None

def parse_flipkart(soup):
    try:
        card = soup.select_one("a.s1Q9rs") or soup.select_one("div._1AtVbE")
        if not card:
            card = soup.select_one("div._13oc-S")  # alternative layout
        # Flipkart search layouts vary a lot; try multiple selectors
        link = soup.select_one("a.s1Q9rs") or soup.select_one("a._1fQZEK")
        product_url = "https://www.flipkart.com" + link.get("href") if link else None
        img = soup.select_one("img._396cs4") or soup.select_one("img._2r_T1I")
        img_url = img.get("src") if img else None
        price_tag = soup.select_one("div._30jeq3")
        price_text = price_tag.get_text(strip=True) if price_tag else None
        return product_url, img_url, price_text
    except Exception as e:
        return None

def clean_price(p):
    if not p: return None
    # remove non-digits except dot
    import re
    digits = re.sub(r"[^\d.]", "", p)
    return digits if digits else None

def search_and_parse(site, query):
    url = SITES[site].format(query=urllib.parse.quote(query))
    soup = get_soup(url)
    if not soup:
        return None
    if site == "nykaa":
        return parse_nykaa(soup)
    if site == "amazon":
        return parse_amazon(soup)
    if site == "flipkart":
        return parse_flipkart(soup)
    return None

def main():
    # Expect input CSV 'products.csv' with columns: category,brand,name
    df = pd.read_csv("products.csv")
    out_rows = []
    for idx, row in df.iterrows():
        q = f"{row['brand']} {row['name']}"
        print(f"\nSearching: {q}")
        for site in SITES:
            try:
                res = search_and_parse(site, q)
                if res:
                    product_url, img_url, price_text = res
                    price = clean_price(price_text)
                else:
                    product_url = img_url = price = None
                out_rows.append({
                    "category": row.get("category"),
                    "brand": row.get("brand"),
                    "name": row.get("name"),
                    "site": site,
                    "price": price,
                    "currency": "INR" if price else None,
                    "image_url": img_url,
                    "product_url": product_url
                })
                # polite delay
                time.sleep(random.uniform(1.5, 3.0))
            except Exception as e:
                print("Error for", site, e)
                out_rows.append({
                    "category": row.get("category"),
                    "brand": row.get("brand"),
                    "name": row.get("name"),
                    "site": site,
                    "price": None,
                    "currency": None,
                    "image_url": None,
                    "product_url": None
                })
    out_df = pd.DataFrame(out_rows)
    out_df.to_csv("price_comparison.csv", index=False)
    print("\nSaved price_comparison.csv")

if __name__ == "__main__":
    main()





