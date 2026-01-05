"""
Script de test pour vérifier la connexion à la base de données
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_connection


def test_database_connection():
    """
    Test de connexion à la base de données
    """
    print("=" * 80)
    print("TEST DE CONNEXION À LA BASE DE DONNÉES")
    print("=" * 80)
    print()

    print("Tentative de connexion...")
    connection = get_connection()

    if connection:
        print("✅ Connexion réussie !")
        print(f"   Base de données connectée")

        # Tester une requête simple
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE()")
            db_name = cursor.fetchone()
            print(f"   Nom de la base : {db_name[0]}")

            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"   Nombre de tables : {len(tables)}")
            print(f"   Tables : {[table[0] for table in tables]}")

            cursor.close()
            connection.close()
            print("\n✅ Test de connexion réussi !")
        except Exception as e:
            print(f"\n❌ Erreur lors de l'exécution de la requête : {e}")
    else:
        print("❌ Échec de la connexion !")
        print("\nVérifie les paramètres de connexion dans app/database/connection.py")

    print("=" * 80)


if __name__ == "__main__":
    test_database_connection()
