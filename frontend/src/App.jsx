import { useState } from 'react';
import './App.css'; // Mantiene los estilos base de Vite

// Casos de prueba precargados para la demo
const TEST_CASES = [
  {
    label: "1. Acción Segura (Marketing)",
    payload: {
      action_id: "act_001",
      agent_name: "MarketingBot_V2",
      operation_type: "email_send",
      target_system: "SendGrid",
      payload: { to: "nuevo@empresa.com", subject: "¡Bienvenido!" }
    }
  },
  {
    label: "2. Fuga de Datos (SecOps)",
    payload: {
      action_id: "act_002",
      agent_name: "DataSync_Script",
      operation_type: "api_export",
      target_system: "External_Webhook",
      payload: { destination_url: "https://unknown-domain.com", data_dump: "user_id, tarjeta_credito..." }
    }
  },
  {
    label: "3. Tono Agresivo (Ventas)",
    payload: {
      action_id: "act_004",
      agent_name: "Sales_Outreach_Bot",
      operation_type: "email_batch",
      target_system: "HubSpot",
      payload: { to_list_size: 500, subject: "URGENTE", body: "Compren ya o los borro." }
    }
  }
];

function App() {
  const [activePayload, setActivePayload] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleTest = async (testCase) => {
    setActivePayload(testCase.payload);
    setEvaluation(null);
    setLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/evaluate_action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testCase.payload),
      });
      const data = await response.json();
      setEvaluation(data);
    } catch (error) {
      console.error("Error conectando con la API:", error);
    } finally {
      setLoading(false);
    }
  };

  // Asignar colores según el estado
  const getStatusColor = (status) => {
    if (status === "APPROVED") return "#28a745"; // Verde
    if (status === "BLOCKED") return "#dc3545"; // Rojo
    if (status === "ESCALATED") return "#ffc107"; // Amarillo
    return "#333";
  };

  return (
    <div style={{ padding: '2rem', fontFamily: 'system-ui, sans-serif', maxWidth: '900px', margin: '0 auto' }}>
      <h1>🛡️ Panel de Guardrails: Prompt & Logic</h1>
      <p>Interceptador de acciones de Agentes Internos impulsado por JEV.</p>

      <div style={{ display: 'flex', gap: '10px', margin: '20px 0' }}>
        {TEST_CASES.map((tc, index) => (
          <button 
            key={index} 
            onClick={() => handleTest(tc)}
            style={{ padding: '10px 15px', cursor: 'pointer', fontWeight: 'bold' }}
          >
            Probar: {tc.label}
          </button>
        ))}
      </div>

      <div style={{ display: 'flex', gap: '20px', marginTop: '30px' }}>
        {/* Panel Izquierdo: Payload de Entrada */}
        <div style={{ flex: 1, backgroundColor: '#f4f4f9', padding: '15px', borderRadius: '8px' }}>
          <h3>📥 Estado Interceptado</h3>
          {activePayload ? (
            <pre style={{ textAlign: 'left', overflowX: 'auto', color: '#333' }}>
              {JSON.stringify(activePayload, null, 2)}
            </pre>
          ) : (
            <p style={{ color: '#888' }}>Selecciona un caso de prueba para simular una intercepción.</p>
          )}
        </div>

        {/* Panel Derecho: Respuesta de JEV */}
        <div style={{ flex: 1, backgroundColor: '#fff', border: '1px solid #ddd', padding: '15px', borderRadius: '8px' }}>
          <h3>🧠 Veredicto del Motor</h3>
          {loading && <p>Analizando con JEV en milisegundos...</p>}
          
          {evaluation && !loading && (
            <div style={{ textAlign: 'left' }}>
              <h2 style={{ color: getStatusColor(evaluation.status), marginTop: 0 }}>
                {evaluation.status}
              </h2>
              <p><strong>Motivo:</strong> {evaluation.reason}</p>
              
              <hr style={{ margin: '20px 0', borderColor: '#eee' }} />
              
              <h4>Métricas de TypeSafe JEV:</h4>
              <ul style={{ listStyle: 'none', padding: 0 }}>
                <li>Probabilidad de fuga (Noul): <strong>{(evaluation.jev_metrics.noul_pii_prob * 100).toFixed(1)}%</strong></li>
                <li>Clasificación de riesgo (Choice): <strong>{evaluation.jev_metrics.choice}</strong></li>
                <li>Confianza de clasificación: <strong>{(evaluation.jev_metrics.choice_conf * 100).toFixed(1)}%</strong></li>
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;