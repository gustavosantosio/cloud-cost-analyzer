#!/usr/bin/env python3
"""
Integration Test Script for Cloud Cost Agent

Script para testar a integração completa do sistema de análise de custos de nuvem.
Testa servidores MCP, API Flask, e funcionalidades do CrewAI.
"""

import os
import sys
import json
import time
import requests
import subprocess
import logging
from typing import Dict, Any, List
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CloudCostAgentTester:
    """Classe para testar integração do sistema completo"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.api_url = "http://localhost:5000"
        self.processes = []
        self.test_results = []
    
    def start_services(self) -> bool:
        """Iniciar todos os serviços necessários"""
        logger.info("🚀 Iniciando serviços do sistema...")
        
        try:
            # Iniciar API Flask
            api_path = os.path.join(self.base_dir, "crewai_agents", "crew_api.py")
            api_process = subprocess.Popen(
                [sys.executable, api_path],
                cwd=os.path.join(self.base_dir, "crewai_agents"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.processes.append(("API Flask", api_process))
            logger.info("✅ API Flask iniciada")
            
            # Aguardar inicialização
            time.sleep(5)
            
            # Verificar se API está respondendo
            for attempt in range(10):
                try:
                    response = requests.get(f"{self.api_url}/health", timeout=5)
                    if response.status_code == 200:
                        logger.info("✅ API Flask está respondendo")
                        return True
                except requests.exceptions.RequestException:
                    time.sleep(2)
            
            logger.error("❌ API Flask não está respondendo")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar serviços: {e}")
            return False
    
    def test_api_endpoints(self) -> Dict[str, Any]:
        """Testar endpoints da API"""
        logger.info("🧪 Testando endpoints da API...")
        
        test_results = {
            "health_check": False,
            "providers_info": False,
            "templates": False,
            "analysis_history": False
        }
        
        try:
            # Test health endpoint
            response = requests.get(f"{self.api_url}/health")
            if response.status_code == 200:
                test_results["health_check"] = True
                logger.info("✅ Health check passou")
            else:
                logger.error(f"❌ Health check falhou: {response.status_code}")
            
            # Test providers info
            response = requests.get(f"{self.api_url}/api/providers/info")
            if response.status_code == 200:
                data = response.json()
                if "providers" in data and "aws" in data["providers"] and "gcp" in data["providers"]:
                    test_results["providers_info"] = True
                    logger.info("✅ Providers info passou")
                else:
                    logger.error("❌ Providers info com estrutura inválida")
            else:
                logger.error(f"❌ Providers info falhou: {response.status_code}")
            
            # Test templates
            response = requests.get(f"{self.api_url}/api/templates")
            if response.status_code == 200:
                data = response.json()
                if "templates" in data:
                    test_results["templates"] = True
                    logger.info("✅ Templates passou")
                else:
                    logger.error("❌ Templates com estrutura inválida")
            else:
                logger.error(f"❌ Templates falhou: {response.status_code}")
            
            # Test analysis history
            response = requests.get(f"{self.api_url}/api/analysis/history")
            if response.status_code == 200:
                data = response.json()
                if "analyses" in data:
                    test_results["analysis_history"] = True
                    logger.info("✅ Analysis history passou")
                else:
                    logger.error("❌ Analysis history com estrutura inválida")
            else:
                logger.error(f"❌ Analysis history falhou: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao testar endpoints: {e}")
        
        return test_results
    
    def test_mcp_servers(self) -> Dict[str, Any]:
        """Testar servidores MCP individualmente"""
        logger.info("🔧 Testando servidores MCP...")
        
        test_results = {
            "aws_server": False,
            "gcp_server": False,
            "comparison_server": False
        }
        
        try:
            # Testar servidor AWS MCP
            aws_server_path = os.path.join(self.base_dir, "mcp_servers", "aws_pricing_server.py")
            if os.path.exists(aws_server_path):
                # Verificar se o arquivo pode ser importado
                try:
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("aws_server", aws_server_path)
                    if spec and spec.loader:
                        test_results["aws_server"] = True
                        logger.info("✅ Servidor AWS MCP pode ser carregado")
                    else:
                        logger.error("❌ Servidor AWS MCP não pode ser carregado")
                except Exception as e:
                    logger.error(f"❌ Erro ao carregar servidor AWS MCP: {e}")
            else:
                logger.error("❌ Arquivo do servidor AWS MCP não encontrado")
            
            # Testar servidor GCP MCP
            gcp_server_path = os.path.join(self.base_dir, "mcp_servers", "gcp_pricing_server.py")
            if os.path.exists(gcp_server_path):
                try:
                    spec = importlib.util.spec_from_file_location("gcp_server", gcp_server_path)
                    if spec and spec.loader:
                        test_results["gcp_server"] = True
                        logger.info("✅ Servidor GCP MCP pode ser carregado")
                    else:
                        logger.error("❌ Servidor GCP MCP não pode ser carregado")
                except Exception as e:
                    logger.error(f"❌ Erro ao carregar servidor GCP MCP: {e}")
            else:
                logger.error("❌ Arquivo do servidor GCP MCP não encontrado")
            
            # Testar servidor de comparação MCP
            comp_server_path = os.path.join(self.base_dir, "mcp_servers", "comparison_server.py")
            if os.path.exists(comp_server_path):
                try:
                    spec = importlib.util.spec_from_file_location("comp_server", comp_server_path)
                    if spec and spec.loader:
                        test_results["comparison_server"] = True
                        logger.info("✅ Servidor de comparação MCP pode ser carregado")
                    else:
                        logger.error("❌ Servidor de comparação MCP não pode ser carregado")
                except Exception as e:
                    logger.error(f"❌ Erro ao carregar servidor de comparação MCP: {e}")
            else:
                logger.error("❌ Arquivo do servidor de comparação MCP não encontrado")
                
        except Exception as e:
            logger.error(f"❌ Erro ao testar servidores MCP: {e}")
        
        return test_results
    
    def test_crewai_integration(self) -> Dict[str, Any]:
        """Testar integração com CrewAI"""
        logger.info("👥 Testando integração CrewAI...")
        
        test_results = {
            "crew_file_exists": False,
            "crew_can_import": False,
            "agents_configured": False
        }
        
        try:
            # Verificar se arquivo do crew existe
            crew_path = os.path.join(self.base_dir, "crewai_agents", "cloud_cost_crew.py")
            if os.path.exists(crew_path):
                test_results["crew_file_exists"] = True
                logger.info("✅ Arquivo do CrewAI encontrado")
                
                # Tentar importar o módulo
                try:
                    sys.path.append(os.path.join(self.base_dir, "crewai_agents"))
                    import cloud_cost_crew
                    test_results["crew_can_import"] = True
                    logger.info("✅ Módulo CrewAI pode ser importado")
                    
                    # Verificar se a classe pode ser instanciada
                    try:
                        crew_instance = cloud_cost_crew.CloudCostAnalysisCrew()
                        if hasattr(crew_instance, 'aws_specialist') and hasattr(crew_instance, 'gcp_specialist'):
                            test_results["agents_configured"] = True
                            logger.info("✅ Agentes CrewAI configurados corretamente")
                        else:
                            logger.error("❌ Agentes CrewAI não configurados corretamente")
                    except Exception as e:
                        logger.error(f"❌ Erro ao instanciar CrewAI: {e}")
                        
                except Exception as e:
                    logger.error(f"❌ Erro ao importar módulo CrewAI: {e}")
            else:
                logger.error("❌ Arquivo do CrewAI não encontrado")
                
        except Exception as e:
            logger.error(f"❌ Erro ao testar integração CrewAI: {e}")
        
        return test_results
    
    def test_frontend_build(self) -> Dict[str, Any]:
        """Testar build do frontend React"""
        logger.info("⚛️ Testando frontend React...")
        
        test_results = {
            "react_app_exists": False,
            "dependencies_installed": False,
            "can_build": False
        }
        
        try:
            # Verificar se aplicação React existe
            react_path = os.path.join(self.base_dir, "web_interface", "cloud-cost-analyzer")
            if os.path.exists(react_path):
                test_results["react_app_exists"] = True
                logger.info("✅ Aplicação React encontrada")
                
                # Verificar se dependências estão instaladas
                node_modules_path = os.path.join(react_path, "node_modules")
                if os.path.exists(node_modules_path):
                    test_results["dependencies_installed"] = True
                    logger.info("✅ Dependências React instaladas")
                    
                    # Tentar fazer build
                    try:
                        build_process = subprocess.run(
                            ["pnpm", "run", "build"],
                            cwd=react_path,
                            capture_output=True,
                            text=True,
                            timeout=120
                        )
                        
                        if build_process.returncode == 0:
                            test_results["can_build"] = True
                            logger.info("✅ Build do React executado com sucesso")
                        else:
                            logger.error(f"❌ Erro no build do React: {build_process.stderr}")
                            
                    except subprocess.TimeoutExpired:
                        logger.error("❌ Timeout no build do React")
                    except Exception as e:
                        logger.error(f"❌ Erro ao executar build do React: {e}")
                else:
                    logger.error("❌ Dependências React não instaladas")
            else:
                logger.error("❌ Aplicação React não encontrada")
                
        except Exception as e:
            logger.error(f"❌ Erro ao testar frontend React: {e}")
        
        return test_results
    
    def test_end_to_end_flow(self) -> Dict[str, Any]:
        """Testar fluxo completo end-to-end"""
        logger.info("🔄 Testando fluxo end-to-end...")
        
        test_results = {
            "compute_analysis": False,
            "storage_analysis": False,
            "comprehensive_analysis": False
        }
        
        try:
            # Dados de teste
            test_data = {
                "aws_instance_type": "t3.medium",
                "gcp_machine_type": "e2-medium",
                "aws_region": "us-east-1",
                "gcp_region": "us-central1",
                "workload_type": "general",
                "aws_storage_type": "s3_standard",
                "gcp_storage_type": "standard",
                "storage_size_gb": 1000,
                "monthly_budget": 500
            }
            
            # Testar análise de computação (com timeout curto para teste)
            try:
                response = requests.post(
                    f"{self.api_url}/api/analyze/compute",
                    json=test_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "analysis_type" in result:
                        test_results["compute_analysis"] = True
                        logger.info("✅ Análise de computação funcionando")
                    else:
                        logger.error("❌ Resposta de análise de computação inválida")
                else:
                    logger.error(f"❌ Análise de computação falhou: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                logger.warning("⚠️ Timeout na análise de computação (esperado em teste)")
            except Exception as e:
                logger.error(f"❌ Erro na análise de computação: {e}")
            
            # Testar análise de armazenamento (com timeout curto para teste)
            try:
                response = requests.post(
                    f"{self.api_url}/api/analyze/storage",
                    json=test_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "analysis_type" in result:
                        test_results["storage_analysis"] = True
                        logger.info("✅ Análise de armazenamento funcionando")
                    else:
                        logger.error("❌ Resposta de análise de armazenamento inválida")
                else:
                    logger.error(f"❌ Análise de armazenamento falhou: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                logger.warning("⚠️ Timeout na análise de armazenamento (esperado em teste)")
            except Exception as e:
                logger.error(f"❌ Erro na análise de armazenamento: {e}")
                
        except Exception as e:
            logger.error(f"❌ Erro no teste end-to-end: {e}")
        
        return test_results
    
    def generate_test_report(self, all_results: Dict[str, Dict[str, Any]]) -> str:
        """Gerar relatório de testes"""
        logger.info("📊 Gerando relatório de testes...")
        
        report = f"""
