import sqlite3
import httpx
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from urllib.parse import quote
from datetime import datetime
import pytz

app = FastAPI()

# Подключение шаблонов
templates = Jinja2Templates(directory="app/templates")
templates.env.filters["urlencode"] = lambda u: quote(u)

# Подключение статических файлов (если есть)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect("app/weather.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Главная страница
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        conn = sqlite3.connect("app/weather.db")
        cursor = conn.cursor()
        cursor.execute("SELECT city FROM search_history ORDER BY timestamp DESC LIMIT 1")
        result = cursor.fetchone()
        last_city = result[0] if result else None
    except Exception:
        last_city = None
    finally:
        conn.close()
    return templates.TemplateResponse("index.html", {"request": request, "last_city": last_city})

# Получение координат через Nominatim
async def get_coordinates(city: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": city, "format": "json", "limit": 1},
            headers={"User-Agent": "weather-app"}
        )
        response.raise_for_status()
        data = response.json()
        if not data:
            raise ValueError("Город не найден")
        return float(data[0]["lat"]), float(data[0]["lon"])

# Получение погоды
async def get_weather(lat: float, lon: float):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": True
            }
        )
        response.raise_for_status()
        return response.json()

# Погода
@app.get("/weather", response_class=HTMLResponse)
async def weather(request: Request, city: str = Query(...)):
    try:
        lat, lon = await get_coordinates(city)
        data = await get_weather(lat, lon)
        weather_data = data.get("current_weather")

        if not weather_data:
            raise ValueError("Нет данных о погоде")

        temperature = weather_data.get("temperature")
        wind_speed = weather_data.get("windspeed")
        time_utc = weather_data.get("time")

        # Конвертация времени
        time_local = datetime.fromisoformat(time_utc).astimezone(pytz.timezone("Europe/Moscow")).strftime("%Y-%m-%d %H:%M")

        # Сохраняем в БД
        conn = sqlite3.connect("app/weather.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO search_history (city) VALUES (?)", (city,))
        conn.commit()
        conn.close()

        return templates.TemplateResponse("weather.html", {
            "request": request,
            "city": city,
            "temperature": temperature,
            "wind_speed": wind_speed,
            "local_time": time_local,
            "error": None
        })

    except Exception as e:
        return templates.TemplateResponse("weather.html", {
            "request": request,
            "city": city,
            "temperature": None,
            "wind_speed": None,
            "local_time": None,
            "error": f"Ошибка: {str(e)}"
        })
