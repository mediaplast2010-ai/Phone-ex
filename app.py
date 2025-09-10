# app.py — сумісний з Streamlit Cloud
import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse

st.set_page_config(page_title="📞 Phone Extractor UA", layout="centered")
st.title("📞 Phone Extractor UA")
st.markdown("🔍 Знаходить телефони на українських сайтах")

urls_input = st.text_area(
    "Список сайтів",
    placeholder="https://zrada.com.ua\nhttps://prom.ua",
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        for url in url_list:
            if not url.startswith("http"):
                url = "https://" + url

            try:
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                response.encoding = response.apparent_encoding
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text()

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

                # Пошук у тексті
                patterns = [
                    r'\+?38\s*\(?\d{3}\)?\s*\d{3}[-.\s]?\d{2}[-.\s]?\d{2}',
                    r'800[-.\s]?\d{3}[-.\s]?\d{3}',
                ]
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
                domain = urlparse(url).netloc.replace("www.", "")
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
                file_name="phones.txt",
                mime="text/plain"
            )
        else:
            st.warning("❌ Телефони не знайдено.")

        if failed_sites:
            st.error("❌ Помилки:")
            for fail in failed_sites:
                st.markdown(f"- `{fail}`")

st.markdown("---")
st.markdown("💡 <small>Працює на простих сайтах. Не підтримує кліки.</small>", unsafe_allow_html=True)