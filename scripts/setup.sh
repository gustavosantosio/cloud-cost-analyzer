#!/bin/bash

# Cloud Cost Agent - Setup Script
# Este script configura o ambiente de desenvolvimento

set -e

echo "🚀 Configurando Cloud Cost Agent..."

# Verificar Python
if ! command -v python3.11 &> /dev/null; then
    echo "❌ Python 3.11 não encontrado. Por favor, instale Python 3.11+"
    exit 1
fi

# Verificar Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js não encontrado. Por favor, instale Node.js 20+"
    exit 1
fi

# Verificar pnpm
if ! command -v pnpm &> /dev/null; then
    echo "📦 Instalando pnpm..."
    npm install -g pnpm
fi

# Criar ambiente virtual Python
echo "🐍 Criando ambiente virtual Python..."
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependências Python
echo "📦 Instalando dependências Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Instalar dependências Node.js
echo "⚛️ Instalando dependências React..."
cd web_interface/cloud-cost-analyzer
pnpm install
cd ../..

# Configurar pre-commit hooks
echo "🔧 Configurando pre-commit hooks..."
pip install pre-commit
pre-commit install

# Executar testes
echo "🧪 Executando testes..."
python integration_test.py

echo "✅ Configuração concluída!"
echo ""
echo "📋 Próximos passos:"
echo "1. Ativar ambiente virtual: source venv/bin/activate"
echo "2. Executar backend: python crewai_agents/crew_api.py"
echo "3. Executar frontend: cd web_interface/cloud-cost-analyzer && pnpm dev"
echo ""
echo "🌐 Demo online: https://y0h0i3cqn6yq.manus.space"

