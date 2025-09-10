# scraper.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import csv
import os

# Список міст (можна розширити)
CITIES = [
    "kiev", "lviv", "odessa", "kharkiv", "dnipro", "vinnytsia", "zhytomyr",
    "zaporizhzhia", "ivano-frankivsk", "ternopil", "poltava", "rovno",
    "sumy", "khmelnytskyi", "cherkasy", "chernivtsi", "chernihiv", "lutsk"
]

OUTPUT_FILE = "results.csv"

def create_driver():
    options = Options()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless")  # Розкоментуй, щоб приховати браузер
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def extract_phones_from_page(driver, city):
    phones = set()
    try:
        # Прокрутка до кінця (підвантаження)
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Клікаємо на всі "Показати телефон"
        buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'Показати телефон') or contains(text(), 'Показать телефон')]")
        print(f"🔧 Клікаємо на {len(buttons)} кнопок у місті {city}")
        for btn in buttons:
            try:
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.2)
            except:
                continue

        time.sleep(2)

        # Збираємо всі телефони
        tel_links = driver.find_elements(By.XPATH, "//a[starts-with(@href, 'tel:')]")
        for link in tel_links:
            phone = link.get_attribute("href").replace("tel:", "").strip()
            if phone.startswith("380") or phone.startswith("0"):
                if phone.startswith("0") and len(phone) == 10:
                    phone = "38" + phone
                elif phone.startswith("0") and len(phone) == 9:
                    phone = "380" + phone
                phone = "+" + phone
            phones.add(phone)

    except Exception as e:
        print(f"Помилка при обробці сторінки: {e}")

    return phones

def run_scraper():
    driver = create_driver()
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Місто", "Телефон"])

        for city in CITIES:
            url = f"https://okna.ua/{city}/montazhniki"
            print(f"🌐 Відкриваємо: {url}")
            try:
                driver.get(url)
                time.sleep(5)  # Час на завантаження

                phones = extract_phones_from_page(driver, city)
                for phone in phones:
                    writer.writerow([city, phone])
                print(f"✅ {city}: знайдено {len(phones)} телефонів")

            except Exception as e:
                print(f"❌ Помилка з {city}: {e}")

            time.sleep(2)

    driver.quit()
    print(f"\n🎉 Готово! Усі телефони збережено в {OUTPUT_FILE}")