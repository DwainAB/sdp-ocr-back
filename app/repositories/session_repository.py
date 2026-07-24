from typing import Optional

from app.database import get_connection
from app.crud import crud_session


def create_session(
    customer_name: Optional[str] = None,
    customer_email: Optional[str] = None,
) -> Optional[int]:
    conn = get_connection()
    if not conn:
        return None
    try:
        return crud_session.create(conn, customer_name, customer_email)
    finally:
        conn.close()


def get_active_sessions() -> list[dict]:
    conn = get_connection()
    if not conn:
        return []
    try:
        return crud_session.get_active(conn)
    finally:
        conn.close()


def get_session_by_id(session_id: int) -> Optional[dict]:
    conn = get_connection()
    if not conn:
        return None
    try:
        return crud_session.get_by_id(conn, session_id)
    finally:
        conn.close()


def assign_supervisor_to_session(session_id: int, supervisor_id: int) -> bool:
    conn = get_connection()
    if not conn:
        return False
    try:
        return crud_session.assign_supervisor(conn, session_id, supervisor_id)
    finally:
        conn.close()


def update_session_status(session_id: int, status: str) -> bool:
    conn = get_connection()
    if not conn:
        return False
    try:
        return crud_session.update_status(conn, session_id, status)
    finally:
        conn.close()


def upsert_answer(
    session_id: int,
    question_key: str,
    answer_value: str,
) -> tuple[bool, str]:
    conn = get_connection()
    if not conn:
        return False, "Pas de connexion BDD"
    try:
        return crud_session.upsert_answer(conn, session_id, question_key, answer_value)
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def get_answers(session_id: int) -> list[dict]:
    conn = get_connection()
    if not conn:
        return []
    try:
        return crud_session.get_answers(conn, session_id)
    finally:
        conn.close()
