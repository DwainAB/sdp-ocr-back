"""
Test simple de connexion à la base de données
"""
import mysql.connector
from mysql.connector import Error

def test_connection():
    print("=" * 80)
    print("TEST DE CONNEXION À LA BASE DE DONNÉES")
    print("=" * 80)
    print()

    # Paramètres de connexion
    config = {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'u440859155_dwain_sdp',
        'password': 'Daventys93110@',
        'database': 'u440859155_sdp_test',
        'connection_timeout': 5
    }

    print(f"Host: {config['host']}:{config['port']}")
    print(f"User: {config['user']}")
    print(f"Database: {config['database']}")
    print()
    print("Tentative de connexion...")

    try:
        connection = mysql.connector.connect(**config)

        if connection.is_connected():
            print("✅ Connexion réussie !")

            # Tester une requête simple
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE()")
            db_name = cursor.fetchone()
            print(f"   Base de données connectée : {db_name[0]}")

            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"   Version MySQL : {version[0]}")

            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"   Nombre de tables : {len(tables)}")
            if tables:
                print(f"   Tables : {[table[0] for table in tables[:5]]}")

            cursor.close()
            connection.close()
            print("\n✅ Test de connexion terminé avec succès !")
        else:
            print("❌ Connexion échouée (pas d'erreur mais pas connecté)")

    except Error as e:
        print(f"❌ Erreur de connexion MySQL : {e}")
        print(f"   Code erreur : {e.errno}")
        print(f"   Message : {e.msg}")

    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")

    print("=" * 80)

if __name__ == "__main__":
    test_connection()
