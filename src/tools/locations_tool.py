"""
Tool: get_active_locations
Llama a GET /api/users/brigadas/active via HTTP interno.
Retorna camiones EN_CAMINO o EN_SITIO con coords GPS.
"""

from langchain_core.tools import tool
from src.config.http_client import get_client
from src.config.settings import settings


@tool
async def get_active_locations() -> str:
    """
    Retorna los camiones de brigada actualmente desplegados (EN_CAMINO o EN_SITIO).
    Incluye coords GPS, brigada y reporte al que responden.
    Usar para saber si hay recursos en campo en este momento.
    """
    client = get_client()
    url = f"{settings.USER_SERVICE_URL}/api/users/brigadas/active"

    resp = await client.get(url)
    resp.raise_for_status()
    data = resp.json()

    unidades = data if isinstance(data, list) else data.get("activas", data.get("data", []))

    if not unidades:
        return "No hay unidades desplegadas en este momento."

    lines = [f"UNIDADES ACTIVAS ({len(unidades)}):"]
    for u in unidades:
        estado = u.get("estado", "—")
        emoji = "🚒" if estado == "EN_CAMINO" else "🔥"
        lat = u.get("lat"); lng = u.get("lng")
        coords = f"({float(lat):.4f}, {float(lng):.4f})" if lat and lng else "Sin GPS"
        brigada = u.get("brigada_nombre") or u.get("nombre") or f"Brigada #{u.get('brigade_id')}"
        lines.append(
            f"  {emoji} {brigada} — {estado} "
            f"| Reporte #{u.get('report_id', '—')} | GPS: {coords}"
        )

    return "\n".join(lines)