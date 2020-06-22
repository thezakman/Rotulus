import argparse
import asyncio
import base64
import signal
import sys

import asyncpg
import psycopg2
import psycopg2.extras

from database import get_db_conf
from record import Record


def parse_cli():
    parser = argparse.ArgumentParser(
        description='Query Rotulus database')
    parser.add_argument('-s', '--search',
                        choices=['username', 'domain',
                                 'password', 'hash', 'hash_type'],
                        required=True,
                        help='Search particular value in defined colum')
    parser.add_argument('-e', '--equal',
                        help='Match string')
    parser.add_argument('-c', '--contain',
                        help='Contain string')
    return parser.parse_args()


def signal_handler(signal, frame):
    print('[-] Stopping the query')
    sys.exit(0)

def db_connect():
    db_conf = get_db_conf()
    if db_conf != False:
        try:
            con = psycopg2.connect(user=db_conf["psql"]["username"],
                                   password=db_conf["psql"]["password"],
                                   host=db_conf["psql"]["host"],
                                   port=db_conf["psql"]["port"],
                                   database=db_conf["psql"]["dbname"])
            return con
        except:
            print("[!] Error while connecting to PostgreSQL")
            return False
    else:
        return False


async def select_record_count(connection):
    query = '''select count(*) from rotulus.records'''
    statement = await connection.prepare(query)
    return await statement.fetchval()


def select_record_from_username_id(connection, record_id):
    cur = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = '''select username, domain, password, hash, hash_type 
            from rotulus.usernames u 
            inner join rotulus.records r 
                on u.id = r.username_id 
            inner join rotulus.domains d 
                on r.domain_id = d.id 
            inner join rotulus.passwords p 
                on r.password_id = p.id 
            inner join rotulus.hashes h 
                on r.hash_id = h.id 
            inner join rotulus.hashes_types t 
                on h.hash_type_id = t.id 
            where r.username_id = %s'''
    cur.execute(query, (record_id,))
    record = cur.fetchone()
    yield record


def select_record_from_domain_id(connection, record_id):
    cur = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = '''select username, domain, password, hash, hash_type 
            from rotulus.usernames u 
            inner join rotulus.records r 
                on u.id = r.username_id 
            inner join rotulus.domains d 
                on r.domain_id = d.id 
            inner join rotulus.passwords p 
                on r.password_id = p.id 
            inner join rotulus.hashes h 
                on r.hash_id = h.id 
            inner join rotulus.hashes_types t 
                on h.hash_type_id = t.id 
            where r.domain_id = %s'''
    cur.execute(query, (record_id,))
    record = cur.fetchone()
    yield record


def select_record_from_password_id(connection, record_id):
    cur = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = '''select username, domain, password, hash, hash_type 
            from rotulus.usernames u 
            inner join rotulus.records r 
                on u.id = r.username_id 
            inner join rotulus.domains d 
                on r.domain_id = d.id 
            inner join rotulus.passwords p 
                on r.password_id = p.id 
            inner join rotulus.hashes h 
                on r.hash_id = h.id 
            inner join rotulus.hashes_types t 
                on h.hash_type_id = t.id 
            where r.domain_id = %s'''
    cur.execute(query, (record_id,))
    record = cur.fetchone()
    yield record


def select_record_from_hash_id(connection, record_id):
    cur = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = '''select username, domain, password, hash, hash_type 
            from rotulus.usernames u 
            inner join rotulus.records r 
                on u.id = r.username_id 
            inner join rotulus.domains d 
                on r.domain_id = d.id 
            inner join rotulus.passwords p 
                on r.password_id = p.id 
            inner join rotulus.hashes h 
                on r.hash_id = h.id 
            inner join rotulus.hashes_types t 
                on h.hash_type_id = t.id 
            where r.domain_id = %s'''
    cur.execute(query, (record_id,))
    record = cur.fetchone()
    yield record


def select_record_from_hash_type_id(connection, record_id):
    cur = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = '''select username, domain, password, hash, hash_type 
            from rotulus.usernames u 
            inner join rotulus.records r 
                on u.id = r.username_id 
            inner join rotulus.domains d 
                on r.domain_id = d.id 
            inner join rotulus.passwords p 
                on r.password_id = p.id 
            inner join rotulus.hashes h 
                on r.hash_id = h.id 
            inner join rotulus.hashes_types t 
                on h.hash_type_id = t.id 
            where r.domain_id = %s'''
    cur.execute(query, (record_id,))
    record = cur.fetchone()
    yield record


