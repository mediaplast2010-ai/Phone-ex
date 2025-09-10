# app.py
# Phone Extractor UA — з підтримкою кліків на "Показати телефон", "Показать номер"

import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urlparse

st.set_page_config(page_title="📞 Phone Extractor Pro", layout="centered")
st.title("📞 Phone Extractor Pro")
st.markdown("🔍 Знаходить телефони, навіть якщо вони приховані за кнопками")

# --- Вибір режиму ---
mode = st.radio(
    "Режим роботи",
    ["🟢 Звичайний режим (requests)", "🟡 Режим з кліками (Selenium)"],
    help="Використовуйте Selenium, якщо телефони з'являються після кліку"
)

urls_input = st.text_area(
    "Список сайтів",
    placeholder="https://okna.ua\nhttps://budzmo.ua",
    height=150
)

# Налаштування
delay = st.sidebar.slider("Затримка між сайтами (сек)", 1, 10, 3)
show_raw = st.sidebar.checkbox("Показувати сирі дані")

if st.button("🔍 Знайти телефони"):
    if not urls_input.strip():
        st.warning("Будь ласка, введіть хоча б один URL")
    else:
        url_list = [url.strip() for url in urls_input.splitlines() if url.strip()]
        all_phones = {}
        failed_sites = []

        if mode == "🟢 Звичайний режим (requests)":
            # === Звичайний режим ===
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html',
                'Accept-Language': 'uk',
            }

            for url in url_list:
                if not url.startswith("http"):
                    url = "https://" + url

                try:
                    response = requests.get(url, headers=headers, timeout=15)
                    response.raise_for_status()
                    response.encoding = response.apparent_encoding
                    soup = BeautifulSoup(response.text, 'html.parser')
                    text = soup.get_text() + str(soup)

                    phones = set()

                    # Пошук у tel: посиланнях
                    tel_links = soup.find_all(href=lambda x: x and x.startswith("tel:"))
                    for link in tel_links:
                        tel = link['href'].replace("tel:", "").strip()
                        digits = re.sub(r'[^\d]', '', tel)
                        if len(digits) == 12 and digits.startswith('380'):
                            phones.add('+' + digits)
                        elif len(digits) == 10 and digits.startswith('0'):
                            phones.add('+38' + digits)
                        elif len(digits) == 9 and digits.startswith('800'):
                            phones.add('+380' + digits)
                        elif len(digits) == 9 and digits.startswith('0'):
                            phones.add('+380' + digits)

                    # Пошук у тексті
                    patterns = [
                        r'\+?38\s*\(?\d{3}\)?\s*\d{3}[-.\s]?\d{2}[-.\s]?\d{2}',
                        r'0\s*\(?\d{2,3}\)?\s*\d{3}[-.\s]?\d{2}[-.\s]?\d{2}',
                        r'800[-.\s]?\d{3}[-.\s]?\d{3}',
                    ]
                    for pattern in patterns:
                        matches = re.finditer(pattern, text, re.IGNORECASE)
                        for match in matches:
                            full = match.group(0)
                            digits = re.sub(r'[^\d]', '', full)
                            if len(digits) == 12 and digits.startswith('380'):
                                phones.add('+' + digits)
                            elif len(digits) == 10 and digits.startswith('0'):
                                phones.add('+38' + digits)
                            elif len(digits) == 9 and digits.startswith('800'):
                                phones.add('+380' + digits)

                    phones = sorted(phones)
                    domain = urlparse(url).netloc
                    all_phones[domain] = phones

                    if show_raw:
                        with st.expander(f"📄 Сирі дані: {domain}"):
                            st.text_area("HTML", response.text[:2000], height=200, key=f"raw_{url}")

                except Exception as e:
                    failed_sites.append(f"{url} — {str(e)}")

                time.sleep(delay)

        else:
            # === Режим з кліками (Selenium) ===
            with st.spinner("Підготовка браузера..."):
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

                try:
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                except Exception as e:
                    st.error(f"❌ Не вдалося запустити Chrome: {e}")
                    st.stop()

            CLICK_TEXTS = [
                "Показати телефон", "показати телефон",
                "Показать телефон", "показать телефон",
                "Показати номер", "показати номер",
                "Показать номер", "показать номер",
                "Дивитися номер", "Смотреть номер",
                "Показати контакти", "Показать контакты"
            ]

            for url in url_list:
                if not url.startswith("http"):
                    url = "https://" + url

                try:
                    driver.get(url)
                    time.sleep(3)

                    # Клікаємо на всі кнопки
                    for text in CLICK_TEXTS:
                        try:
                            buttons = driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
                            for btn in buttons:
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                driver.execute_script("arguments[0].click();", btn)
                                time.sleep(1.5)
                        except:
                            continue

                    time.sleep(3)
                    html = driver.page_source
                    soup = BeautifulSoup(html, 'html.parser')
                    text = soup.get_text() + html

                    phones = set()
                    # (аналогічний пошук, як вище)
                    tel_links = soup.find_all(href=lambda x: x and x.startswith("tel:"))
                    for link in tel_links:
                        tel = link['href'].replace("tel:", "").strip()
                        digits = re.sub(r'[^\d]', '', tel)
                        if len(digits) == 12 and digits.startswith('380'):
                            phones.add('+' + digits)
                        elif len(digits) == 10 and digits.startswith('0'):
                            phones.add('+38' + digits)
                        elif len(digits) == 9 and digits.startswith('800'):
                            phones.add('+380' + digits)

                    # Пошук за патернами
                    patterns = [r'\+?38\s*\(?\d{3}\)?\s*\d{3}[-.\s]?\d{2}[-.\s]?\d{2}', r'800[-.\s]?\d{3}[-.\s]?\d{3}']
                    for pattern in patterns:
                        matches = re.finditer(pattern, text, re.IGNORECASE)
                        for match in matches:
                            full = match.group(0)
                            digits = re.sub(r'[^\d]', '', full)
                            if len(digits) == 12 and digits.startswith('380'):
                                phones.add('+' + digits)
                            elif len(digits) == 9 and digits.startswith('800'):
                                phones.add('+380' + digits)

                    phones = sorted(phones)
                    domain = urlparse(url).netloc
                    all_phones[domain] = phones

                    if show_raw:
                        with st.expander(f"📄 Сирі дані (Selenium): {domain}"):
                            st.text_area("HTML", html[:2000], height=200, key=f"selenium_{url}")

                except Exception as e:
                    failed_sites.append(f"{url} — {str(e)}")

                time.sleep(delay)

            driver.quit()

        # === Вивід результатів ===
        if all_phones:
            st.success("📞 Знайдені телефони:")
            full_output = ""
            for domain, phones in all_phones.items():
                if phones:
                    st.markdown(f"### 🌐 `{domain}`")
                    for phone in phones:
                        st.code(phone)
                    full_output += f"{domain}\n" + "\n".join(phones) + "\n\n"
                else:
                    st.info(f"ℹ️ На `{domain}` телефони не знайдено")
                    full_output += f"{domain}\n(не знайдено)\n\n"

            st.download_button(
                label="⬇️ Завантажити всі результати",
                data=full_output.strip(),
                file_name="phones_extracted.txt",
                mime="text/plain"
            )
        else:
            st.warning("❌ Телефони не знайдено на жодному сайті.")

        if failed_sites:
            st.error("❌ Помилки:")
            for fail in failed_sites:
                st.markdown(f"- `{fail}`")

st.markdown("---")
st.markdown(
    "💡 <small>Режим з кліками потрібен, якщо телефони приховані за кнопками. Працює локально.</small>",
    unsafe_allow_html=True
)if __name__ == '__main__':
    import os
    os.system('streamlit run app.py --server.address=0.0.0.0 --server.port=$PORT')