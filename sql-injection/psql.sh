set -e
set -x

docker exec -ti sqlinjection_postgres_1 psql --username=postgres
