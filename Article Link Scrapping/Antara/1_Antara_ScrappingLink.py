from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time

# ─── Konfigurasi ──────────────────────────────────────────────────────────────
QUERY  = "ali khamenei tewas"
TARGET = 100

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver


def scrape_page(driver, page_num):
    query_encoded = QUERY.replace(" ", "+")
    url = f"https://www.antaranews.com/search?q={query_encoded}&page={page_num}"

    print(f"\n[Halaman {page_num}] {url}")
    driver.get(url)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "card__post"))
        )
    except Exception:
        print("  ⚠️  Timeout atau tidak ada artikel di halaman ini")
        return []

    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # ── Ambil hanya dari kolom utama, exclude sidebar "Terpopuler" ──────────
    main_col = soup.find("div", class_="wrapper__list__article")
    if not main_col:
        main_col = soup  # fallback jika struktur berubah

    articles = main_col.find_all("div", class_="card__post")

    print(f"  Ditemukan: {len(articles)} artikel")

    data = []
    for article in articles:

        # Judul & Link — ambil dari card__post__title
        title, link = None, None
        title_div = article.find("div", class_="card__post__title")
        if title_div:
            a_tag = title_div.find("a", href=True)
            if a_tag:
                title = a_tag.get_text(strip=True)
                link  = a_tag["href"]

        # Tanggal — ambil dari span di card__post__author-info
        date = None
        author_div = article.find("div", class_="card__post__author-info")
        if author_div:
            span = author_div.find("span")
            if span:
                date = span.get_text(strip=True)

        # Hanya simpan jika judul & link valid dan bukan homepage
        if title and link and link.startswith("https://www.antaranews.com/") and link != "https://www.antaranews.com/":
            data.append({
                "Judul"             : title,
                "Penerbit"          : "Antara News",
                "Link"              : link,
                "Tanggal Published" : date
            })

    print(f"  ✅ Valid: {len(data)} artikel")
    return data


def main():
    driver   = init_driver()
    all_data = []
    page     = 1

    try:
        while len(all_data) < TARGET:
            page_data = scrape_page(driver, page)

            if not page_data:
                print("\n⚠️  Halaman kosong, scraping berhenti.")
                break

            all_data.extend(page_data)
            print(f"Total terkumpul: {len(all_data)} / {TARGET}")

            page += 1
            time.sleep(3)

    finally:
        driver.quit()

    all_data = all_data[:TARGET]
    df = pd.DataFrame(all_data)
    df.to_csv("antara_khamenei_articles.csv", index=False, encoding="utf-8-sig")

    print("\n" + "=" * 50)
    print(f"✅ Total artikel : {len(df)}")
    print(f"✅ File CSV      : antara_khamenei_articles.csv")
    print("=" * 50)
    print(df.head(10).to_string())


if __name__ == "__main__":
    main()
