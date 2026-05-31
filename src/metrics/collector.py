"""
Metrics collector — llama a los microservicios en paralelo con asyncio.gather
y devuelve un resumen del sistema sin pasar por el LLM.
También calcula riesgo climático para la zona base (San Fernando, O'Higgins).
"""

import asyncio
import httpx
from datetime import datetime

from src.config.http_client import get_client
from src.config.settings import settings

# Coordenadas base: San Fernando, Región de O'Higgins
BASE_LAT = -34.59
BASE_LNG = -70.98


async def _fetch_brigades(client: httpx.AsyncClient) -> dict:
    try:
        r = await client.get(f"{settings.USER_SERVICE_URL}/api/users/brigadas")
        r.raise_for_status()
        data = r.json()
        lista = data if isinstance(data, list) else data.get("brigadas", data.get("data", []))
        activas = [b for b in lista if b.get("activa", True)]
        return {
            "total": len(lista),
            "activas": len(activas),
            "brigadas": [
                {
                    "id": b.get("id"),
                    "nombre": b.get("nombre"),
                    "zona": b.get("zona"),
                    "miembros": b.get("miembros") or b.get("member_count") or 0,
                }
                for b in activas
            ],
        }
    except Exception as e:
        return {"error": str(e), "total": 0, "activas": 0, "brigadas": []}


async def _fetch_reports(client: httpx.AsyncClient) -> dict:
    try:
        r = await client.get(f"{settings.REPORT_SERVICE_URL}/api/reports")
        r.raise_for_status()
        data = r.json()
        lista = data if isinstance(data, list) else data.get("reportes", data.get("data", []))

        by_status: dict[str, int] = {}
        by_tipo: dict[str, int] = {}
        for rep in lista:
            s = rep.get("status", "UNKNOWN")
            t = rep.get("tipo", "UNKNOWN")
            by_status[s] = by_status.get(s, 0) + 1
            by_tipo[t] = by_tipo.get(t, 0) + 1

        activos = [r for r in lista if r.get("status") == "ACTIVE"]
        return {
            "total": len(lista),
            "activos": len(activos),
            "por_estado": by_status,
            "por_tipo": by_tipo,
            "ultimos_activos": [
                {
                    "id": r.get("id"),
                    "title": r.get("title"),
                    "tipo": r.get("tipo"),
                    "lat": r.get("lat"),
                    "lng": r.get("lng"),
                    "created_at": r.get("created_at"),
                }
                for r in activos[:5]
            ],
        }
    except Exception as e:
        return {"error": str(e), "total": 0, "activos": 0, "por_estado": {}, "por_tipo": {}, "ultimos_activos": []}


async def _fetch_active_units(client: httpx.AsyncClient) -> dict:
    try:
        r = await client.get(f"{settings.USER_SERVICE_URL}/api/users/brigadas/active")
        r.raise_for_status()
        data = r.json()
        unidades = data if isinstance(data, list) else data.get("activas", data.get("data", []))
        return {
            "total": len(unidades),
            "unidades": [
                {
                    "brigada": u.get("brigada_nombre") or u.get("nombre") or f"#{u.get('brigade_id')}",
                    "estado": u.get("estado"),
                    "report_id": u.get("report_id"),
                    "lat": u.get("lat"),
                    "lng": u.get("lng"),
                }
                for u in unidades
            ],
        }
    except Exception as e:
        return {"error": str(e), "total": 0, "unidades": []}


async def _fetch_admin_alerts(client: httpx.AsyncClient) -> dict:
    try:
        r = await client.get(f"{settings.NOTIFICATION_SERVICE_URL}/api/notifications/admin/alerts")
        r.raise_for_status()
        data = r.json()
        lista = data if isinstance(data, list) else data.get("alerts", data.get("data", []))
        pending = [a for a in lista if a.get("status") == "PENDING"]
        return {
            "total": len(lista),
            "pendientes": len(pending),
        }
    except Exception as e:
        return {"error": str(e), "total": 0, "pendientes": 0}


async def _fetch_weather(lat: float, lng: float) -> dict:
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lng}"
        "&current=temperature_2m,relative_humidity_2m,"
        "wind_speed_10m,precipitation&hourly=precipitation"
        "&forecast_days=1&timezone=auto"
    )
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.get(url)
            r.raise_for_status()
            data = r.json()

        cur = data["current"]
        temp     = cur["temperature_2m"]
        humidity = cur["relative_humidity_2m"]
        wind     = cur["wind_speed_10m"]
        precip_24h = sum(data.get("hourly", {}).get("precipitation", [])[:24]) or cur["precipitation"]

        score = 0
        if temp > 35: score += 3
        elif temp > 25: score += 2
        if humidity < 20: score += 3
        elif humidity < 40: score += 2
        if wind > 40: score += 2
        elif wind > 20: score += 1
        if precip_24h == 0: score += 1

        level = (
            "EXTREMO" if score >= 9 else
            "ALTO"    if score >= 6 else
            "MODERADO" if score >= 3 else
            "BAJO"
        )

        return {
            "lat": lat, "lng": lng,
            "temperatura": temp,
            "humedad": humidity,
            "viento": wind,
            "precipitacion_24h": round(precip_24h, 1),
            "score": score,
            "nivel_riesgo": level,
        }
    except Exception as e:
        return {"error": str(e), "nivel_riesgo": "DESCONOCIDO"}


async def get_system_summary() -> dict:
    """
    Llama a todos los microservicios en paralelo y devuelve el resumen del sistema.
    Usado por GET /api/agent/metrics/summary — sin LLM, respuesta rápida.
    """
    client = get_client()

    brigades, reports, units, alerts, weather = await asyncio.gather(
        _fetch_brigades(client),
        _fetch_reports(client),
        _fetch_active_units(client),
        _fetch_admin_alerts(client),
        _fetch_weather(BASE_LAT, BASE_LNG),
    )

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "zona_referencia": "San Fernando, O'Higgins",
        "clima": weather,
        "brigadas": brigades,
        "reportes": reports,
        "unidades_desplegadas": units,
        "alertas": alerts,
    }