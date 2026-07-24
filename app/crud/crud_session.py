from typing import Optional
import pymysql


def create(
    connection: pymysql.connections.Connection,
    customer_name: Optional[str] = None,
    customer_email: Optional[str] = None,
) -> Optional[int]:
    cursor = None
    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO sessions (customer_name, customer_email, status)
            VALUES (%s, %s, 'active')
        """
        cursor.execute(query, (customer_name, customer_email))
        connection.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Erreur creation session : {e}")
        connection.rollback()
        return None
    finally:
        if cursor:
            cursor.close()


def get_active(connection: pymysql.connections.Connection) -> list[dict]:
    cursor = None
    try:
        cursor = connection.cursor()
        query = """
            SELECT s.id, s.customer_name, s.customer_email, s.status,
                   s.started_at, s.updated_at, s.supervisor_id,
                   CONCAT(u.first_name, ' ', u.last_name) AS supervisor_name
            FROM sessions s
            LEFT JOIN users u ON u.id = s.supervisor_id
            WHERE s.status = 'active'
            ORDER BY s.updated_at DESC, s.started_at DESC
        """
        cursor.execute(query)
        return cursor.fetchall() or []
    except Exception as e:
        print(f"Erreur recuperation sessions actives : {e}")
        return []
    finally:
        if cursor:
            cursor.close()


def get_by_id(
    connection: pymysql.connections.Connection,
    session_id: int,
) -> Optional[dict]:
    cursor = None
    try:
        cursor = connection.cursor()
        query = """
            SELECT s.id, s.customer_name, s.customer_email, s.status,
                   s.started_at, s.updated_at, s.supervisor_id,
                   CONCAT(u.first_name, ' ', u.last_name) AS supervisor_name
            FROM sessions s
            LEFT JOIN users u ON u.id = s.supervisor_id
            WHERE s.id = %s
        """
        cursor.execute(query, (session_id,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Erreur recuperation session {session_id} : {e}")
        return None
    finally:
        if cursor:
            cursor.close()


def assign_supervisor(
    connection: pymysql.connections.Connection,
    session_id: int,
    supervisor_id: int,
) -> bool:
    cursor = None
    try:
        cursor = connection.cursor()
        query = "UPDATE sessions SET supervisor_id = %s, updated_at = NOW() WHERE id = %s"
        cursor.execute(query, (supervisor_id, session_id))
        connection.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Erreur assignation superviseur session {session_id} : {e}")
        connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()


def update_status(
    connection: pymysql.connections.Connection,
    session_id: int,
    status: str,
) -> bool:
    cursor = None
    try:
        cursor = connection.cursor()
        query = "UPDATE sessions SET status = %s, updated_at = NOW() WHERE id = %s"
        cursor.execute(query, (status, session_id))
        connection.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Erreur mise a jour session {session_id} : {e}")
        connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()


def upsert_answer(
    connection: pymysql.connections.Connection,
    session_id: int,
    question_key: str,
    answer_value: str,
) -> tuple[bool, str]:
    cursor = None
    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO session_answers (session_id, question_key, answer_value, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE answer_value = %s, updated_at = NOW()
        """
        cursor.execute(query, (session_id, question_key, answer_value, answer_value))
        cursor.execute("UPDATE sessions SET updated_at = NOW() WHERE id = %s", (session_id,))
        connection.commit()
        return True, ""
    except Exception as e:
        msg = f"Erreur upsert answer {session_id}/{question_key} : {e}"
        print(msg)
        connection.rollback()
        return False, msg
    finally:
        if cursor:
            cursor.close()


def get_answers(
    connection: pymysql.connections.Connection,
    session_id: int,
) -> list[dict]:
    cursor = None
    try:
        cursor = connection.cursor()
        query = """
            SELECT question_key, answer_value, updated_at
            FROM session_answers
            WHERE session_id = %s
            ORDER BY updated_at ASC
        """
        cursor.execute(query, (session_id,))
        return cursor.fetchall() or []
    except Exception as e:
        print(f"Erreur recuperation reponses session {session_id} : {e}")
        return []
    finally:
        if cursor:
            cursor.close()
