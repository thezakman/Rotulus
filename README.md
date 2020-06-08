# Rotulus

1. Create PostgreSQL user and database

```bash
sudo -u postgres psql
```

```psql
create database rotulus;
create user rotulususer with encrypted password 'rotuluspassword';
grant all privileges on database rotulus to rotulususer;
```


