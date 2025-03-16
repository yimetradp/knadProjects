import aiohttp
import asyncio
import numpy as np
import pandas as pd
import requests
import time
from datetime import datetime
from joblib import Parallel, delayed

API_KEY = '5189fb2f58df9b07a9c3baae5ba4950f'
BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'

def get_current_season():
    month = datetime.now().month
    if month in [12, 1, 2]:
        return 'winter'
    elif month in [3, 4, 5]:
        return 'spring'
    elif month in [6, 7, 8]:
        return 'summer'
    else:
        return 'autumn'

def is_temperature_normal(city, current_temp, historical_stats, current_season):
    stats = historical_stats[(historical_stats['city'] == city) & (historical_stats['season'] == current_season)]
    if stats.empty:
        raise Exception(f'Нет исторических данных для города {city} и сезона {current_season}')
    mean_temp = stats['mean'].iloc[0]
    std_temp = stats['std'].iloc[0]
    lower_bound = mean_temp - 2 * std_temp
    upper_bound = mean_temp + 2 * std_temp
    return lower_bound <= current_temp <= upper_bound, mean_temp, std_temp

def get_current_temperature_sync(city):
    params = {
        'q': city,
        'appid': API_KEY,
        'units': 'metric'
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    if response.status_code == 200:
        return data['main']['temp']
    else:
        raise Exception(f'Ошибка API для города {city}: {data.get('message', 'Неизвестная ошибка')}')

# Реальные средние температуры (примерные данные) для городов по сезонам
seasonal_temperatures = {
    "New York": {"winter": 0, "spring": 10, "summer": 25, "autumn": 15},
    "London": {"winter": 5, "spring": 11, "summer": 18, "autumn": 12},
    "Paris": {"winter": 4, "spring": 12, "summer": 20, "autumn": 13},
    "Tokyo": {"winter": 6, "spring": 15, "summer": 27, "autumn": 18},
    "Moscow": {"winter": -10, "spring": 5, "summer": 18, "autumn": 8},
    "Sydney": {"winter": 12, "spring": 18, "summer": 25, "autumn": 20},
    "Berlin": {"winter": 0, "spring": 10, "summer": 20, "autumn": 11},
    "Beijing": {"winter": -2, "spring": 13, "summer": 27, "autumn": 16},
    "Rio de Janeiro": {"winter": 20, "spring": 25, "summer": 30, "autumn": 25},
    "Dubai": {"winter": 20, "spring": 30, "summer": 40, "autumn": 30},
    "Los Angeles": {"winter": 15, "spring": 18, "summer": 25, "autumn": 20},
    "Singapore": {"winter": 27, "spring": 28, "summer": 28, "autumn": 27},
    "Mumbai": {"winter": 25, "spring": 30, "summer": 35, "autumn": 30},
    "Cairo": {"winter": 15, "spring": 25, "summer": 35, "autumn": 25},
    "Mexico City": {"winter": 12, "spring": 18, "summer": 20, "autumn": 15},
}

# Сопоставление месяцев с сезонами
month_to_season = {12: "winter", 1: "winter", 2: "winter",
                   3: "spring", 4: "spring", 5: "spring",
                   6: "summer", 7: "summer", 8: "summer",
                   9: "autumn", 10: "autumn", 11: "autumn"}

# Генерация данных о температуре
def generate_realistic_temperature_data(cities, num_years=10):
    dates = pd.date_range(start="2010-01-01", periods=365 * num_years, freq="D")
    data = []

    for city in cities:
        for date in dates:
            season = month_to_season[date.month]
            mean_temp = seasonal_temperatures[city][season]
            # Добавляем случайное отклонение
            temperature = np.random.normal(loc=mean_temp, scale=5)
            data.append({"city": city, "timestamp": date, "temperature": temperature})

    df = pd.DataFrame(data)
    df['season'] = df['timestamp'].dt.month.map(lambda x: month_to_season[x])
    return df

# Генерация данных
data = generate_realistic_temperature_data(list(seasonal_temperatures.keys()))
data.to_csv('temperature_data.csv', index=False)

historical_stats = (
    df.groupby(['city', 'season'])['temperature']
      .agg(mean='mean', std='std')
      .reset_index()
)

current_season = get_current_season()

try:
    current_temp = get_current_temperature_sync(city)
    normal, mean_temp, std_temp = is_temperature_normal(city, current_temp, historical_stats, current_season)
    status = 'Норма' if normal else 'Аномалия'
    print(f'{city}: текущая температура = {current_temp:.1f}°C, историческое среднее = {mean_temp:.1f}°C, std = {std_temp:.1f}°C => {status}')
except Exception as e:
    print(f'{city}: {e}')