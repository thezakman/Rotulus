import argparse
import asyncio
import os
import signal
import sys
from pathlib import Path

import asyncpg
import psycopg2
import yaml

TABLES = [
    {"name": "usernames",
     "columns": [
         {"name": "id",
          "properties": "bigserial primary key"
          },
         {"name": "username",
          "properties": "bytea not null unique"
          }
     ],
     },
    {"name": "domains",
     "columns": [
         {"name": "id",
          "properties": "bigserial primary key"
          },
         {"name": "domain",
             "properties": "bytea not null unique"
          }
     ],
     },
    {"name": "passwords",
     "columns": [
         {"name": "id",
          "properties": "bigserial primary key"
          },
         {"name": "password",
             "properties": "bytea not null unique"
          }
     ],
     },
    {"name": "hashes_types",
     "columns": [
         {"name": "id",
          "properties": "serial primary key"
          },
         {"name": "hash_type",
             "properties": "text not null unique"
          }
     ],
     },
    {"name": "records",
     "columns": [
         {"name": "id",
          "properties": "bigserial primary key"
          },
         {"name": "username_id",
             "properties": "bigint not null references rotulus.usernames(id)"
          },
         {"name": "domain_id",
          "properties": "bigint references rotulus.domains(id)"
          },
         {"name": "password_id",
          "properties": "bigint references rotulus.passwords(id)"
          }
     ]
     }
]

HASH_TEMPLATE = {"name": "hashes",
                 "columns": [
                     {"name": "id",
                      "properties": "bigserial primary key"
                      },
                     {"name": "hash",
                      "properties": "text not null unique"
                      }
                 ]}


def signal_handler(signal, frame):
    sys.exit(0)


def request_conf():
    dbname = input("Database name (default: rotulus) : ") or "rotulus"
    user = input(
        "User name used to authenticate (default: rotulususer) : ") or "rotulususer"
    password = input(
        "Password used to authenticate (default: rotuluspassword) : ") or "rotuluspassword"
    host = input(
        "Database host address (default: localhost) : ") or "localhost"
    port = input("Connection port number (default: 5432) : ") or "5432"
    request_write_conf(dbname, user, password, host, port)


def request_write_conf(dbname, user, password, host, port):
    answer = input(
        "Write database configuration in $HOME/.rotulus.yml ? (default: yes) : ")
    if not answer or "y" in answer:
        write_conf(dbname, user, password, host, port,
                   str(Path.home()) + "/.rotulus.yml")
    else:
        print("Write lines below where you want :\n{}".format(
            get_conf_str(dbname, user, password, host, port)))
        answer = input("Can I write it down ? (default: yes) : ")
        if not answer or "y" in answer:
            path = input("Path : ")
            write_conf(dbname, user, password, host, port, path)
        print("Create an environment varibale named ROTULUS_CONF_PATH to store the database conf path like below :")
        print("export ROTULUS_CONF_PATH=/path/to/file")


def get_conf_str(dbname, user, password, host, port):
    database_conf = "psql:\n  host: {}\n  port: {}\n  dbname: {}\n  username: {}\n  password: {}"
    return database_conf.format(host, port, dbname, user, password)


def write_conf(dbname, user, password, host, port, path):
    try:
        with open(path, "w") as rotulus_conf_file:
            rotulus_conf_file.write(get_conf_str(
                dbname, user, password, host, port))
        print("[+] Database configuration writed in {}".format(path))
    except:
        print("[!] Unable to write database configuration in {}".format(path))
        return False


def get_db_conf():
    if os.environ.get('ROTULUS_CONF_PATH'):
        dbconf = os.environ.get('ROTULUS_CONF_PATH')
    else:
        home_path = str(Path.home())
        db_conf = ".rotulus.yml"
        dbconf = "{}/{}".format(home_path, db_conf)

    try:
        with open(dbconf, "r") as stream:
            return yaml.safe_load(stream)
    except:
        print("[!] Unable to read database configuration in {}".format(db_conf))
        return False


def db_connect():
    db_conf = get_db_conf()
    if db_conf != False:
        try:
            connection = psycopg2.connect(user=db_conf["psql"]["username"],
                                          password=db_conf["psql"]["password"],
                                          host=db_conf["psql"]["host"],
                                          port=db_conf["psql"]["port"],
                                          database=db_conf["psql"]["dbname"])
            return connection
        except (Exception, psycopg2.Error) as error:
            print("[!] Error while connecting to PostgreSQL", error)
            return False
    else:
        return False


async def async_db_connect():
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


def execute_query(connection, query):
    try:
        connection.cursor().execute(query)
        connection.commit()
        return True
    except (Exception, psycopg2.Error) as error:
        print("[!] Unable to execute '{}'".format(query))
        print(error)
        return False


def close_communication(connection):
    connection.cursor().close()
    connection.close()


def create_schema(connection):
    print("[*] Creating schema rotulus")
    query = "create schema rotulus;"
    return execute_query(connection, query)


def drop_schema(connection):
    print("[*] Dropping schema rotulus in cascade")
    query = "drop schema rotulus cascade;"
    return execute_query(connection, query)


def create_tables(connection, tables):
    for table in tables:
        print("[*] Creating table rotulus.{}".format(table["name"]))
        query = "create unlogged table rotulus.{}(".format(table["name"])
        nb_colums = len(table["columns"])
        i = 0
        for column in table["columns"]:
            query += "{} {}".format(column["name"], column["properties"])
            i += 1
            if i != nb_colums:
                query += ", "
        query += ");"
        if execute_query(connection, query) == False:
            return False
    return True


def create_hash_table(connection, hash_type):
    hash_table = HASH_TEMPLATE
    hash_table["name"] = "{}_{}".format(
        hash_type, HASH_TEMPLATE["name"])
    return create_tables(connection, [hash_table])


def alter_records_table(connection, hash_type):
    query = 'alter table rotulus.records add column {}_id bigint references rotulus.{}_hashes(id)'.format(
        hash_type, hash_type)
    return execute_query(connection, query)


def drop_tables(connection, tables):
    print("[*] Dropping tables")
    for table in tables:
        query = "drop table rotulus.{} cascade;".format(table["name"])
        if execute_query(connection, query) == False:
            return False
    return True


def setup_database():
    connection = db_connect()
    if connection != False:
        if create_schema(connection):
            if create_tables(connection, TABLES) == True:
                close_communication(connection)
                return True
            else:
                connection.rollback()
        close_communication(connection)
    return False


def remove_tables():
    connection = db_connect()
    if connection != False:
        if drop_schema(connection) == True:
            connection.commit()
            close_communication(connection)
            return True
        else:
            connection.rollback()
        close_communication(connection)
    return False


def parse_cli():
    parser = argparse.ArgumentParser(description='Manage Rotulus database')
    parser.add_argument('-d', '--database', choices=[
                        'init', 'create', 'drop', 'reset'], required=True, help='Action against database tables')

    args = parser.parse_args()

    if args.database == "init":
        request_conf()
    elif args.database == "create":
        setup_database()
    elif args.database == "drop":
        remove_tables()
    elif args.database == "reset":
        remove_tables()
        setup_database()


def main():
    signal.signal(signal.SIGINT, signal_handler)
    parse_cli()


if __name__ == "__main__":
    main()
