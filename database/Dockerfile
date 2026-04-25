FROM postgres:15

# Scripts in this directory are executed on container startup IF the data volume is empty
COPY init_db.sh /docker-entrypoint-initdb.d/init_db.sh

RUN chmod +x /docker-entrypoint-initdb.d/init_db.sh
