import pymysql
from pymysql import MySQLError


def get_connection():
    try:
        connection = pymysql.connect(
            host="srv1420.hstgr.io",
            port=3306,
            user="u440859155_dwain_sdp",
            password="Daventys93110@",
            database="u440859155_sdp_test",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )

        print("Connexion MySQL réussie (PyMySQL)")
        return connection

    except MySQLError as e:
        print(f"Erreur de connexion MySQL : {e}")
        return None
