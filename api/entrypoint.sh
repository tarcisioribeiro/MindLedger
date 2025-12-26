#!/bin/bash

set -e

# As variáveis de ambiente são fornecidas pelo docker-compose
# Não carregamos .env local para evitar conflitos

echo "Aguardando banco de dados em $DB_HOST:$DB_PORT..."

until nc -z -v -w30 "$DB_HOST" "$DB_PORT"; do
  echo "Aguardando banco de dados..."
  sleep 1
done

echo "Banco de dados está disponível!"

export PGPASSWORD="$DB_PASSWORD"

psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres <<EOF
DO \$\$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_database WHERE datname = '$DB_NAME'
   ) THEN
      CREATE DATABASE $DB_NAME
      WITH OWNER = $DB_USER
      ENCODING = 'UTF8'
      LC_COLLATE = 'pt_BR.UTF-8'
      LC_CTYPE = 'pt_BR.UTF-8'
      TABLESPACE = pg_default
      CONNECTION LIMIT = -1
      IS_TEMPLATE = false;
   END IF;
END
\$\$;
EOF

python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python createsuperuser.py

# Configurar grupo 'members' e suas permissões
echo "🔧 Configurando grupos e permissões do sistema..."
python setup_members.py

echo "🚀 Iniciando servidor Django..."
python manage.py runserver 0.0.0.0:${API_PORT:-39100}
