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

# Criar diretórios necessários para upload de arquivos
echo "Criando diretórios necessários..."
CURRENT_YEAR=$(date +%Y)
CURRENT_MONTH=$(date +%m)

# Create media directories with year/month structure for current date
mkdir -p /app/media/security/archives/${CURRENT_YEAR}/${CURRENT_MONTH} 2>/dev/null || true
mkdir -p /app/media/loans 2>/dev/null || true
mkdir -p /app/logs 2>/dev/null || true
mkdir -p /app/staticfiles 2>/dev/null || true

# Verify write permissions to media directory
if [ ! -w "/app/media/security/archives" ]; then
    echo "⚠️  AVISO: Diretório /app/media/security/archives sem permissão de escrita!"
    echo "   Execute no host: sudo chown -R \$(id -u):\$(id -g) ./api/media"
fi

export PGPASSWORD="$DB_PASSWORD"

# Create database if not exists
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres <<EOF
DO \$\$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_database WHERE datname = '$DB_NAME'
   ) THEN
      CREATE DATABASE $DB_NAME
      WITH OWNER = $DB_USER
      ENCODING = 'UTF8'
      LC_COLLATE = 'C.UTF-8'
      LC_CTYPE = 'C.UTF-8'
      TABLESPACE = pg_default
      CONNECTION LIMIT = -1
      IS_TEMPLATE = false;
   END IF;
END
\$\$;
EOF

# Create pgvector extension in the application database (required for embeddings)
echo "Habilitando extensão pgvector..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS vector;"

python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python createsuperuser.py

# Configurar grupo 'members' e suas permissões
echo "🔧 Configurando grupos e permissões do sistema..."
python setup_members.py

echo "🚀 Iniciando servidor Django..."
python manage.py runserver 0.0.0.0:${API_PORT:-39100}
