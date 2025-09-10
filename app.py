# app.py
# Phone Extractor з підтримкою JavaScript, кліків і прокрутки

import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import re
import os
from urllib.parse import urlparse

# Налаштування сторінки
st.set_page_config(page_title="📞 Phone Extractor (JS-сайти)", layout="centered")

st.title("📞 Phone Extractor")
st.markdown("Введіть URL сайту — знайдемо телефони, навіть якщо вони приховані за кліками")

url = st.text_input("URL сайту", placeholder="https://example.com")

# Кнопка
if st.button("🔍 Знайти телефони"):
    if not url:
        st.warning("Будь ласка, введіть URL")
    else:
        if not url.startswith("http"):
            url = "https://" + url

        with st.spinner("Відкриваємо сторінку... (це може зайняти 10–20 секунд)"):
            # Налаштування Chrome для Streamlit
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Без візуального вікна
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")

            driver = None
            try:
                driver = webdriver.Chrome(options=chrome_options)
                driver.get(url)
                st.info("Сторінка завантажена. Прокручуємо та шукаємо кнопки...")

                # Прокрутка до кінця (імітує користувача)
                last_height = driver.execute_script("return document.body.scrollHeight")
                for _ in range(5):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.5)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height

                # Список текстів кнопок, які можуть приховувати телефон
                click_texts = [
                    "показати телефон", "показати номер", "відкрити телефон",
                    "відкрити номер", "показати", "дивитися", "телефон",
                    "номер", "call", "phone", "show", "дзвінок", "написати"
                ]

                st.info("Шукаємо кнопки типу 'Показати телефон'...")
                buttons_clicked = 0

                for text in click_texts:
                    try:
                        buttons = WebDriverWait(driver, 3).until(
                            EC.presence_of_all_elements_located((By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]"))
                        )
                        for btn in buttons:
                            try:
                                if btn.is_displayed() and btn.is_enabled():
                                    driver.execute_script("arguments[0].scrollIntoView();", btn)
                                    time.sleep(0.5)
                                    btn.click()
                                    buttons_clicked += 1
                                    time.sleep(1)
                            except:
                                continue
                    except TimeoutException:
                        continue

                st.success(f"✅ Натиснуто на {buttons_clicked} елементів, що можуть відкривати телефони")

                # Чекаємо завантаження
                time.sleep(3)

                # Отримуємо весь текст сторінки після кліків
                page_text = driver.page_source

                # Шукаємо телефони
                phone_pattern = r'(\+\d{1,3}[-.\s]?)?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})'
                matches = re.findall(phone_pattern, page_text)
                phones = set()
                for match in matches:
                    phone = ''.join(match)
                    if f"+{phone}" in page_text or str(match[0]).startswith('+'):
                        phone = '+' + phone
                    phones.add(phone)

                phones = sorted(phones)

                if phones:
                    st.success(f"✅ Знайдено {len(phones)} телефонів:")
                    for phone in phones:
                        st.code(phone)

                    # Завантаження
                    full_text = '\n'.join(phones)
                    domain = urlparse(url).netloc
                    st.download_button(
                        label="⬇️ Завантажити як .txt",
                        data=full_text,
                        file_name=f"{domain}_phones.txt",
                        mime="text/plain"
                    )
                else:
                    st.info("❌ Телефони не знайдено. Можливо, сайт вимагає авторизації або використовує складний захист.")

            except WebDriverException as e:
                st.error(f"❌ Помилка браузера: {str(e)}")
                st.info("Сайт може блокувати автоматизовані інструменти.")
            except Exception as e:
                st.error(f"❌ Невідома помилка: {str(e)}")
            finally:
                if driver:
                    driver.quit()

# Футер
st.markdown("---")
st.markdown(
    "💡 <small>Додаток імітує реального користувача: клікає, прокручує. Деякі сайти можуть блокувати автоматизацію.</small>",
    unsafe_allow_html=True
)