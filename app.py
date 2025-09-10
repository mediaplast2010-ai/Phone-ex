# app.py
import streamlit as st
import subprocess
import os

st.set_page_config(page_title="📞 okna.ua Парсер", layout="centered")
st.title("📞 Парсер телефонів з okna.ua")
st.markdown("""
Збирає **всі телефони монтажників** з усіх міст України.
Автоматично клікає на "Показати телефон", прокручує списки.
""")

if st.button("🚀 Запустити парсинг"):
    if os.path.exists("results.csv"):
        os.remove("results.csv")

    with st.spinner("Запускаємо Selenium... Це може зайняти 5–15 хвилин"):
        try:
            result = subprocess.run(["python", "scraper.py"], check=True, capture_output=True, text=True)
            st.success("✅ Парсинг завершено успішно!")

            if os.path.exists("results.csv"):
                with open("results.csv", "r", encoding="utf-8") as f:
                    csv_data = f.read()
                st.download_button(
                    label="⬇️ Завантажити results.csv",
                    data=csv_data,
                    file_name="okna_all_phones.csv",
                    mime="text/csv"
                )

                import pandas as pd
                df = pd.read_csv("results.csv")
                st.write(f"Знайдено **{len(df)}** телефонів")
                st.dataframe(df.head(50))
            else:
                st.error("❌ Файл results.csv не створено")

        except subprocess.CalledProcessError as e:
            st.error(f"❌ Помилка виконання: {e.stderr}")
        except Exception as e:
            st.error(f"❌ Невідома помилка: {e}")