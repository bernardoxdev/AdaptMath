#!/bin/bash

echo "================================"
echo "SETUP DATABASE"
echo "================================"

python -m backend.database.setup_database

STATUS=$?

if [ $STATUS -ne 0 ]; then
    echo ""
    echo "================================"
    echo "ERRO NO SETUP"
    echo "================================"
    echo "O container será encerrado."
    exit 1
fi

echo ""
echo "================================"
echo "SETUP FINALIZADO COM SUCESSO"
echo "================================"

echo ""
echo "================================"
echo "INICIANDO GUNICORN"
echo "================================"

exec gunicorn \
    -b 0.0.0.0:5000 \
    backend.main:app