import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(layout="wide")
st.title("Анализ температурных данных и мониторинг текущей температуры через OpenWeatherMap API")

uploaded_file = st.file_uploader("Загрузите CSV-файл с историческими данными", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, parse_dates=["timestamp"])
    if "city" not in df.columns:
        st.error("В файле отсутствует столбец 'city'. Проверьте формат данных.")
    else:
        st.success("Данные успешно загружены!")
        st.dataframe(df.sample(5))
else:
    st.warning("Пожалуйста, загрузите файл с историческими данными.")

if uploaded_file is not None:
    cities = df["city"].unique().tolist()
    selected_city = st.selectbox("Выберите город", sorted(cities))

    api_key = st.text_input("Введите API-ключ OpenWeatherMap")
    if not api_key:
        st.info("API-ключ не введён. Данные о текущей погоде не будут отображаться.")
    else:
        st.success("API-ключ введён!")

    city_df = df[df["city"] == selected_city].copy()
    city_df.sort_values("timestamp", inplace=True)

    st.subheader("Описательная статистика")
    st.write(city_df.describe())

    season_stats = city_df.groupby("season")["temperature"].agg(['mean', 'std', 'min', 'max']).reset_index()
    st.write("Статистика по сезонам", season_stats)

    stats_dict = season_stats.set_index("season").to_dict(orient="index")


    def mark_anomaly(row):
        season = row["season"]
        mean_val = stats_dict[season]["mean"]
        std_val = stats_dict[season]["std"]
        lower_bound = mean_val - 2 * std_val
        upper_bound = mean_val + 2 * std_val
        return not (lower_bound <= row["temperature"] <= upper_bound)


    city_df["is_anomaly"] = city_df.apply(mark_anomaly, axis=1)

    st.subheader("Временной ряд температур с аномалиями")
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(city_df["timestamp"], city_df["temperature"], label="Температура", color="blue", alpha=0.6)
    anomalies = city_df[city_df["is_anomaly"]]
    ax.scatter(anomalies["timestamp"], anomalies["temperature"], color="red", label="Аномалии", zorder=5)
    ax.set_xlabel("Дата")
    ax.set_ylabel("Температура (°C)")
    ax.legend()
    st.pyplot(fig)

    st.subheader("Сезонные профили")
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    seasons = season_stats["season"]
    means = season_stats["mean"]
    stds = season_stats["std"]
    ax2.bar(seasons, means, yerr=stds, capsize=5, color="skyblue")
    ax2.set_xlabel("Сезон")
    ax2.set_ylabel("Средняя температура (°C)")
    ax2.set_title("Сезонный профиль температуры")
    st.pyplot(fig2)


    def get_current_season():
        month = datetime.now().month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "autumn"


    current_season = get_current_season()

    st.subheader("Текущая погода")


    def get_current_temperature(city, key):
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": key, "units": "metric"}
        response = requests.get(base_url, params=params)
        data = response.json()
        if response.status_code == 401:
            st.error(f"Ошибка: {data.get('message', 'Неверный API-ключ')}")
            return None
        elif response.status_code != 200:
            st.error(f"Ошибка получения данных для {city}: {data.get('message', 'Неизвестная ошибка')}")
            return None
        else:
            return data["main"]["temp"]


    if api_key:
        current_temp = get_current_temperature(selected_city, api_key)
        if current_temp is not None:
            if current_season in stats_dict:
                mean_val = stats_dict[current_season]["mean"]
                std_val = stats_dict[current_season]["std"]
                lower_bound = mean_val - 2 * std_val
                upper_bound = mean_val + 2 * std_val
                normal = lower_bound <= current_temp <= upper_bound
                status = "Норма" if normal else "Аномалия"
                st.write(f"Текущая температура в {selected_city}: **{current_temp:.1f}°C**")
                st.write(
                    f"Для сезона **{current_season}** историческое среднее = **{mean_val:.1f}°C** (± {std_val:.1f}°C)")
                st.write(f"Статус текущей температуры: **{status}**")
            else:
                st.warning("Нет данных для определения сезонного профиля для текущего сезона.")