# Rotulus

## Create PostgreSQL user and database

```bash
sudo -u postgres psql
```

```psql
create database rotulus;
reate user rotulususer with encrypted password 'rotuluspassword';
grant all privileges on database rotulus to rotulususer;
```


