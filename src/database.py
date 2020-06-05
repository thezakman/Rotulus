import sys
import yaml
import psycopg2


TABLES = [
    {"name": "usernames",
     "columns": [
         {"name": "id",
          "properties": "bigserial primary key"
          },
         {"name": "username",
          "properties": "char(64) not null unique"
          }
     ],
     },
    {"name": "domains",
     "columns": [
         {"name": "id",
          "properties": "bigserial primary key"
          },
         {"name": "domain",
             "properties": "char(255) not null unique"
          }
     ],
     },
    {"name": "passwords",
     "columns": [
         {"name": "id",
          "properties": "bigserial primary key"
          },
         {"name": "password",
             "properties": "text not null unique"
          }
     ],
     },
    {"name": "hashes_types",
     "columns": [
         {"name": "id",
          "properties": "serial primary key"
          },
         {"name": "hash_type",
             "properties": "char(50) not null unique"
          }
     ],
     },
    {"name": "hashes",
     "columns": [
         {"name": "id",
          "properties": "bigserial primary key"
          },
         {"name": "hash",
             "properties": "text not null unique"
          },
         {"name": "hash_type_id",
          "properties": "int references hashes_types(id)"
          }
     ],
     },
    {"name": "records",
     "columns": [
         {"name": "id",
          "properties": "bigserial primary key"
          },
         {"name": "username_id",
             "properties": "bigint not null references usernames(id)"
          },
         {"name": "domain_id",
          "properties": "bigint references domains(id)"
          },
         {"name": "password_id",
          "properties": "bigint references passwords(id)"
          },
         {"name": "hash_id",
          "properties": "bigint references hashes(id)"
          }
     ]
     }
]


def get_db_conf():
    conf_path = "../conf"
    db_conf = "database.yml"
    dbconf = "{}/{}".format(conf_path, db_conf)

    try:
        with open(dbconf, "r") as stream:
            return yaml.safe_load(stream)
    except:
        sys.exit("[!] Unable to read database configuration in {}".format(db_conf))


def db_connect(db_conf):
    print("[*] Connecting to PostgreSQL database")
    try:
        connection = psycopg2.connect(user=db_conf["psql"]["username"],
                                      password=db_conf["psql"]["password"],
                                      host=db_conf["psql"]["host"],
                                      port=db_conf["psql"]["port"],
                                      database=db_conf["psql"]["dbname"])
        return connection
    except (Exception, psycopg2.Error) as error:
        sys.exit("[!] Error while connecting to PostgreSQL", error)


def execute_query(cursor, query):
    try:
        cursor.execute(query)
    except:
        sys.exit("[!] Unable to execute '{}'".format(query))


def create_tables(connection):
    print("[*] Creating tables")
    for table in TABLES:
        query = "create table {}( ".format(table["name"])
        nb_colums = len(table["columns"])
        i = 0
        for column in table["columns"]:
            query += "{} {}".format(column["name"], column["properties"])
            i += 1
            if i != nb_colums:
                query += ", "
        query += ");"

        try:
            connection.cursor().execute(query)
            connection.commit()
        except:
            sys.exit("[!] Unable to create tables")
    print("[-] All tables successfully created")

def setup_database():
    db_conf = get_db_conf()
    connection = db_connect(db_conf)
    create_tables(connection)
    return True

if __name__ == "__main__":
    setup_database()
