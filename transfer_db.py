#!/usr/bin/env python3
"""
Script de transfert de la base Hostinger -> Railway
Copie toutes les tables, structures et données.
"""

import pymysql
from pymysql.cursors import DictCursor
import time

SRC_HOST = "hayabusa.proxy.rlwy.net"
SRC_PORT = 48407
SRC_USER = "root"
SRC_PASS = "FyLZUxjrjEKlFdOXnUHqJWclKKiARzVE"
SRC_DB   = "railway"

DST_HOST = "sakura.proxy.rlwy.net"
DST_PORT = 18139
DST_USER = "root"
DST_PASS = "EdMdDyEScLfgbzeQjUcdiZVLYRPdvxtt"
DST_DB   = "railway"


def connect_src():
    return pymysql.connect(
        host=SRC_HOST, port=SRC_PORT, user=SRC_USER,
        password=SRC_PASS, database=SRC_DB,
        cursorclass=DictCursor,
        autocommit=True,
        connect_timeout=10,
        read_timeout=30,
        write_timeout=30,
    )


def connect_dst():
    return pymysql.connect(
        host=DST_HOST, port=DST_PORT, user=DST_USER,
        password=DST_PASS, database=DST_DB,
        cursorclass=DictCursor,
        autocommit=True,
        connect_timeout=10,
        read_timeout=30,
        write_timeout=30,
    )


def get_tables(conn):
    with conn.cursor() as cur:
        cur.execute("SHOW TABLES")
        rows = cur.fetchall()
        key = list(rows[0].keys())[0] if rows else None
        return [row[key] for row in rows]


def get_create_table(conn, table):
    with conn.cursor() as cur:
        cur.execute(f"SHOW CREATE TABLE `{table}`")
        row = cur.fetchone()
        return row["Create Table"]


def get_row_count(conn, table):
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) as cnt FROM `{table}`")
        return cur.fetchone()["cnt"]


def get_all_data_src(table):
    """Lit toutes les données d'une table Hostinger avec sa propre connexion."""
    conn = connect_src()
    rows = []
    offset = 0
    batch_size = 500
    with conn.cursor() as cur:
        while True:
            cur.execute(f"SELECT * FROM `{table}` LIMIT {batch_size} OFFSET {offset}")
            batch = cur.fetchall()
            if not batch:
                break
            rows.extend(batch)
            offset += batch_size
            print(f"    ⏫ Récupéré {offset} lignes de {table}...")
    conn.close()
    return rows


def drop_all_tables(conn, tables):
    with conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        for table in reversed(tables):
            cur.execute(f"DROP TABLE IF EXISTS `{table}`")
    print("   ✅ Toutes les tables supprimées")


def create_table(conn, create_stmt):
    with conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        cur.execute(create_stmt)
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")


def insert_data(conn, table, columns, rows, batch_size=50):
    if not columns or not rows:
        return 0

    placeholders = ", ".join(["%s"] * len(columns))
    cols_fmt = ", ".join([f"`{c}`" for c in columns])
    sql = f"INSERT IGNORE INTO `{table}` ({cols_fmt}) VALUES ({placeholders})"

    inserted = 0
    with conn.cursor() as cur:
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            values = [tuple(row[col] for col in columns) for row in batch]
            
            retries = 3
            while retries > 0:
                try:
                    cur.executemany(sql, values)
                    inserted += len(batch)
                    if inserted % 1000 == 0 or inserted == len(rows):
                        print(f"    → {inserted}/{len(rows)} lignes insérées...")
                    break
                except Exception as e:
                    retries -= 1
                    if retries == 0:
                        print(f"    ✗ ERREUR: {e}")
                        for row_vals in values:
                            try:
                                cur.execute(sql, row_vals)
                                inserted += 1
                            except:
                                pass
                    else:
                        print(f"    ⚠️ Timeout, reprise ({retries})...")
                        time.sleep(1)
                        try:
                            conn.ping(reconnect=True)
                        except:
                            pass
    return inserted


def main():
    print("═" * 60)
    print("TRANSFERT RAILWAY → RAILWAY")
    print("═" * 60)

    # PHASE 1 : Connexion et listage
    src = connect_src()
    tables = get_tables(src)
    print(f"\n📋 Tables: {len(tables)}")
    for t in tables:
        print(f"   - {t} ({get_row_count(src, t)} lignes)")
    src.close()

    # PHASE 2 : Création des tables sur Railway
    print("\n" + "═" * 60)
    print("PHASE 1 : CRÉATION DES TABLES")
    print("═" * 60)
    
    dst = connect_dst()
    drop_all_tables(dst, tables)
    
    src = connect_src()
    create_stmts = {}
    for table in tables:
        create_stmts[table] = get_create_table(src, table)
    src.close()

    for table in tables:
        try:
            create_table(dst, create_stmts[table])
            print(f"   ✅ {table} créée")
        except Exception as e:
            print(f"   ❌ {table} : {e}")
    dst.close()

    # PHASE 3 : Copie des données table par table
    print("\n" + "═" * 60)
    print("PHASE 2 : COPIE DES DONNÉES")
    print("═" * 60)
    
    dst = connect_dst()
    with dst.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    
    total_rows = 0
    for table in tables:
        print(f"\n📦 {table}")
        rows = get_all_data_src(table)
        
        if rows:
            columns = list(rows[0].keys())
            print(f"   🔄 {len(rows)} lignes...")
            inserted = insert_data(dst, table, columns, rows)
            total_rows += inserted
            print(f"   ✅ {inserted}/{len(rows)}")
        else:
            print(f"   📭 Table vide")
        
        # Petite pause entre les tables
        time.sleep(1)
    
    with dst.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    dst.close()

    # PHASE 4 : Vérification
    print("\n" + "═" * 60)
    print("PHASE 3 : VÉRIFICATION")
    print("═" * 60)

    dst = connect_dst()
    src = connect_src()
    all_ok = True
    
    for t in tables:
        sc = get_row_count(src, t)
        dc = get_row_count(dst, t)
        status = "✅" if sc == dc else "⚠️"
        print(f"   {status} {t}: Hostinger={sc}, Railway={dc}")
        if sc != dc:
            all_ok = False

    src.close()
    dst.close()

    print("\n" + "═" * 60)
    if all_ok:
        print("✅ TRANSFERT RÉUSSI !")
    else:
        print("⚠️  TRANSFERT AVEC INCOHÉRENCES")
    print(f"   {total_rows} lignes copiées")
    print("═" * 60)


if __name__ == "__main__":
    main()