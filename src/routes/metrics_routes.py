from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from src.config.settings import settings
from src.metrics.collector import get_system_summary

router = APIRouter(tags=["metrics"])


def _validate_key(key: Optional[str]):
    if not key or key != settings.INTERNAL_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/summary")
async def summary(x_internal_key: Optional[str] = Header(None)):
    """
    Resumen del sistema en tiempo real: clima, brigadas, reportes activos,
    unidades desplegadas y alertas pendientes.
    Sin LLM — respuesta directa en ~2s (llamadas en paralelo).
    """
    _validate_key(x_internal_key)
    data = await get_system_summary()
    return data