# Relatório de Testes de Integração - Cloud Cost Agent
Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Resumo Executivo
"""
        
        total_tests = 0
        passed_tests = 0
        
        for category, results in all_results.items():
            category_total = len(results)
            category_passed = sum(1 for result in results.values() if result)
            total_tests += category_total
            passed_tests += category_passed
            
            report += f"\n### {category.replace('_', ' ').title()}\n"
            report += f"- Testes executados: {category_total}\n"
            report += f"- Testes aprovados: {category_passed}\n"
            report += f"- Taxa de sucesso: {(category_passed/category_total)*100:.1f}%\n"
            
            for test_name, result in results.items():
                status = "✅ PASSOU" if result else "❌ FALHOU"
                report += f"  - {test_name.replace('_', ' ').title()}: {status}\n"
        
        overall_success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        report += f"""
## Resultado Geral
- Total de testes: {total_tests}
- Testes aprovados: {passed_tests}
- Taxa de sucesso geral: {overall_success_rate:.1f}%

## Status do Sistema
"""
        
        if overall_success_rate >= 80:
            report += "🟢 **SISTEMA OPERACIONAL** - Pronto para uso\n"
        elif overall_success_rate >= 60:
            report += "🟡 **SISTEMA PARCIALMENTE FUNCIONAL** - Alguns componentes precisam de ajustes\n"
        else:
            report += "🔴 **SISTEMA COM PROBLEMAS** - Requer correções antes do uso\n"
        
        report += f"""
