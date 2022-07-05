from flask import g
import psycopg2
from psycopg2.extras import DictCursor


def connect_db():
    conn = psycopg2.connect('', cursor_factory=DictCursor)
    conn.autocommit = True
    sql = conn.cursor()
    return conn, sql


def get_db():
    db = connect_db()

    if not hasattr(g, 'postgre_db_conn'):
        g.postgre_db_conn = db[0]
    if not hasattr(g, 'postgre_db_cur'):
        g.postgre_db_cur = db[1]

    return g.postgre_db_cur


def init_db():
    db = connect_db()
    db[1].execute(open('schema.sql', 'r').read())
    db[1].close()
    db[0].close()


def init_admin():
    db = connect_db()
    db[1].execute('UPDATE users set admin = True WHERE name = %s', ('Thamas', ))
    db[1].close()
    db[0].close()