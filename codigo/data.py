# data/meteored_scraper.py
import json
import time
import re
from dataclasses import dataclass
from typing import Optional, List, Tuple
from pathlib import Path
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup

URL_AGS = "https://www.meteored.mx/clima_Aguascalientes-America+Norte-Mexico-Aguascalientes-MMAS-1-22385.html"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "Chrome/122.0.0.0 Safari/537.36"
}
CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = CACHE_DIR / "meteored_ags.json"
CACHE_TTL_SEC = 180  # 3 minutos

@dataclass
class WeatherNow:
    fetched_at: datetime
    temp_c: Optional[float]
    wind_kmh: Optional[float]
    gust_kmh: Optional[float]
    wind_dir: Optional[str]
    humidity_pct: Optional[int]
    pressure_hpa: Optional[float]
    visibility_km: Optional[float]
    cloud_cover_pct: Optional[int]
    description: Optional[str]

@dataclass
class ForecastEntry:
    time_label: str
    temp_c: Optional[float]
    wind_kmh: Optional[float]
    wind_dir: Optional[str]
    rain_mm: Optional[float]
    gust_kmh: Optional[float]
    cloud_cover_pct: Optional[int]

def _extract_number(text: Optional[str]) -> Optional[float]:
    if not text:
        return None
    m = re.search(r"(-?\d+(?:[.,]\d+)?)", text)
    return float(m.group(1).replace(",", ".")) if m else None

def _int_safe(val: Optional[float]) -> Optional[int]:
    return int(val) if val is not None else None

def fetch_html(url: str = URL_AGS) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=25)
    resp.raise_for_status()
    return resp.text

def parse_now(html: str) -> WeatherNow:
    soup = BeautifulSoup(html, "html.parser")
    now = WeatherNow(
        fetched_at=datetime.now(timezone.utc),
        temp_c=None, wind_kmh=None, gust_kmh=None, wind_dir=None,
        humidity_pct=None, pressure_hpa=None, visibility_km=None,
        cloud_cover_pct=None, description=None
    )

    # Temperatura actual
    temp_node = soup.select_one(".dato-temperatura, .temperatura.actual, .actual .temperatura, .temp .dato")
    if temp_node:
        now.temp_c = _extract_number(temp_node.get_text())

    # Descripción de estado
    desc_node = soup.select_one(".texto, .estado, .descripcion, .weather-description")
    if desc_node:
        now.description = desc_node.get_text(strip=True)

    # Viento sostenido
    wind_node = soup.select_one(".viento .valor, .wind .valor, .viento .dato, .wind .value")
    if wind_node:
        now.wind_kmh = _extract_number(wind_node.get_text())

    # Rachas
    gust_node = soup.select_one(".racha .valor, .gust .valor, .racha .dato, .gust .value")
    if gust_node:
        now.gust_kmh = _extract_number(gust_node.get_text())

    # Dirección del viento
    dir_node = soup.select_one(".viento .direccion, .wind .direccion, .wind .dir")
    if dir_node:
        now.wind_dir = dir_node.get_text(strip=True)

    # Humedad
    hum_node = soup.select_one(".humedad .valor, .humidity .valor, .humedad .dato, .humidity .value")
    if hum_node:
        now.humidity_pct = _int_safe(_extract_number(hum_node.get_text()))

    # Presión
    pres_node = soup.select_one(".presion .valor, .pressure .valor, .pressure .value")
    if pres_node:
        now.pressure_hpa = _extract_number(pres_node.get_text())

    # Visibilidad
    vis_node = soup.select_one(".visibilidad .valor, .visibility .valor, .visibility .value")
    if vis_node:
        now.visibility_km = _extract_number(vis_node.get_text())

    # Nubosidad
    cloud_node = soup.select_one(".nubosidad .valor, .cloud .valor, .cloud .value")
    if cloud_node:
        now.cloud_cover_pct = _int_safe(_extract_number(cloud_node.get_text()))

    return now

