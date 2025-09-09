# app.py
# Phone Extractor UA — покращений пошук для okna.ua та подібних

import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse

st.set_page_config(page_title="📞 Phone Extractor UA", layout="centered")
st.title("📞 Phone Extractor UA")
st.markdown("🔍 Шукає телефони на українських сайтах, включаючи `0800`")

urls_input = st.text_area(
    "Список сайтів",
    placeholder="https://okna.ua\nhttps://zrada.com.ua",
    height=150
)

if st.button("🔍 Знайти телефони"):
    if not urls_input.strip():
        st.warning("Будь ласка, введіть хоча б один URL")
    else:
        url_list = [url.strip() for url in urls_input.splitlines() if url.strip()]
        all_phones = {}
        failed_sites = []

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

                phones = set()

                # 1. Пошук у тегах <a href="tel:...">
                tel_links = soup.find_all(href=lambda x: x and x.startswith("tel:"))
                for link in tel_links:
                    tel = link['href'].replace("tel:", "").strip()
                    # Чистимо
                    digits = re.sub(r'[^\d]', '', tel)
                    if len(digits) == 9 and digits.startswith('800'):
                        phone = '+380' + digits
                        phones.add(phone)
                    elif len(digits) == 10 and digits.startswith('0'):
                        phone = '+38' + digits
                        phones.add(phone)
                    elif len(digits) == 12 and digits.startswith('380'):
                        phone = '+' + digits
                        phones.add(phone)
                    elif len(digits) == 9 and digits.startswith('0'):
                        phone = '+380' + digits
                        phones.add(phone)

                # 2. Пошук у тексті (розширені патерни)
                text = soup.get_text()
                patterns = [
                    r'\+38\s*\(?\d{3}\)?\s*\d{3}[-.\s]\d{2}[-.\s]\d{2}',
                    r'380\s*[0-9\s\-()]+',
                    r'0\s*\(?\d{2,3}\)?\s*\d{3}[-.\s]\d{2}[-.\s]\d{2}',
                    r'0\d{2}[-.\s]?\d{3}[-.\s]?\d{2}[-.\s]?\d{2}',
                    r'800\s*\d{3}[-.\s]?\d{3}',
                    r'Телефон[:\s]*[+]?[0-9\s\-()]+',
                    r'Phone[:\s]*[+]?[0-9\s\-()]+',
                ]
                for pattern in patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        full = match.group(0)
                        digits = re.sub(r'[^\d]', '', full)
                        if len(digits) == 9 and digits.startswith('800'):
                            phone = '+380' + digits
                            phones.add(phone)
                        elif len(digits) == 10 and digits.startswith('0'):
                            phone = '+38' + digits
                            phones.add(phone)
                        elif len(digits) == 12 and digits.startswith('380'):
                            phone = '+' + digits
                            phones.add(phone)

                phones = sorted(phones)
                domain = urlparse(url).netloc
                all_phones[domain] = phones

            except Exception as e:
                failed_sites.append(f"{url} — {str(e)}")

        # Вивід
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
                label="⬇️ Завантажити",
                data=full_output.strip(),
                file_name="phones_okna.txt",
                mime="text/plain"
            )
        else:
            st.warning("❌ Телефони не знайдено.")

        if failed_sites:
            st.error("❌ Помилки:")
            for fail in failed_sites:
                st.markdown(f"- `{fail}`")