def select_username(connection, username):
    cur = connection.cursor()
    query = '''select r.id from rotulus.records r 
            inner join rotulus.usernames u 
                on r.username_id = u.id 
            where u.username like %s'''
    cur.execute(query, (username,))
    records = cur.fetchall()
    return records


def select_domain(connection, domain):
    cur = connection.cursor()
    query = '''select r.id from rotulus.records r 
            inner join rotulus.domains d
                on r.domain_id = d.id 
            where d.domain like %s'''
    cur.execute(query, (domain,))
    records = cur.fetchall()
    return records


def select_password(connection, password):
    cur = connection.cursor()
    query = '''select r.id from rotulus.records r 
            inner join rotulus.passwords p 
                on r.password_id = p.id 
            where p.password like %s'''
    cur.execute(query, (password,))
    records = cur.fetchall()
    return records


def select_hash(connection, hash):
    cur = connection.cursor()
    query = '''select r.id from rotulus.records r 
            inner join rotulus.hashes h 
                on r.hash_id = h.id 
            where h.hash like %s'''
    cur.execute(query, (hash,))
    records = cur.fetchall()
    return records


def select_hash_type(connection, hash_type):
    cur = connection.cursor()
    query = '''select r.id from rotulus.records r 
            inner join rotulus.hashes_types t 
                on r.hash_id = t.id 
            where t.hash_type like %s'''
    cur.execute(query, (hash_type,))
    records = cur.fetchall()
    return records


def search_username(connection, username):
    usernames_records = select_username(connection, username)
    usernames_id = [record[0] for record in usernames_records]
    for username_id in usernames_id:
        rows = select_record_from_username_id(connection, username_id)
        for row in rows:
            print_record(row)


def search_domain(connection, domain):
    domains_records = select_domain(connection, domain)
    domains_id = [record[0] for record in domains_records]
    for domain_id in domains_id:
        rows = select_record_from_domain_id(connection, domain_id)
        for row in rows:
            print_record(row)


def search_password(connection, password):
    passwords_records = select_password(connection, password)
    passwords_id = [record[0] for record in passwords_records]
    for password_id in passwords_id:
        rows = select_record_from_password_id(connection, password_id)
        for row in rows:
            print_record(row)


def search_hash(connection, hash):
    hashes_records = select_hash(connection, hash)
    hashes_id = [record[0] for record in hashes_records]
    for hash_id in hashes_id:
        rows = select_record_from_hash_id(connection, hash_id)
        for row in rows:
            print_record(row)


def search_hash_type(connection, hash_type):
    hashes_types_records = select_hash(connection, hash_type)
    hashes_types_id = [record[0] for record in hashes_types_records]
    for hash_type_id in hashes_types_id:
        rows = select_record_from_hash_type_id(connection, hash_type_id)
        for row in rows:
            print_record(row)


def print_record(row):
    if row:
        record = Record()
        record.set_username(row[0].tobytes())
        record.set_domain(row[1].tobytes())
        record.set_password(row[2].tobytes())
        record.set_password_hash(row[3])
        record.set_hash_type(row[4])
        print(record)


def query(args):
    connection = db_connect()
    if connection == False:
        return
    if args.search == 'username':
        if args.equal:
            char = args.equal.encode()
            search_username(connection, char)
        elif args.contain:
            char = b'%' + args.contain.encode() + b'%'
            search_username(connection, char)
    elif args.search == 'domain':
        if args.equal:
            char = args.equal.encode()
            search_domain(connection, char)
        elif args.contain:
            char = b'%' + args.contain.encode() + b'%'
            search_domain(connection, char)
    elif args.search == 'password':
        if args.equal:
            char = args.equal.encode()
            search_password(connection, char)
        elif args.contain:
            char = b'%' + args.contain.encode() + b'%'
            search_password(connection, char)
    elif args.search == 'hash':
        if args.equal:
            char = args.equal.encode()
            search_hash(connection, char)
        elif args.contain:
            char = b'%' + args.contain.encode() + b'%'
            search_hash(connection, char)
    elif args.search == 'hash_type':
        if args.equal:
            char = args.equal.encode()
            search_hash_type(connection, char)
        elif args.contain:
            char = b'%' + args.contain.encode() + b'%'
            search_hash_type(connection, char)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    query(parse_cli())
