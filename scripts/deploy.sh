#!/bin/bash

# Cloud Cost Agent - Deploy Script
# Este script prepara e faz deploy da aplicação

set -e

echo "🚀 Iniciando deploy do Cloud Cost Agent..."

# Verificar se está no diretório correto
if [ ! -f "requirements.txt" ]; then
    echo "❌ Execute este script a partir do diretório raiz do projeto"
    exit 1
fi

# Ativar ambiente virtual se existir
if [ -d "venv" ]; then
    echo "🐍 Ativando ambiente virtual..."
    source venv/bin/activate
fi

# Build do frontend
echo "⚛️ Fazendo build do frontend..."
cd web_interface/cloud-cost-analyzer
pnpm install
pnpm run build
cd ../..

# Copiar build para aplicação de deploy
echo "📦 Preparando aplicação de deploy..."
rm -rf cloud-cost-agent-deploy/src/static/*
cp -r web_interface/cloud-cost-analyzer/dist/* cloud-cost-agent-deploy/src/static/

# Testar aplicação localmente
echo "🧪 Testando aplicação..."
cd cloud-cost-agent-deploy/src
python main.py &
SERVER_PID=$!
sleep 5

# Verificar se servidor está respondendo
if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "✅ Servidor local funcionando"
    kill $SERVER_PID
else
    echo "❌ Erro no servidor local"
    kill $SERVER_PID
    exit 1
fi

cd ../..

echo "✅ Deploy preparado com sucesso!"
echo ""
echo "📋 Para fazer deploy:"
echo "1. Commit e push para GitHub"
echo "2. Configure seu provedor de deploy (Vercel, Netlify, etc.)"
echo "3. Ou use: manus service_deploy_backend flask cloud-cost-agent-deploy/"
echo ""
echo "🌐 Demo atual: https://y0h0i3cqn6yq.manus.space"

