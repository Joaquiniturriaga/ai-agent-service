"""
Tool: query_brigades
Llama a GET /api/users/brigadas via HTTP interno.
No toca la DB directamente — respeta la arquitectura de microservicios.
"""

from langchain_core.tools import tool
from src.config.http_client import get_client
from src.config.settings import settings


@tool
async def query_brigades() -> str:
    """
    Consulta las brigadas activas del sistema Valle del Sol.
    Retorna nombre, zona, dominio y cantidad de miembros asignados.
    Usar cuando se necesite saber qué brigadas están disponibles.
    """
    client = get_client()
    url = f"{settings.USER_SERVICE_URL}/api/users/brigadas"

    resp = await client.get(url)
    resp.raise_for_status()
    data = resp.json()

    # El endpoint retorna lista o { brigadas: [...] } según implementación
    brigadas = data if isinstance(data, list) else data.get("brigadas", data.get("data", []))

    if not brigadas:
        return "No hay brigadas registradas en el sistema."

    activas = [b for b in brigadas if b.get("activa", True)]
    lines = [f"BRIGADAS ACTIVAS ({len(activas)} de {len(brigadas)} totales):"]

    for b in activas:
        zona    = b.get("zona") or "Sin zona"
        dominio = b.get("dominio") or "Sin dominio"
        members = b.get("miembros") or b.get("member_count") or "—"
        lines.append(
            f"  [{b.get('id')}] {b.get('nombre')} "
            f"— Zona: {zona} | Dominio: {dominio} | Miembros: {members}"
        )

    return "\n".join(lines)