"""
AgentExecutor con GitHub Models (gpt-4o-mini via ChatOpenAI + base_url custom).
create_tool_calling_agent = ReAct moderno con function calling nativo.
"""

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from src.config.settings import settings
from src.tools.weather_tool import get_weather_risk
from src.tools.brigades_tool import query_brigades
from src.tools.reports_tool import query_active_reports
from src.tools.locations_tool import get_active_locations
from src.tools.create_report_tool import create_report

# ── LLM ────────────────────────────────────────────────────────────────────
# GitHub Models expone protocolo OpenAI — solo cambia base_url y api_key
llm = ChatOpenAI(
    model=settings.GITHUB_MODEL,
    api_key=settings.GITHUB_TOKEN,
    base_url=settings.GITHUB_API_BASE,
    temperature=0.2,
    max_tokens=1024,
)

tools = [
    get_weather_risk,
    query_brigades,
    query_active_reports,
    get_active_locations,
    create_report,
]

# ── System prompt ──────────────────────────────────────────────────────────
SYSTEM = """Eres el Agente de Riesgo de Incendios del sistema Valle del Sol,
plataforma de gestión para el Cuerpo de Bomberos de la Región de O'Higgins, Chile.

CAPACIDADES:
1. Evaluar riesgo de incendio forestal según clima actual (get_weather_risk)
2. Consultar brigadas disponibles (query_brigades)
3. Revisar emergencias activas (query_active_reports)
4. Ver unidades desplegadas en campo (get_active_locations)
5. Crear reportes de emergencia (create_report) — SOLO con confirmación explícita

COORDENADAS DE REFERENCIA (Chile):
- San Fernando / O'Higgins : lat -34.59, lng -70.98
- Santiago                 : lat -33.45, lng -70.65
- Rancagua                 : lat -34.17, lng -70.74
- Biobío / Concepción      : lat -36.82, lng -73.05
- Valparaíso               : lat -33.04, lng -71.62

REGLAS:
- Nunca inventes datos climáticos — usa get_weather_risk con coords reales.
- Si el usuario no da coordenadas, usa las de San Fernando como referencia regional.
- Con riesgo ALTO o EXTREMO: menciona pastos secos, vientos, recomienda alertar brigadas.
- NUNCA crear reporte sin que el operador lo pida con palabras claras.
- Responde siempre en español. Sé conciso y operacionalmente útil.
- Si hay unidades desplegadas, inclúyelas en el análisis de situación.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])

agent = create_tool_calling_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=6,
    handle_parsing_errors=True,
    return_intermediate_steps=False,
)


def _build_history(raw: list[dict]) -> list:
    msgs = []
    for m in raw:
        if m["role"] == "user":
            msgs.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            msgs.append(AIMessage(content=m["content"]))
    return msgs


async def run_agent(message: str, history: list[dict] = None) -> str:
    result = await agent_executor.ainvoke({
        "input": message,
        "chat_history": _build_history(history or []),
    })
    return result["output"]