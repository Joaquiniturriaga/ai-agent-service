"""
Tool: create_report
Llama a POST /api/reports via HTTP interno al Report Service.
SOLO usar con confirmación explícita del operador.
"""

from langchain_core.tools import tool
from src.config.http_client import get_client
from src.config.settings import settings

VALID_TIPOS = {"INCENDIO", "ACCIDENTE", "DERRUMBE", "INUNDACION"}


@tool
async def create_report(
    title: str,
    lat: float,
    lng: float,
    tipo: str = "INCENDIO",
    description: str = "",
) -> str:
    """
    Crea un nuevo reporte de emergencia en el sistema.
    SOLO usar cuando el operador confirme EXPLÍCITAMENTE con palabras como
    'crear', 'registrar', 'ingresa el reporte'. Nunca crear sin confirmación.

    Args:
        title: Título del reporte (ej: "Incendio forestal sector Las Palmas")
        lat: Latitud del incidente
        lng: Longitud del incidente
        tipo: INCENDIO | ACCIDENTE | DERRUMBE | INUNDACION
        description: Descripción adicional (opcional)
    """
    if tipo not in VALID_TIPOS:
        return f"Error: tipo '{tipo}' inválido. Opciones: {', '.join(VALID_TIPOS)}"
    if not (-90 <= lat <= 90):
        return f"Error: latitud {lat} fuera de rango."
    if not (-180 <= lng <= 180):
        return f"Error: longitud {lng} fuera de rango."

    client = get_client()
    url = f"{settings.REPORT_SERVICE_URL}/api/reports"

    payload = {"title": title, "lat": lat, "lng": lng, "tipo": tipo}
    if description:
        payload["description"] = description

    resp = await client.post(url, json=payload)

    if resp.status_code == 201:
        data = resp.json()
        rid = data.get("id") or data.get("reporte", {}).get("id", "—")
        return (
            f"✅ Reporte creado.\n"
            f"  ID     : #{rid}\n"
            f"  Título : {title}\n"
            f"  Tipo   : {tipo}\n"
            f"  Coords : ({lat}, {lng})\n"
            f"  El Notification Service procesará alertas automáticamente."
        )
    else:
        return f"Error HTTP {resp.status_code}: {resp.text[:200]}"