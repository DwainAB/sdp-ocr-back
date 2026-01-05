"""
Test simple de connexion à la base de données
"""
import pymysql
from pymysql import MySQLError

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
        'cursorclass': pymysql.cursors.DictCursor,
        'connect_timeout': 5
    }

    print(f"Host: {config['host']}:{config['port']}")
    print(f"User: {config['user']}")
    print(f"Database: {config['database']}")
    print()
    print("Tentative de connexion...")

    try:
        connection = pymysql.connect(**config)

        if connection.open:
            print("✅ Connexion réussie !")

            # Tester une requête simple
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE()")
            db_name = cursor.fetchone()
            print(f"   Base de données connectée : {db_name['DATABASE()']}")

            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"   Version MySQL : {version['VERSION()']}")

            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"   Nombre de tables : {len(tables)}")
            if tables:
                # Récupérer le nom de la table depuis le dictionnaire
                table_key = list(tables[0].keys())[0] if tables else None
                print(f"   Tables : {[table[table_key] for table in tables[:5]]}")

            cursor.close()
            connection.close()
            print("\n✅ Test de connexion terminé avec succès !")
        else:
            print("❌ Connexion échouée (pas d'erreur mais pas connecté)")

    except MySQLError as e:
        print(f"❌ Erreur de connexion MySQL : {e}")
        if hasattr(e, 'args') and len(e.args) >= 2:
            print(f"   Code erreur : {e.args[0]}")
            print(f"   Message : {e.args[1]}")

    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")

    print("=" * 80)

if __name__ == "__main__":
    test_connection()
