# Guia de Contribuição

Obrigado por considerar contribuir para o Cloud Cost Agent! Este documento fornece diretrizes para contribuições.

## 🚀 Como Contribuir

### 1. Fork e Clone
```bash
# Fork o repositório no GitHub
# Clone seu fork
git clone https://github.com/SEU_USUARIO/cloud-cost-agent.git
cd cloud-cost-agent
```

### 2. Configurar Ambiente
```bash
# Instalar dependências Python
pip install -r requirements.txt

# Instalar dependências Node.js
cd web_interface/cloud-cost-analyzer
pnpm install
```

### 3. Criar Branch
```bash
git checkout -b feature/nova-funcionalidade
# ou
git checkout -b fix/correcao-bug
```

### 4. Fazer Mudanças
- Siga os padrões de código existentes
- Adicione testes para novas funcionalidades
- Atualize documentação se necessário

### 5. Testar
```bash
# Executar testes
python integration_test.py

# Testar frontend
cd web_interface/cloud-cost-analyzer
pnpm test
```

### 6. Commit e Push
```bash
git add .
git commit -m "feat: adiciona nova funcionalidade X"
git push origin feature/nova-funcionalidade
```

### 7. Pull Request
- Abra um Pull Request no GitHub
- Descreva as mudanças claramente
- Referencie issues relacionadas

## 📋 Padrões de Código

### Python
- Use PEP 8
- Docstrings para funções públicas
- Type hints quando possível

### JavaScript/React
- Use ESLint e Prettier
- Componentes funcionais com hooks
- Props tipadas com PropTypes

### Commits
Use Conventional Commits:
- `feat:` nova funcionalidade
- `fix:` correção de bug
- `docs:` documentação
- `style:` formatação
- `refactor:` refatoração
- `test:` testes

## 🐛 Reportar Bugs

Use o template de issue para bugs:
1. Descrição clara do problema
2. Passos para reproduzir
3. Comportamento esperado vs atual
4. Ambiente (OS, Python, Node.js)
5. Logs relevantes

## 💡 Sugerir Funcionalidades

Para novas funcionalidades:
1. Verifique se já não existe issue similar
2. Descreva o problema que resolve
3. Proponha uma solução
4. Considere alternativas

## 📝 Documentação

- README.md para visão geral
- Docstrings para código Python
- Comentários JSDoc para JavaScript
- Exemplos de uso quando relevante

## 🧪 Testes

- Testes unitários para lógica de negócio
- Testes de integração para APIs
- Testes E2E para fluxos críticos
- Cobertura mínima de 80%

## 📦 Estrutura do Projeto

```
cloud-cost-agent/
├── mcp_servers/           # Servidores MCP
├── crewai_agents/         # Sistema CrewAI
├── web_interface/         # Frontend React
├── cloud-cost-agent-deploy/ # Deploy
├── tests/                 # Testes
├── docs/                  # Documentação
└── scripts/               # Scripts utilitários
```

## 🔄 Processo de Review

1. **Automated Checks**: CI/CD executa testes
2. **Code Review**: Maintainer revisa código
3. **Testing**: Testa funcionalidade manualmente
4. **Merge**: Aprovação e merge

## 📞 Contato

- Issues: Para bugs e funcionalidades
- Discussions: Para perguntas gerais
- Email: Para questões sensíveis

## 🙏 Reconhecimento

Contribuidores são listados no README.md e recebem crédito apropriado.

---

**Obrigado por contribuir! 🎉**

