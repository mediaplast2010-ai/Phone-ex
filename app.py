# app.py
# Phone Extractor UA — без Selenium, працює на Streamlit Cloud

import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urlparse

st.set_page_config(page_title="📞 Phone Extractor UA", layout="centered")
st.title("📞 Phone Extractor UA")
st.markdown("🔍 Шукає телефони з кодом **+38** та українські формати (044, 067, 095)")

urls_input = st.text_area(
    "Список сайтів",
    placeholder="https://zrada.com.ua\nhttps://prom.ua",
    height=150
)

# Налаштування
st.sidebar.header("Налаштування")
delay = st.sidebar.slider("Затримка між сайтами (сек)", 1, 10, 3)
show_raw = st.sidebar.checkbox("Показувати сирі дані")

if st.button("🔍 Знайти телефони"):
    if not urls_input.strip():
        st.warning("Будь ласка, введіть хоча б один URL")
    else:
        url_list = [url.strip() for url in urls_input.splitlines() if url.strip()]
        total_urls = len(url_list)
        st.info(f"Обробляємо {total_urls} сайтів...")

        all_phones = {}
        failed_sites = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Реалістичний User-Agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'uk,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        # Українські патерни
        ua_patterns = [
            r'\+38\s*\(?\d{3}\)?\s*\d{3}[-.\s]\d{2}[-.\s]\d{2}',  # +38 (044) 123-45-67
            r'\+38\s*[0-9\s\-()]+',                               # +38 044 123 45 67
            r'380\s*[0-9\s\-()]+',                                # 380 44 123 45 67
            r'0\s*\(?\d{2,3}\)?\s*\d{3}[-.\s]\d{2}[-.\s]\d{2}',   # 0 (44) 123-45-67
            r'0\d{2}\s*\d{3}[-.\s]\d{2}[-.\s]\d{2}',              # 044 123-45-67
            r'0\d{2}[-]\d{3}[-]\d{2}[-]\d{2}',                    # 044-123-45-67
            r'0\d{9}',                                            # 0441234567
            r'\(0\d{2}\)\s*\d{3}[-.\s]\d{2}[-.\s]\d{2}',          # (044) 123-45-67
            r'Телефон[:\s]*[+]?[0-9\s\-()]+',                    # "Телефон: 044 123 45 67"
            r'Phone[:\s]*[+]?[0-9\s\-()]+',
        ]

        for i, url in enumerate(url_list):
            status_text.text(f"🌐 Обробляємо: {url}")
            progress_bar.progress((i + 1) / total_urls)

            if not url.startswith("http"):
                url = "https://" + url

            try:
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                response.encoding = response.apparent_encoding  # Важливо для кирилиці

                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text() + str(soup)  # + HTML для пошуку в атрибутах

                phones = set()

                for pattern in ua_patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        full_match = match.group(0)
                        digits = re.sub(r'[^\d]', '', full_match)

                        if len(digits) == 12 and digits.startswith('380'):
                            phone = '+' + digits
                        elif len(digits) == 10 and digits.startswith('0'):
                            phone = '+38' + digits
                        elif len(digits) == 9 and digits.startswith('0'):
                            phone = '+380' + digits
                        else:
                            continue
                        phones.add(phone)

                # Пошук у tel: посиланнях
                tel_links = soup.find_all(href=lambda x: x and x.startswith("tel:"))
                for link in tel_links:
                    tel = link['href'].replace("tel:", "").strip()
                    digits = re.sub(r'[^\d]', '', tel)
                    if len(digits) == 10 and digits.startswith('0'):
                        phone = '+38' + digits
                        phones.add(phone)
                    elif len(digits) == 12 and digits.startswith('380'):
                        phone = '+' + digits
                        phones.add(phone)

                phones = sorted(phones)
                domain = urlparse(url).netloc
                all_phones[domain] = phones

                if show_raw:
                    with st.expander(f"📄 Сирі дані: {domain}"):
                        st.text_area("Відповідь сервера", response.text[:2000], height=200)

            except Exception as e:
                failed_sites.append(f"{url} — {str(e)}")

            time.sleep(delay)  # Не поспішаймо

        status_text.text("✅ Пошук завершено!")
        progress_bar.progress(100)

        # Вивід
        if any(phones for phones in all_phones.values()):
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
                file_name="ua_phones.txt",
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
    "💡 <small>Працює без Selenium. Оптимізовано для українських сайтів. Підходить для Streamlit Cloud.</small>",
    unsafe_allow_html=True
)