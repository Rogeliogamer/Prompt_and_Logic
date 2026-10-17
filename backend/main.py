from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict

app = FastAPI(title="Prompt & Logic - JEV Guardrails API")

# --- HABILITAR CORS PARA CONECTAR CON REACT (VITE) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción se cambia por la URL de tu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. MODELOS DE DATOS (PYDANTIC) ---
class AgentAction(BaseModel):
    action_id: str
    agent_name: str
    operation_type: str
    target_system: str
    payload: Dict[str, Any]

class EvaluationResult(BaseModel):
    status: str  # "APPROVED", "BLOCKED", "ESCALATED"
    reason: str
    jev_metrics: Dict[str, Any]

# --- 2. SIMULADOR DE JEV (AQUÍ IRÁ LA LLAMADA A TYPESAFE) ---
def simulate_jev_call(action: AgentAction) -> dict:
    """
    Simula la respuesta probabilística y estructurada del modelo JEV.
    """
    mock_responses = {
        "act_001": {"noul_pii_prob": 0.05, "choice": 2, "choice_conf": 0.95, "score_tone": 5, "score_conf": 0.90},
        "act_002": {"noul_pii_prob": 0.98, "choice": 4, "choice_conf": 0.80, "score_tone": 1, "score_conf": 0.85},
        "act_003": {"noul_pii_prob": 0.01, "choice": 3, "choice_conf": 0.99, "score_tone": 3, "score_conf": 0.90},
        "act_004": {"noul_pii_prob": 0.10, "choice": 2, "choice_conf": 0.80, "score_tone": 2, "score_conf": 0.95},
        "act_005": {"noul_pii_prob": 0.05, "choice": 4, "choice_conf": 0.85, "score_tone": 3, "score_conf": 0.80},
        "act_006": {"noul_pii_prob": 0.00, "choice": 1, "choice_conf": 0.98, "score_tone": 5, "score_conf": 0.90},
    }
    
    # Respuesta por defecto si mandas un ID no mapeado
    return mock_responses.get(action.action_id, {
        "noul_pii_prob": 0.1, "choice": 4, "choice_conf": 0.6, "score_tone": 3, "score_conf": 0.6
    })

# --- 3. EL MOTOR DE REGLAS (LA LÓGICA DE PROMPT & LOGIC) ---
@app.post("/evaluate_action", response_model=EvaluationResult)
async def evaluate_agent_action(action: AgentAction):
    # 1. Ejecutar evaluación (System One)
    jev_output = simulate_jev_call(action)
    
    noul_pii = jev_output["noul_pii_prob"]
    choice = jev_output["choice"]
    choice_conf = jev_output["choice_conf"]
    score = jev_output["score_tone"]
    score_conf = jev_output["score_conf"]

    status = "APPROVED"
    reason = "Acción segura y dentro de parámetros normales."

    # 2. Lógica de Bloqueo Total (Prioridad Alta)
    if noul_pii > 0.50:
        status = "BLOCKED"
        reason = "Riesgo crítico: Fuga detectada de PII o datos financieros."
    elif choice == 3:
        status = "BLOCKED"
        reason = "Riesgo crítico: Acción masiva o destructiva en base de datos."
        
    # 3. Lógica de Escalamiento a Humano (Prioridad Media)
    elif status != "BLOCKED":
        # Baja confianza del modelo
        if choice_conf < 0.70 or score_conf < 0.70:
            status = "ESCALATED"
            reason = "Revisión requerida: JEV reporta baja confianza en su clasificación."
        # Comportamiento extraño/fuera de esquema
        elif choice == 4:
            status = "ESCALATED"
            reason = "Revisión requerida: Comportamiento anómalo o no estándar."
        # Tono agresivo o no alineado en comunicaciones masivas
        elif "email" in action.operation_type and score < 4:
            status = "ESCALATED"
            reason = "Revisión requerida: El tono del mensaje no cumple la política corporativa."

    # 4. Retornar veredicto al Frontend
    return EvaluationResult(
        status=status,
        reason=reason,
        jev_metrics=jev_output
    )