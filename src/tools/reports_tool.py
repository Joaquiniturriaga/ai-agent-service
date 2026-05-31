
"""
Tool: query_active_reports
Llama a GET /api/reports via HTTP interno al Report Service.
"""

from langchain_core.tools import tool
from src.config.http_client import get_client
from src.config.settings import settings


@tool
async def query_active_reports() -> str:
    """
    Consulta los reportes de emergencia activos en el sistema.
    Retorna título, tipo, coordenadas y fecha de creación.
    Usar cuando se pregunte sobre emergencias en curso.
    """
    client = get_client()
    url = f"{settings.REPORT_SERVICE_URL}/api/reports"

    resp = await client.get(url)
    resp.raise_for_status()
    data = resp.json()

    reportes = data if isinstance(data, list) else data.get("reportes", data.get("data", []))
    activos = [r for r in reportes if r.get("status") == "ACTIVE"]

    if not activos:
        return "No hay reportes activos en este momento."

    lines = [f"REPORTES ACTIVOS ({len(activos)}):"]
    for r in activos:
        lat = r.get("lat"); lng = r.get("lng")
        coords = f"({float(lat):.4f}, {float(lng):.4f})" if lat and lng else "Sin coords"
        created = r.get("created_at", "—")[:16].replace("T", " ") if r.get("created_at") else "—"
        lines.append(
            f"  [#{r.get('id')}] {r.get('title')} "
            f"— Tipo: {r.get('tipo', '—')} | Coords: {coords} | Creado: {created}"
        )

    return "\n".join(lines)