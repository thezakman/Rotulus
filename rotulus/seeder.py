import argparse
import asyncio
import hashlib
import os
import signal
import sys
import time

from rotulus.database import async_db_connect, db_connect, create_hash_table, close_communication, alter_records_table
from rotulus.hashid import get_hash_type
from rotulus.query import select_record_count, hash_type_known
from rotulus.record import Record


def signal_handler(signal, frame):
    print('[-] Stopping the query')
    sys.exit(0)


def parse_cli():
    parser = argparse.ArgumentParser(
        description='Insert data in Rotulus database')
    parser.add_argument('-f', '--file',
                        required=True,
                        help='One or more files containing email address, password or hash',
                        type=argparse.FileType('rb'),
                        nargs='+')
    parser.add_argument('-s', '--spliter',
                        required=True,
                        type=os.fsencode,
                        help='Character to split line')
    parser.add_argument('-a', '--hash',
                        action='store_true',
                        help='Use it if passwords are hashed')
    parser.add_argument('-c', '--cipher',
                        help='Set cipher hash type')

    return parser.parse_args()


def write_errors(errors):
    f_name = 'errors_{}.txt'.format(time.strftime('%Y%m%d%H%M%S'))
    with open(f_name, 'wb') as file:
        for data in errors:
            try:
                if not data.endswith(b'\n'):
                    data += b'\n'
            except:
                pass
            try:
                record = data.encode()
            except:
                record = data
            try:
                file.write(record)
            except:
                print('[!] {}'.format(record))
                continue
    print('[+] Errors writed to ./{}'.format(f_name))


async def insert_records_with_passwords(connection, records):
    statement = '''WITH ins1 AS ( \
                INSERT INTO rotulus.usernames (username) VALUES ($1) \
                ON CONFLICT (username) DO UPDATE SET username=EXCLUDED.username \
                RETURNING id AS username_id) \
            , ins2 AS ( \
                INSERT INTO rotulus.domains (domain) VALUES ($2) \
                ON CONFLICT (domain) DO UPDATE SET domain=EXCLUDED.domain \
                RETURNING id AS domain_id) \
            , ins3 AS ( \
                INSERT INTO rotulus.passwords (password) VALUES ($3) \
                ON CONFLICT (password) DO UPDATE SET password=EXCLUDED.password \
                RETURNING id AS password_id) \
            INSERT INTO rotulus.records (username_id, domain_id, password_id) \
            VALUES ( \
                (select username_id from ins1), \
                (select domain_id from ins2), \
                (select password_id from ins3)
            )'''
    await connection.executemany(statement, records)


async def insert_records_with_hash(connection, records, hash_type):
    statement = '''WITH ins1 AS ( \
                INSERT INTO rotulus.usernames (username) VALUES ($1) \
                ON CONFLICT (username) DO UPDATE SET username=EXCLUDED.username \
                RETURNING id AS username_id) \
            , ins2 AS ( \
                INSERT INTO rotulus.domains (domain) VALUES ($2) \
                ON CONFLICT (domain) DO UPDATE SET domain=EXCLUDED.domain \
                RETURNING id AS domain_id) \
            , ins3 AS ( \
                INSERT INTO rotulus.hashes_types (hash_type) VALUES ($4) \
                ON CONFLICT (hash_type) DO UPDATE SET hash_type=EXCLUDED.hash_type \
                RETURNING id AS hash_type_id) \
            , ins4 AS ( \
                INSERT INTO rotulus.{}_hashes (hash) VALUES ($3) \
                ON CONFLICT (hash) DO UPDATE SET hash=EXCLUDED.hash \
                RETURNING id AS hash_id) \
            INSERT INTO rotulus.records (username_id, domain_id, {}_id) \
            VALUES ( \
                (select username_id from ins1), \
                (select domain_id from ins2), \
                (select hash_id from ins4)
            )'''.format(hash_type, hash_type)
    await connection.executemany(statement, records)


async def add_records_with_hashes(connection, records):
    ret = True
    con = db_connect()
    hash_type = records[0][3]
    if con:
        if not hash_type_known(con, hash_type):
            if create_hash_table(con, hash_type):
                ret = alter_records_table(con, hash_type)
        close_communication(con)
    if ret:
        await insert_records_with_hash(connection, records, hash_type)


async def insert_in_db(args):
    connection = await async_db_connect()
    l_errors = []
    records = []
    nb_records = 0
    before = await select_record_count(connection)
    for file in args.file:
        for line in file:
            nb_records += 1
            try:
                if line.endswith(b'\n'):
                    line = line[:-1]
            except:
                l_errors.append(line)
                continue
            if args.spliter in line:
                try:
                    data = line.split(args.spliter, 1)
                except:
                    l_errors.append(line)
                    continue
                if len(data) == 2:
                    if b'@' in data[0]:
                        record = Record()
                        record.set_username(data[0].split(b'@')[0])
                        record.set_domain(data[0].split(b'@')[1])
                        if args.hash or args.cipher:
                            record.set_password_hash(data[1])
                            if args.cipher:
                                record.set_hash_type(args.cipher.lower())
                            else:
                                record.set_hash_type(
                                    get_hash_type(record.hash))
                            records.append(
                                (record.username, record.domain, record.hash, record.hash_type))
                        else:
                            record.set_password(data[1])
                            records.append(
                                (record.username, record.domain, record.password))
                    else:
                        l_errors.append(line)
                else:
                    l_errors.append(line)
            else:
                l_errors.append(line)
    try:
        print('[*] Inserting {} records'.format(len(records)))
        if args.hash or args.cipher:
            await add_records_with_hashes(connection, records)
        else:
            await insert_records_with_passwords(connection, records)
    except Exception as e:
        print('[!] Error while inserting data to PostgreSQL:\n\t{}'.format(e))

    after = await select_record_count(connection)

    if l_errors:
        write_errors(l_errors)

    print('[-] SUCCESS={} ERROR={}'.format(after-before, len(l_errors)))


def main():
    signal.signal(signal.SIGINT, signal_handler)
    asyncio.get_event_loop().run_until_complete(insert_in_db(parse_cli()))


if __name__ == '__main__':
    main()
