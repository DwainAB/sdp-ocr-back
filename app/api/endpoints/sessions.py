from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
import json

from app.repositories import session_repository
from app.schemas.session_schemas import (
    SessionCreate,
    SessionResponse,
    AssignSupervisorRequest,
    SingleAnswerUpdate,
    SessionAnswersUpdate,
    SessionDetailResponse,
    AnswerEntry,
)

router = APIRouter()


# ── Gestionnaire de connexions temps réel ──
class ConnectionManager:
    """Maintient une liste de WebSocket par session pour le broadcast temps réel."""

    def __init__(self):
        self.active: dict[int, list[WebSocket]] = {}

    async def connect(self, session_id: int, ws: WebSocket):
        await ws.accept()
        if session_id not in self.active:
            self.active[session_id] = []
        self.active[session_id].append(ws)

    def disconnect(self, session_id: int, ws: WebSocket):
        if session_id in self.active:
            self.active[session_id].remove(ws)
            if not self.active[session_id]:
                del self.active[session_id]

    async def broadcast(self, session_id: int, message: str):
        for ws in self.active.get(session_id, []):
            try:
                await ws.send_text(message)
            except Exception:
                pass


manager = ConnectionManager()


# ── REST endpoints ──

@router.post("/sessions", response_model=dict)
async def create_session(payload: SessionCreate):
    session_id = session_repository.create_session(
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
    )
    if not session_id:
        raise HTTPException(status_code=500, detail="Erreur creation session")
    return {"session_id": session_id}


@router.patch("/sessions/{session_id}/cancel")
async def cancel_session(session_id: int):
    ok = session_repository.update_session_status(session_id, "cancelled")
    if not ok:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return {"status": "cancelled"}


@router.patch("/sessions/{session_id}/complete")
async def complete_session(session_id: int):
    ok = session_repository.update_session_status(session_id, "completed")
    if not ok:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return {"status": "completed"}


@router.patch("/sessions/{session_id}/assign-supervisor")
async def assign_supervisor(session_id: int, payload: AssignSupervisorRequest):
    ok = session_repository.assign_supervisor_to_session(session_id, payload.supervisor_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return {"status": "assigned", "supervisor_id": payload.supervisor_id}


@router.get("/sessions/active", response_model=list[SessionResponse])
async def list_active_sessions():
    sessions = session_repository.get_active_sessions()
    return [SessionResponse(**s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(session_id: int):
    session = session_repository.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")
    answers = session_repository.get_answers(session_id)
    return SessionDetailResponse(
        session=SessionResponse(**session),
        answers=[AnswerEntry(**a) for a in answers],
    )


@router.put("/sessions/{session_id}/answers")
async def update_session_answers(session_id: int, payload: SessionAnswersUpdate):
    for entry in payload.answers:
        ok, err = session_repository.upsert_answer(session_id, entry.question_key, str(entry.answer_value))
        if not ok:
            raise HTTPException(status_code=500, detail=f"Erreur mise a jour reponse: {err}")
    return {"status": "updated"}


@router.post("/sessions/{session_id}/answer")
async def update_single_answer(session_id: int, payload: SingleAnswerUpdate):
    ok, err = session_repository.upsert_answer(session_id, payload.question_key, str(payload.answer_value))
    if not ok:
        raise HTTPException(status_code=500, detail=f"Erreur mise a jour reponse: {err}")
    msg = json.dumps({"question_key": payload.question_key, "answer_value": payload.answer_value})
    await manager.broadcast(session_id, msg)
    return {"status": "updated"}


# ── WebSocket endpoint (temps réel) ──

@router.websocket("/ws/session/{session_id}")
async def websocket_endpoint(ws: WebSocket, session_id: int):
    session = session_repository.get_session_by_id(session_id)
    if not session:
        await ws.close(code=4004)
        return

    await manager.connect(session_id, ws)
    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)
            qk = msg.get("question_key")
            av = msg.get("answer_value")
            if qk is not None and av is not None:
                session_repository.upsert_answer(session_id, qk, str(av))
                broadcast = json.dumps({"question_key": qk, "answer_value": av})
                await manager.broadcast(session_id, broadcast)
    except WebSocketDisconnect:
        manager.disconnect(session_id, ws)
    except Exception:
        manager.disconnect(session_id, ws)
