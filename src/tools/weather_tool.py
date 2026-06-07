import httpx
from langchain_core.tools import tool

@tool
async def get_weather_risk(lat: float, lng: float) -> str:
    """
    Consulta el clima actual en las coordenadas dadas y calcula el riesgo
    de incendio forestal. Retorna temperatura, humedad, viento, precipitación
    y nivel de riesgo (BAJO / MODERADO / ALTO / EXTREMO).
    Usar SIEMPRE antes de emitir cualquier evaluación de riesgo de incendio.

    Args:
        lat: Latitud (ej: -33.45 Santiago, -34.17 San Fernando, -37.5 Biobío)
        lng: Longitud (ej: -70.65 Santiago, -70.98 San Fernando, -72.5 Biobío)
    """
    # URL Corregida: Limpia, dinámica y sin las coordenadas de Berlín
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lng}"
        "&current=temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation,weather_code"
        "&hourly=precipitation&forecast_days=1&timezone=auto"
    )

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    c = data["current"]
    temp     = c["temperature_2m"]
    humidity = c["relative_humidity_2m"]
    wind     = c["wind_speed_10m"]
    precip   = c["precipitation"]
    precip_24h = sum(data.get("hourly", {}).get("precipitation", [])[:24]) or precip

    score, reasons = 0, []

    if temp > 35:
        score += 3; reasons.append(f"temperatura crítica ({temp}°C)")
    elif temp > 25:
        score += 2; reasons.append(f"temperatura elevada ({temp}°C)")

    if humidity < 20:
        score += 3; reasons.append(f"humedad muy baja ({humidity}%)")
    elif humidity < 40:
        score += 2; reasons.append(f"humedad baja ({humidity}%)")

    if wind > 40:
        score += 2; reasons.append(f"viento fuerte ({wind} km/h)")
    elif wind > 20:
        score += 1; reasons.append(f"viento moderado ({wind} km/h)")

    if precip_24h == 0:
        score += 1; reasons.append("sin precipitaciones en 24h")

    level = (
        "EXTREMO" if score >= 9 else
        "ALTO"    if score >= 6 else
        "MODERADO" if score >= 3 else
        "BAJO"
    )

    factors = ", ".join(reasons) if reasons else "condiciones normales"
    return (
        f"CLIMA en ({lat}, {lng}):\n"
        f"  Temperatura : {temp}°C\n"
        f"  Humedad     : {humidity}%\n"
        f"  Viento      : {wind} km/h\n"
        f"  Precip 24h  : {precip_24h:.1f} mm\n"
        f"  Score       : {score}/11\n"
        f"  Riesgo      : {level}\n"
        f"  Factores    : {factors}"
    )