# app.py
# Онлайн Phone Extractor з масовим введенням сайтів | Українська мова

import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
from time import sleep

# Налаштування сторінки
st.set_page_config(page_title="📞 Phone Extractor Онлайн", layout="centered")

# Заголовок
st.title("📞 Phone Extractor")
st.markdown("Введіть один або кілька URL (по одному на рядок) — знайдемо усі телефонні номери")

# Поле вводу (багаторядкове)
urls_input = st.text_area(
    "Список сайтів",
    placeholder="https://idcompass.com\nhttps://example.com",
    height=150
)

# Кнопка
if st.button("🔍 Знайти телефони"):
    if not urls_input.strip():
        st.warning("Будь ласка, введіть хоча б один URL")
    else:
        # Розділяємо на рядки та очищаємо
        url_list = [url.strip() for url in urls_input.splitlines() if url.strip()]
        total_urls = len(url_list)

        st.info(f"Обробляємо {total_urls} сайтів...")

        all_phones = {}  # словник: сайт → телефони
        failed_sites = []

        progress_bar = st.progress(0)
        status_text = st.empty()

        # Обробка кожного сайту
        for i, url in enumerate(url_list):
            status_text.text(f"Обробляємо: {url}")
            progress_bar.progress((i + 1) / total_urls)

            if not url.startswith("http"):
                url = "https://" + url

            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text()

                # Пошук телефонів
                phone_pattern = r'(\+\d{1,3}[-.\s]?)?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})'
                matches = re.findall(phone_pattern, text)

                phones = set()
                for match in matches:
                    phone = ''.join(match)
                    if f"+{phone}" in text or str(match[0]).startswith('+'):
                        phone = '+' + phone
                    phones.add(phone)

                phones = sorted(phones)

                domain = urlparse(url).netloc or "unknown"
                all_phones[domain] = phones

            except Exception as e:
                failed_sites.append(f"{url} — помилка: {str(e)}")

            sleep(0.5)  # легка затримка, щоб не блокували

        # Підсумок
        status_text.text("Пошук завершено!")
        progress_bar.progress(100)

        # Вивід результатів
        if all_phones:
            st.success("✅ Пошук завершено. Знайдені телефони:")

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

            # Кнопка завантаження
            st.download_button(
                label="⬇️ Завантажити всі результати як .txt",
                data=full_output.strip(),
                file_name="phone_extractor_results.txt",
                mime="text/plain"
            )
        else:
            st.warning("❌ Телефони не знайдено на жодному сайті.")

        if failed_sites:
            st.error("❌ Не вдалося обробити:")
            for fail in failed_sites:
                st.markdown(f"- `{fail}`")

# Футер
st.markdown("---")
st.markdown(
    "💡 <small>Додаток працює без зберігання даних. Не використовуйте для спаму.</small>",
    unsafe_allow_html=True
)
