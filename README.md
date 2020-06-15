# Rotulus

 The aim of this project is to provide a database schema and a seeder to stock database leak the most efficient way.

- If the database leak contains hashed password it will try finding the corresponding clear text password in the database.

- It creates an error file containing all the records which it haven't been able to parse.

## 1. Databse setup

Depending on the data drive, add one of the `conf` files from the `conf` directory to
Postgres' `conf.d` dir.

It's recommended to modify the configuration to feet your hardware.

```bash
sudo cp conf/16gb_4cpu_ssd.conf /etc/postgresql/12/main/conf.d/dump.conf
sudo systemctl restart postgresql@12-main.service
```

## 2. Create PostgreSQL user and database

```bash
sudo -u postgres psql
```

```psql
create database rotulus;
create user rotulususer with encrypted password 'rotuluspassword';
grant all privileges on database rotulus to rotulususer;
```

## 3. Modify database configuration file

The database configuration file is `conf/database.yml`.

Modify it to fit your database configuration.

## 4. Create tables

```bash
python3 database.py -d create
```

## Usage
### Seeding

#### Input file format
Dump entries should be in the format:

```
email@domain.com<separator>[password|hash]
```

For example:

- With clear text password
```
00zzzz00@mail.ru:alenuska1
```

- With hashed password
```
00zz@mail.ru:503c84b04c107ed207e9b5e07d3fac46
```

#### CLI

- Insert data from one file with `:` separator
```bash
python3 seeder.py -f dbleak.txt -s :
```

- Insert data from all file in a directory with `;` separator
```bash
python3 seeder.py -f dbleaks/* -s ;
```

- Insert data from one file with `:` separator and hashed password without knowing the type of hash
```bash
python3 seeder.py -f dbleak_with_hashed_passwords.txt -s : -a
```
Using a modified version of [hashID](https://github.com/psypanda/hashID) it'll identify for you the type of hash used. **Without a 100% accuracy**.

- Insert data from one file with `:` separator and hashed password without knowing the type of hash
```bash
python3 seeder.py -f dbleak_with_hashed_passwords.txt -s : -c md5
```

### Databse

`database.py` reade the database configuration in `conf/database.yml`.

#### Create

```bash
python3 database.py -d create
```

#### Drop

```bash
python3 database.py -d drop
```

#### Reset

```bash
python3 database.py -d rest
```

It like making a drop and a create (`python3 database.py -d drop && python3 database.py -d create)`.

## Coming soon

- [] Database migration
- [] Database query

## Support us !
```
BTC: 3KRs9A7CqJChHQfNEeKU2hGCaDYWCzcT7S
XMR: 8BQBQ6hDNKcXzTggFMugLqeoENdA9GgYfXMdp1Lxxtw5ECmzkUTsPYhVMS6oxzYBHU4AdgotDnuTp2RTj98ozdkfKVGBLxa
```