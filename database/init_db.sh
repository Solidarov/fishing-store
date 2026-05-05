#!/bin/bash
set -e

echo "Running native database initialization script..."

# 1. Create the App User if it's different from the root POSTGRES_USER
if [ "$DB_USER" != "$POSTGRES_USER" ]; then
    echo "Creating additional user: $DB_USER"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
        DO \$\$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = '$DB_USER') THEN
                CREATE USER "$DB_USER" WITH PASSWORD '$DB_PASSWORD';
                ALTER USER "$DB_USER" WITH SUPERUSER;
            END IF;
        END
        \$\$;
EOSQL
fi

# 2. Create the App Database if it's different from the root POSTGRES_DB
if [ "$DB_NAME" != "$POSTGRES_DB" ]; then
    echo "Creating additional database: $DB_NAME"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
        SELECT 'CREATE DATABASE "$DB_NAME"'
        WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec
        ALTER DATABASE "$DB_NAME" OWNER TO "$DB_USER";
EOSQL
fi

# 3. Grant Permissions
echo "Granting permissions for $DB_USER on $DB_NAME..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DB_NAME" <<-EOSQL
    GRANT ALL PRIVILEGES ON DATABASE "$DB_NAME" TO "$DB_USER";
    GRANT ALL ON SCHEMA public TO "$DB_USER";
EOSQL

echo "Native database initialization complete!"
