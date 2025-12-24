import mysql.connector
from mysql.connector import Error

def get_connection():
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            port = 8889,
            user="root",
            password="root",
            database="ocr-sdp"
        )

        if connection.is_connected():
            print("Connexion réussie")
            return connection

    except Error as e:
        print(f"Erreur de connexion : {e}")
        return None