import argparse
import asyncio
import hashlib
import os
import time

import asyncpg
from hashid import get_hash_type

from database import get_db_conf
from query import select_record_count
from record import Record


def parse_cli():
    parser = argparse.ArgumentParser(
        description='Insert data in Rotulus database')
    parser.add_argument('-f', '--file',
                        required=True,
                        help='One or more files containing email address, password, ...',
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


async def db_connect():
    print('[*] Connecting to PostgreSQL database')
    db_conf = get_db_conf()
    if db_conf != False:
        try:
            con = await asyncpg.connect(user=db_conf['psql']['username'],
                                        password=db_conf['psql']['password'],
                                        host=db_conf['psql']['host'],
                                        port=db_conf['psql']['port'],
                                        database=db_conf['psql']['dbname'])
            return con
        except:
            print('[!] Error while connecting to PostgreSQL')
            return False
    else:
        return False


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
            , ins4 AS ( \
                INSERT INTO rotulus.hashes_types (hash_type) VALUES ($5) \
                ON CONFLICT (hash_type) DO UPDATE SET hash_type=EXCLUDED.hash_type \
                RETURNING id AS hash_type_id) \
            , ins5 AS ( \
                INSERT INTO rotulus.hashes (hash, hash_type_id) \
                VALUES ($4, (select hash_type_id from ins4) ) \
                ON CONFLICT (hash) DO UPDATE SET hash=EXCLUDED.hash \
                RETURNING id AS hash_id) \
            INSERT INTO rotulus.records (username_id, domain_id, password_id, hash_id) \
            VALUES ( \
                (select username_id from ins1), \
                (select domain_id from ins2), \
                (select password_id from ins3), \
                (select hash_id from ins5) \
            )'''
    await connection.executemany(statement, records)


async def insert_records_without_passwords(connection, records):
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
                INSERT INTO rotulus.hashes (hash, hash_type_id) \
                VALUES ($3, (select hash_type_id from ins3) ) \
                ON CONFLICT (hash) DO UPDATE SET hash=EXCLUDED.hash \
                RETURNING id AS hash_id) \
            INSERT INTO rotulus.records (username_id, domain_id, hash_id, password_id) \
            VALUES ( \
                (select username_id from ins1), \
                (select domain_id from ins2), \
                (select hash_id from ins4), \
                (select distinct password_id from rotulus.records where hash_id = (select hash_id from ins4) and password_id IS NOT NULL)
            )'''
    await connection.executemany(statement, records)


async def main(args):
    connection = await db_connect()
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
                    data = line.split(args.spliter)
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
                            record.set_password_hash(
                                hashlib.md5(data[1]).hexdigest())
                            record.set_hash_type('md5')
                            records.append(
                                (record.username, record.domain, record.password, record.hash, record.hash_type))
                    else:
                        l_errors.append(line)
                else:
                    l_errors.append(line)
            else:
                l_errors.append(line)
    try:
        print('[*] Inserting {} records'.format(len(records)))
        if args.hash:
            await insert_records_without_passwords(connection, records)
        else:
            await insert_records_with_passwords(connection, records)
    except Exception as e:
        print('[!] Error while inserting data to PostgreSQL:\n\t{}'.format(e))

    after = await select_record_count(connection)

    if l_errors:
        write_errors(l_errors)

    print('[-] SUCCESS={} ERROR={}'.format(after-before, len(l_errors)))

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main(parse_cli()))
