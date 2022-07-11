from flask import g
import psycopg2
from psycopg2.extras import DictCursor


def connect_db():
    conn = psycopg2.connect('postgres://ocjcrguftgoypt:8612cf1e6bec3162fc48f83833d15be511fa06d31fb9dcc245de913d891ee740@ec2-44-198-82-71.compute-1.amazonaws.com:5432/ddnpodl1muefbm', cursor_factory=DictCursor)
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
    db[1].execute('UPDATE users SET admin = True WHERE name = %s', ('Thamas', ))
    db[1].close()
    db[0].close()
