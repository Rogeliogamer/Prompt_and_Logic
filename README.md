# 🛡️ Prompt & Logic - Guardrails para Agentes Internos

**Reto 30X:** JEV (TypeSafe AI)  
**Equipo:** Prompt & Logic

Este repositorio contiene el prototipo funcional de un **Interceptor de Seguridad (Guardrail)** para agentes autónomos. Utiliza el modelo **TypeSafe JEV** (System One) para evaluar en milisegundos las operaciones que intentan ejecutar los agentes internos (bots, scripts, o IAs generativas), previniendo fugas de datos, operaciones destructivas o comunicaciones no alineadas.

---

## 🧠 ¿Cómo funciona la toma de decisiones?

Antes de que un agente ejecute una acción (ej. un `DELETE` en la base de datos o enviar un correo masivo), el payload pasa por nuestro motor en FastAPI, el cual envía **tres preguntas en paralelo a JEV**:

1. **Noul (Sí/No):** *¿Esta acción expone PII (Información Personal Identificable) o datos financieros?*
2. **Choice (Clasificación):** *Clasifica el riesgo de la operación: [1] Lectura [2] Modificación Segura [3] Destructiva [4] Anómalo.*
3. **Score (Puntuación):** *Del 1 al 5, ¿qué tan alineado está el tono corporativo?*

### 🚦 El Enrutador (Lógica)
Con las respuestas deterministas y las probabilidades calibradas de JEV, nuestro código enruta la acción:
* 🟢 **Auto-Aprobación:** Acciones de lectura o modificaciones seguras con alta confianza (`> 0.85`) y sin fuga de datos.
* 🔴 **Bloqueo Total:** Detección de fuga de datos (probabilidad `> 0.50`) o acciones destructivas/masivas no autorizadas.
* 🟡 **Escalamiento a Humano:** Decisiones anómalas, tono corporativo bajo (`< 4`) o clasificaciones donde JEV reporta baja confianza (`< 0.70`).

---

## 🏗️ Arquitectura del Prototipo

* **Backend:** `FastAPI` (Python) - Actúa como el enrutador asíncrono y se comunica con la API de JEV.
* **Frontend:** `React + Vite` - Panel de control (Dashboard) de SecOps para visualizar las interceptaciones en tiempo real.
* **Manejo de Estado:** Payloads simulados en formato JSON estructurado.

---

## 🚀 Instrucciones de Instalación y Despliegue

### Requisitos Previos
* Python 3.9 o superior
* Node.js 18 o superior

### 1. Levantar el Backend (FastAPI)
Abre una terminal, navega a la carpeta del backend y ejecuta:
```bash
cd backend
python -m venv venv
# Activar entorno (Windows)
.\venv\Scripts\activate
# Instalar dependencias
pip install fastapi uvicorn pydantic
# Iniciar el servidor
uvicorn main:app --reload
```
La API estará corriendo en [http://127.0.0.1:8000](http://127.0.0.1:8000)

### 2. Levantar el Frontend (React)
Abre una nueva terminal en la raíz del proyecto y ejecuta:
```cd frontend
npm install
npm run dev
```
El panel interactivo estará disponible en http://localhost:5173

## 🧪 Cómo probar el prototipo
En el panel web encontrarás botones con casos de prueba precargados que envían peticiones HTTP reales al backend:

1. Acción Segura: Simula un correo estándar de bienvenida (Debería resultar en APPROVED).

2. Fuga de Datos: Simula un intento de exportar tarjetas de crédito a un webhook externo (Debería resultar en BLOCKED).

3. Tono Agresivo: Simula un correo masivo de ventas con un tono no profesional (Debería resultar en ESCALATED).

Nota para los jueces: El proyecto utiliza datos simulados y no procesa información real de 30X, cumpliendo con las restricciones del reto.