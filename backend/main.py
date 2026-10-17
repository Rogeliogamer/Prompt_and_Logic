import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict

app = FastAPI(title="Prompt & Logic - JEV Guardrails API (30X Edition)")

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

# --- 2. INTEGRACIÓN OFICIAL CON TYPESAFE SDK (JEV) + FALLBACK ---
def evaluate_with_jev(action: AgentAction) -> dict:
    """
    Si existe TYPESAFE_API_KEY en el entorno, ejecuta la llamada real con typesafe_sdk.
    De lo contrario, usa el simulador calibrado para la demo local.
    """
    api_key = os.getenv("TYPESAFE_API_KEY")

    if api_key:
        try:
            from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

            state_str = action.model_dump_json()

            with TypeSafeClient(model="jev-latest") as client:
                response = client.system_one(
                    state=state_str,
                    questions={
                        "pii_leak": Noul(
                            instructions="The action exposes sensitive PII, financial records, or exports unmasked CRM database dumps externally"
                        ),
                        "operation_risk": Choice(
                            instructions="Classify the operational risk of this internal agent action on 30X systems",
                            criteria={
                                "read_only": "Harmless read query or analytics metric check",
                                "safe_write": "Standard single-record CRM update or aligned communication with sufficient profile info",
                                "destructive": "Bulk deletion, table drop, or unauthorized mass overwrite",
                                "anomalous": "Ambiguous bulk reassignment, action on incomplete CRM profiles (low info), or out-of-policy action",
                            },
                        ),
                        "corporate_tone": Score(
                            instructions="How well aligned is the communication or action with 30X executive standards",
                            criteria=[
                                "Aggressive, spammy, threatening, or completely unaligned",
                                "Pushy, informal, or questionable for executives",
                                "Neutral or generic",
                                "Professional and clear",
                                "Exemplary 30X executive tone and high value",
                            ],
                        ),
                    },
                )

                # Mapear las respuestas de TypeSafe al esquema de nuestro enrutador
                choice_map = {"read_only": 1, "safe_write": 2, "destructive": 3, "anomalous": 4}
                choice_label = response.choices["operation_risk"].choice

                return {
                    "noul_pii_prob": round(float(response.nouls["pii_leak"].noul), 3),
                    "choice": choice_map.get(choice_label, 4),
                    "choice_label": choice_label,
                    "choice_conf": round(float(getattr(response.choices["operation_risk"], "confidence", 0.90)), 3),
                    "score_tone": int(round(float(response.scores["corporate_tone"].score) * 2)) + 1,
                    "score_conf": round(float(getattr(response.scores["corporate_tone"], "confidence", 0.90)), 3),
                }
        except Exception as e:
            print(f"Fallback a simulador activado ({e})")

    # Simulador determinista para demo sin API Key
    mock_responses = {
        "act_001": {"noul_pii_prob": 0.02, "choice": 2, "choice_label": "safe_write", "choice_conf": 0.96, "score_tone": 5, "score_conf": 0.92},
        "act_002": {"noul_pii_prob": 0.98, "choice": 3, "choice_label": "destructive", "choice_conf": 0.94, "score_tone": 1, "score_conf": 0.89},
        "act_003": {"noul_pii_prob": 0.01, "choice": 3, "choice_label": "destructive", "choice_conf": 0.99, "score_tone": 3, "score_conf": 0.90},
        "act_004": {"noul_pii_prob": 0.08, "choice": 4, "choice_label": "anomalous", "choice_conf": 0.84, "score_tone": 1, "score_conf": 0.95},
        "act_005": {"noul_pii_prob": 0.05, "choice": 4, "choice_label": "anomalous", "choice_conf": 0.88, "score_tone": 3, "score_conf": 0.80},
        "act_006": {"noul_pii_prob": 0.00, "choice": 1, "choice_label": "read_only", "choice_conf": 0.98, "score_tone": 5, "score_conf": 0.90},
    }
    return mock_responses.get(action.action_id, {
        "noul_pii_prob": 0.10, "choice": 4, "choice_label": "anomalous", "choice_conf": 0.65, "score_tone": 3, "score_conf": 0.65
    })

# --- 3. MOTOR DE REGLAS DETERMINISTA (PROMPT & LOGIC) ---
@app.post("/evaluate_action", response_model=EvaluationResult)
async def evaluate_agent_action(action: AgentAction):
    jev_output = evaluate_with_jev(action)

    noul_pii = jev_output["noul_pii_prob"]
    choice = jev_output["choice"]
    choice_conf = jev_output["choice_conf"]
    score = jev_output["score_tone"]
    score_conf = jev_output["score_conf"]

    status = "APPROVED"
    reason = "Acción segura: Perfil con contexto suficiente y operación dentro de parámetros de 30X."

    # 1. Reglas de Bloqueo Total (Prioridad Crítica)
    if noul_pii > 0.50:
        status = "BLOCKED"
        reason = "Riesgo crítico: Exposición de PII o volcado no autorizado del CRM de 30X."
    elif choice == 3:
        status = "BLOCKED"
        reason = "Riesgo crítico: Operación masiva o destructiva sobre la base de perfiles/deals."

    # 2. Reglas de Escalamiento a Humano / LLM System 2 (Prioridad Media)
    elif status != "BLOCKED":
        if choice_conf < 0.70 or score_conf < 0.70:
            status = "ESCALATED"
            reason = "Revisión requerida: Baja confianza calibrada en la evaluación de JEV (<70%)."
        elif choice == 4:
            status = "ESCALATED"
            reason = "Revisión requerida: Operación anómala o perfil sin contexto suficiente (Nivel de info: Baja)."
        elif "email" in action.operation_type and score < 4:
            status = "ESCALATED"
            reason = "Revisión requerida: El tono del mensaje incumple el estándar ejecutivo de 30X."

    return EvaluationResult(
        status=status,
        reason=reason,
        jev_metrics=jev_output
    )