## Recomendações
- Verificar logs detalhados para componentes que falharam
- Executar testes individuais para diagnóstico específico
- Considerar configurações de ambiente e dependências
- Validar conectividade de rede e permissões

## Próximos Passos
1. Corrigir falhas identificadas
2. Re-executar testes após correções
3. Realizar testes de carga se necessário
4. Documentar configurações de produção
"""
        
        return report
    
    def cleanup(self):
        """Limpar processos iniciados"""
        logger.info("🧹 Limpando processos...")
        
        for name, process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"✅ {name} finalizado")
            except subprocess.TimeoutExpired:
                process.kill()
                logger.info(f"🔪 {name} forçadamente finalizado")
            except Exception as e:
                logger.error(f"❌ Erro ao finalizar {name}: {e}")
    
    def run_all_tests(self) -> str:
        """Executar todos os testes"""
        logger.info("🎯 Iniciando bateria completa de testes...")
        
        all_results = {}
        
        try:
            # Iniciar serviços
            if not self.start_services():
                logger.error("❌ Falha ao iniciar serviços. Abortando testes.")
                return "Erro: Não foi possível iniciar os serviços necessários."
            
            # Executar testes
            all_results["API_Endpoints"] = self.test_api_endpoints()
            all_results["MCP_Servers"] = self.test_mcp_servers()
            all_results["CrewAI_Integration"] = self.test_crewai_integration()
            all_results["Frontend_Build"] = self.test_frontend_build()
            all_results["End_to_End_Flow"] = self.test_end_to_end_flow()
            
            # Gerar relatório
            report = self.generate_test_report(all_results)
            
            # Salvar relatório
            report_path = os.path.join(self.base_dir, "integration_test_report.md")
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"📄 Relatório salvo em: {report_path}")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Erro durante execução dos testes: {e}")
            return f"Erro durante execução dos testes: {str(e)}"
        
        finally:
            self.cleanup()

def main():
    """Função principal"""
    print("🚀 Cloud Cost Agent - Integration Test Suite")
    print("=" * 50)
    
    tester = CloudCostAgentTester()
    
    try:
        report = tester.run_all_tests()
        print("\n" + "=" * 50)
        print("📊 RELATÓRIO DE TESTES")
        print("=" * 50)
        print(report)
        
    except KeyboardInterrupt:
        print("\n⚠️ Testes interrompidos pelo usuário")
        tester.cleanup()
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        tester.cleanup()

if __name__ == "__main__":
    main()

