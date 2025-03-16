import streamlit as st
import pandas as pd
import requests

st.title("Анализ температурных данных и мониторинг текущей температуры через OpenWeatherMap API")

uploaded_file = st.file_uploader("Загрузите CSV-файл с историческими данными", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, parse_dates=["timestamp"])
    st.success("Данные успешно загружены!")
    st.dataframe(df.head())
else:
    st.warning("Пожалуйста, загрузите файл с историческими данными.")

cities = ["Berlin", "Cairo", "Dubai", "Beijing", "Moscow"]
selected_city = st.selectbox("Выберите город", cities)

api_key = st.text_input("Введите API-ключ OpenWeatherMap", type="password")
if not api_key:
    st.info("API-ключ не введён. Данные о текущей погоде не будут отображаться.")
else:
    st.success("API-ключ введён!")

def get_current_temperature(city, key):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": key, "units": "metric"}
    response = requests.get(base_url, params=params)
    data = response.json()
    if response.status_code == 200:
        return data["main"]["temp"]
    else:
        st.error(f"Ошибка получения данных для {city}: {data.get('message', 'Неизвестная ошибка')}")
        return None

if api_key and uploaded_file is not None:
    current_temp = get_current_temperature(selected_city, api_key)
    if current_temp is not None:
        st.write(f"Текущая температура в {selected_city}: {current_temp:.1f}°C")