def parse_forecast(html: str) -> List[ForecastEntry]:
    soup = BeautifulSoup(html, "html.parser")
    entries: List[ForecastEntry] = []

    # Modo tabla por horas
    rows = soup.select("table.horas tr, .tabla-horas tr, .hourly-table tr")
    if rows:
        for tr in rows:
            time_label_node = tr.select_one("th, .hora, .time")
            if not time_label_node:
                continue
            temp_node = tr.select_one(".temperatura, .temp .valor, .temp .value")
            wind_node = tr.select_one(".viento .valor, .wind .valor, .wind .value")
            wdir_node = tr.select_one(".viento .direccion, .wind .direccion, .wind .dir")
            rain_node = tr.select_one(".lluvia .valor, .rain .valor, .rain .value")
            gust_node = tr.select_one(".racha .valor, .gust .valor, .gust .value")
            cloud_node = tr.select_one(".nubosidad .valor, .cloud .valor, .cloud .value")

            entries.append(ForecastEntry(
                time_label=time_label_node.get_text(strip=True),
                temp_c=_extract_number(temp_node.get_text()) if temp_node else None,
                viento_kmh=_extract_number(wind_node.get_text()) if wind_node else None,
                viento_dir=Wdir_node.get_text(strip=True) if wdir_node else None,
                rain_mm=_extract_number(rain_node.get_text()) if rain_node else None,
                gust_kmh=_extract_number(gust_node.get_text()) if gust_node else None,
                cloud_cover_pct=_int_safe(_extract_number(cloud_node.get_text())) if cloud_node else None
            ))
        return entries

    # Modo tarjetas por hora
    cards = soup.select(".pronostico-horas .hora, .hourly .hour-card, .hour-card")
    for card in cards:
        time_label_node = card.select_one(".hora, .time")
        if not time_label_node:
            continue
        temp_node = card.select_one(".temperatura, .temp")
        wind_node = card.select_one(".viento .valor, .wind .value")
        wdir_node = card.select_one(".viento .direccion, .wind .dir")
        rain_node = card.select_one(".lluvia .valor, .rain .value")
        gust_node = card.select_one(".racha .valor, .gust .value")
        cloud_node = card.select_one(".nubosidad .valor, .cloud .value")

        entries.append(ForecastEntry(
            time_label=time_label_node.get_text(strip=True),
            temp_c=_extract_number(temp_node.get_text()) if temp_node else None,
            wind_kmh=_extract_number(wind_node.get_text()) if wind_node else None,
            wind_dir=wdir_node.get_text(strip=True) if wdir_node else None,
            rain_mm=_extract_number(rain_node.get_text()) if rain_node else None,
            gust_kmh=_extract_number(gust_node.get_text()) if gust_node else None,
            cloud_cover_pct=_int_safe(_extract_number(cloud_node.get_text())) if cloud_node else None
        ))
    return entries

def load_cache() -> Optional[Tuple[WeatherNow, List[ForecastEntry]]]:
    if not CACHE_FILE.exists():
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if time.time() - data["ts"] > CACHE_TTL_SEC:
            return None
        now = WeatherNow(
            fetched_at=datetime.fromisoformat(data["now"]["fetched_at"]),
            temp_c=data["now"]["temp_c"],
            wind_kmh=data["now"]["wind_kmh"],
            gust_kmh=data["now"]["gust_kmh"],
            wind_dir=data["now"]["wind_dir"],
            humidity_pct=data["now"]["humidity_pct"],
            pressure_hpa=data["now"]["pressure_hpa"],
            visibility_km=data["now"]["visibility_km"],
            cloud_cover_pct=data["now"]["cloud_cover_pct"],
            description=data["now"]["description"],
        )
        hourly = [ForecastEntry(**e) for e in data["hourly"]]
        return now, hourly
    except Exception:
        return None

def save_cache(now: WeatherNow, hourly: List[ForecastEntry]) -> None:
    payload = {
        "ts": time.time(),
        "now": {
            "fetched_at": now.fetched_at.isoformat(),
            "temp_c": now.temp_c,
            "wind_kmh": now.wind_kmh,
            "gust_kmh": now.gust_kmh,
            "wind_dir": now.wind_dir,
            "humidity_pct": now.humidity_pct,
            "pressure_hpa": now.pressure_hpa,
            "visibility_km": now.visibility_km,
            "cloud_cover_pct": now.cloud_cover_pct,
            "description": now.description,
        },
        "hourly": [e.__dict__ for e in hourly],
    }
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def get_weather() -> Tuple[WeatherNow, List[ForecastEntry]]:
    cached = load_cache()
    if cached:
        return cached
    html = fetch_html(URL_AGS)
    now = parse_now(html)
    hourly = parse_forecast(html)
    save_cache(now, hourly)
    return now, hourly