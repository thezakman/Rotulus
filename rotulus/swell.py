import argparse
import signal
import sys

from rotulus.database import db_connect, execute_query
from rotulus.query import get_hash_types


def signal_handler(signal, frame):
    sys.exit(0)


def parse_cli():
    parser = argparse.ArgumentParser(description='Improve data relation')
    parser.add_argument('-f', '--find', action='store_true',
                        help='Find clear password of a hashes')
    parser.add_argument('-a', '--hash', action='store_true',
                        help='Hash all passwords using hash types present in database')
    args = parser.parse_args()

    if args.find:
        associate_hash_to_clear()
    elif args.hash:
        hash_all_passwords()


def associate_hash_to_clear():
    connection = db_connect()
    if connection != False:
        hash_types = get_hash_types(connection)
        for hash_type in hash_types:
            query = 'with ins1 as ( \
                select distinct password_id, {}_id \
                from rotulus.records \
                where password_id is not null and {}_id is not null) \
                update rotulus.records r \
                set password_id = ( \
                    select password_id from ins1 \
                    where {}_id = r.{}_id) \
                where password_id is null'.format(hash_type, hash_type, hash_type, hash_type)
            execute_query(connection, query)
            print("[*] {} hashes has been associated with their clear".format(hash_type.upper()))


def passwords_not_hashed(connection, hash_type):
    cur = connection.cursor()
    query = 'select id from rotulus.records where {}_id is null'.format(hash_type)
    cur.execute(query)
    return cur.fetchone()


def hash_passwords_to_md5(connection):
    query = 'with ins1 as ( \
        insert into rotulus.md5_hashes (hash) \
        select md5(password) from rotulus.passwords p \
        inner join rotulus.records r on p.id = r.password_id \
            where r.md5_id is null limit 1 \
        on conflict (hash) do update set hash=excluded.hash returning id as hash_id) \
        update rotulus.records \
        set md5_id = (select hash_id from ins1) \
            where id = (select id from rotulus.records where md5_id is null limit 1)'
    while passwords_not_hashed(connection, 'md5') != None:
        execute_query(connection, query)


def hash_all_passwords():
    connection = db_connect()
    if connection != False:
        hash_types = get_hash_types(connection)
        for hash_type in hash_types:
            if hash_type[0] == 'md5':
                hash_passwords_to_md5(connection)
                print("[*] All passwords has been hashes to MD5")
            else:
                print("[*] Issue a ticket to implement {}".format(hash_type.upper())) 


def main():
    signal.signal(signal.SIGINT, signal_handler)
    parse_cli()


if __name__ == "__main__":
    main()
