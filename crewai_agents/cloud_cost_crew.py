#!/usr/bin/env python3
"""
Cloud Cost Analysis Crew

Sistema CrewAI com agentes especializados para análise de custos de nuvem.
Utiliza servidores MCP para conectar com APIs da AWS e Google Cloud.
"""

import os
import json
import logging
from typing import Dict, List, Any
from datetime import datetime

from crewai import Agent, Task, Crew, Process
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloudCostAnalysisCrew:
    """Crew para análise de custos de nuvem"""
    
    def __init__(self):
        self.setup_mcp_servers()
        self.setup_agents()
    
    def setup_mcp_servers(self):
        """Configurar servidores MCP"""
        
        # Configurações dos servidores MCP
        self.aws_server_params = StdioServerParameters(
            command="python3",
            args=[os.path.join(os.path.dirname(__file__), "..", "mcp_servers", "aws_pricing_server.py")],
            env={"PYTHONPATH": os.path.dirname(__file__), **os.environ}
        )
        
        self.gcp_server_params = StdioServerParameters(
            command="python3",
            args=[os.path.join(os.path.dirname(__file__), "..", "mcp_servers", "gcp_pricing_server.py")],
            env={"PYTHONPATH": os.path.dirname(__file__), **os.environ}
        )
        
        self.comparison_server_params = StdioServerParameters(
            command="python3",
            args=[os.path.join(os.path.dirname(__file__), "..", "mcp_servers", "comparison_server.py")],
            env={"PYTHONPATH": os.path.dirname(__file__), **os.environ}
        )
    
    def setup_agents(self):
        """Configurar agentes especializados"""
        
        # AWS Specialist Agent
        self.aws_specialist = Agent(
            role="AWS Cost Specialist",
            goal="Analisar custos, performance e características de serviços AWS",
            backstory="""Você é um especialista em AWS com mais de 10 anos de experiência.
            Conhece profundamente todos os serviços AWS, modelos de preços, e otimizações de custo.
            Sua expertise inclui EC2, S3, RDS, Lambda, e todos os aspectos de billing da AWS.
            Você sempre fornece análises detalhadas e precisas sobre custos e performance.""",
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
        
        # Google Cloud Specialist Agent
        self.gcp_specialist = Agent(
            role="Google Cloud Cost Specialist",
            goal="Analisar custos, performance e características de serviços Google Cloud",
            backstory="""Você é um especialista em Google Cloud Platform com vasta experiência.
            Domina Compute Engine, Cloud Storage, BigQuery, Cloud Functions e todos os aspectos
            de billing do GCP. Conhece as nuances dos descontos por uso sustentado e
            committed use discounts. Sempre fornece análises técnicas detalhadas.""",
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
        
        # Cost Analysis Coordinator
        self.cost_coordinator = Agent(
            role="Cloud Cost Analysis Coordinator",
            goal="Coordenar análises comparativas e gerar recomendações fundamentadas",
            backstory="""Você é um arquiteto de nuvem sênior com experiência em múltiplos
            provedores. Sua especialidade é análise comparativa de custos, TCO (Total Cost
            of Ownership), e estratégias de otimização. Você considera não apenas custos,
            mas também performance, escalabilidade, confiabilidade e facilidade de manutenção.
            Suas recomendações são sempre baseadas em dados concretos e análises rigorosas.""",
            verbose=True,
            allow_delegation=True,
            max_iter=5
        )
        
        # Report Generator Agent
        self.report_generator = Agent(
            role="Technical Report Generator",
            goal="Criar relatórios técnicos detalhados e apresentações executivas",
            backstory="""Você é um analista técnico especializado em documentação e
            comunicação de resultados complexos. Transforma análises técnicas em relatórios
            claros, acionáveis e bem estruturados. Seus relatórios incluem resumos executivos,
            análises detalhadas, recomendações práticas e próximos passos. Você sempre
            adapta o conteúdo para diferentes audiências técnicas e executivas.""",
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
    
    def analyze_compute_costs(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Analisar custos de computação"""
        
        # Extrair parâmetros
        instance_type_aws = requirements.get('aws_instance_type', 't3.medium')
        machine_type_gcp = requirements.get('gcp_machine_type', 'e2-medium')
        region_aws = requirements.get('aws_region', 'us-east-1')
        region_gcp = requirements.get('gcp_region', 'us-central1')
        workload_type = requirements.get('workload_type', 'general')
        
        # Definir tarefas
        aws_analysis_task = Task(
            description=f"""Analise os custos e características da instância AWS {instance_type_aws} 
            na região {region_aws}. Inclua:
            1. Preços por hora e mensais
            2. Características técnicas
            3. Opções de otimização de custo
            4. Comparação com outras instâncias similares
            
            Use as ferramentas MCP disponíveis para obter dados precisos.""",
            agent=self.aws_specialist,
            expected_output="Análise detalhada dos custos AWS com dados específicos da instância"
        )
        
        gcp_analysis_task = Task(
            description=f"""Analise os custos e características da instância GCP {machine_type_gcp} 
            na região {region_gcp}. Inclua:
            1. Preços por hora e mensais
            2. Características técnicas
            3. Descontos por uso sustentado
            4. Comparação com outras instâncias similares
            
            Use as ferramentas MCP disponíveis para obter dados precisos.""",
            agent=self.gcp_specialist,
            expected_output="Análise detalhada dos custos GCP com dados específicos da instância"
        )
        
        comparison_task = Task(
            description=f"""Com base nas análises dos especialistas AWS e GCP, realize uma 
            comparação abrangente considerando:
            1. Custos diretos e TCO
            2. Performance para workload tipo '{workload_type}'
            3. Escalabilidade e confiabilidade
            4. Facilidade de manutenção
            5. Recomendação final fundamentada
            
            Use ferramentas de comparação para análise quantitativa.""",
            agent=self.cost_coordinator,
            expected_output="Comparação detalhada com recomendação fundamentada",
            context=[aws_analysis_task, gcp_analysis_task]
        )
        
        report_task = Task(
            description="""Crie um relatório executivo completo da análise de custos de computação.
            O relatório deve incluir:
            1. Resumo executivo com recomendação principal
            2. Análise detalhada de custos
            3. Comparação técnica
            4. Análise de TCO
            5. Próximos passos e implementação
            
            Formate o relatório de forma profissional e acionável.""",
            agent=self.report_generator,
            expected_output="Relatório executivo completo em formato estruturado",
            context=[aws_analysis_task, gcp_analysis_task, comparison_task]
        )
        
        # Configurar ferramentas MCP para cada agente
        try:
            with MCPServerAdapter(self.aws_server_params) as aws_tools:
                self.aws_specialist.tools = list(aws_tools)
                
                with MCPServerAdapter(self.gcp_server_params) as gcp_tools:
                    self.gcp_specialist.tools = list(gcp_tools)
                    
                    with MCPServerAdapter(self.comparison_server_params) as comparison_tools:
                        self.cost_coordinator.tools = list(comparison_tools)
                        
                        # Criar e executar crew
                        crew = Crew(
                            agents=[self.aws_specialist, self.gcp_specialist, 
                                   self.cost_coordinator, self.report_generator],
                            tasks=[aws_analysis_task, gcp_analysis_task, 
                                  comparison_task, report_task],
                            process=Process.sequential,
                            verbose=True
                        )
                        
                        result = crew.kickoff()
                        
                        return {
                            'analysis_type': 'compute_costs',
                            'requirements': requirements,
                            'result': str(result),
                            'timestamp': datetime.now().isoformat()
                        }
        
        except Exception as e:
            logger.error(f"Erro na análise de custos de computação: {e}")
            return {
                'analysis_type': 'compute_costs',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def analyze_storage_costs(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Analisar custos de armazenamento"""
        
        # Extrair parâmetros
        aws_storage_type = requirements.get('aws_storage_type', 's3_standard')
        gcp_storage_type = requirements.get('gcp_storage_type', 'standard')
        region_aws = requirements.get('aws_region', 'us-east-1')
        region_gcp = requirements.get('gcp_region', 'us-central1')
        storage_size_gb = requirements.get('storage_size_gb', 1000)
        
        # Definir tarefas
        aws_storage_task = Task(
            description=f"""Analise os custos de armazenamento AWS {aws_storage_type} 
            na região {region_aws} para {storage_size_gb} GB. Inclua:
            1. Custos por GB/mês
            2. Custos de transferência
            3. Características do tipo de armazenamento
            4. Estimativas para diferentes volumes
            
            Use as ferramentas MCP para obter dados precisos.""",
            agent=self.aws_specialist,
            expected_output="Análise detalhada dos custos de armazenamento AWS"
        )
        
        gcp_storage_task = Task(
            description=f"""Analise os custos de armazenamento GCP {gcp_storage_type} 
            na região {region_gcp} para {storage_size_gb} GB. Inclua:
            1. Custos por GB/mês
            2. Custos de transferência
            3. Características do tipo de armazenamento
            4. Estimativas para diferentes volumes
            
            Use as ferramentas MCP para obter dados precisos.""",
            agent=self.gcp_specialist,
            expected_output="Análise detalhada dos custos de armazenamento GCP"
        )
        
        storage_comparison_task = Task(
            description=f"""Compare as opções de armazenamento AWS e GCP analisadas.
            Considere:
            1. Custos diretos por GB
            2. Durabilidade e disponibilidade
            3. Performance de acesso
            4. Casos de uso recomendados
            5. Recomendação baseada nos requisitos
            
            Use ferramentas de comparação para análise quantitativa.""",
            agent=self.cost_coordinator,
            expected_output="Comparação detalhada de armazenamento com recomendação",
            context=[aws_storage_task, gcp_storage_task]
        )
        
        storage_report_task = Task(
            description="""Crie um relatório completo da análise de custos de armazenamento.
            Inclua:
            1. Resumo executivo
            2. Comparação de custos
            3. Análise técnica
            4. Recomendações de implementação
            5. Considerações de migração
            
            Formate profissionalmente para apresentação.""",
            agent=self.report_generator,
            expected_output="Relatório executivo de análise de armazenamento",
            context=[aws_storage_task, gcp_storage_task, storage_comparison_task]
        )
        
        # Executar análise com ferramentas MCP
        try:
            with MCPServerAdapter(self.aws_server_params) as aws_tools:
                self.aws_specialist.tools = list(aws_tools)
                
                with MCPServerAdapter(self.gcp_server_params) as gcp_tools:
                    self.gcp_specialist.tools = list(gcp_tools)
                    
                    with MCPServerAdapter(self.comparison_server_params) as comparison_tools:
                        self.cost_coordinator.tools = list(comparison_tools)
                        
                        crew = Crew(
                            agents=[self.aws_specialist, self.gcp_specialist, 
                                   self.cost_coordinator, self.report_generator],
                            tasks=[aws_storage_task, gcp_storage_task, 
                                  storage_comparison_task, storage_report_task],
                            process=Process.sequential,
                            verbose=True
                        )
                        
                        result = crew.kickoff()
                        
                        return {
                            'analysis_type': 'storage_costs',
                            'requirements': requirements,
                            'result': str(result),
                            'timestamp': datetime.now().isoformat()
                        }
        
        except Exception as e:
            logger.error(f"Erro na análise de custos de armazenamento: {e}")
            return {
                'analysis_type': 'storage_costs',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def comprehensive_analysis(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Análise abrangente incluindo computação, armazenamento e TCO"""
        
        # Definir tarefas abrangentes
        aws_comprehensive_task = Task(
            description=f"""Realize uma análise abrangente dos custos AWS baseada nos requisitos:
            {json.dumps(requirements, indent=2)}
            
            Analise:
            1. Custos de computação (instâncias EC2)
            2. Custos de armazenamento (S3, EBS)
            3. Custos de rede e transferência
            4. Serviços adicionais relevantes
            5. Opções de otimização e descontos
            
            Forneça estimativas detalhadas e recomendações.""",
            agent=self.aws_specialist,
            expected_output="Análise abrangente dos custos AWS com todas as categorias"
        )
        
        gcp_comprehensive_task = Task(
            description=f"""Realize uma análise abrangente dos custos GCP baseada nos requisitos:
            {json.dumps(requirements, indent=2)}
            
            Analise:
            1. Custos de computação (Compute Engine)
            2. Custos de armazenamento (Cloud Storage, Persistent Disk)
            3. Custos de rede e transferência
            4. Serviços adicionais relevantes
            5. Descontos por uso sustentado e committed use
            
            Forneça estimativas detalhadas e recomendações.""",
            agent=self.gcp_specialist,
            expected_output="Análise abrangente dos custos GCP com todas as categorias"
        )
        
        comprehensive_comparison_task = Task(
            description="""Realize uma comparação abrangente entre AWS e GCP baseada nas 
            análises dos especialistas. Inclua:
            
            1. Comparação de custos por categoria
            2. Análise de TCO (Total Cost of Ownership)
            3. Análise de performance e escalabilidade
            4. Considerações de confiabilidade e manutenção
            5. Recomendação final com justificativa detalhada
            6. Plano de migração (se aplicável)
            
            Use todas as ferramentas de comparação disponíveis.""",
            agent=self.cost_coordinator,
            expected_output="Comparação abrangente com recomendação estratégica",
            context=[aws_comprehensive_task, gcp_comprehensive_task]
        )
        
        final_report_task = Task(
            description="""Crie um relatório executivo completo da análise abrangente.
            O relatório deve ser estruturado para apresentação a stakeholders técnicos
            e executivos. Inclua:
            
            1. Resumo Executivo
               - Recomendação principal
               - Economia potencial
               - Próximos passos críticos
            
            2. Análise Detalhada
               - Comparação de custos por categoria
               - Análise de TCO
               - Considerações técnicas
            
            3. Implementação
               - Plano de migração
               - Timeline estimado
               - Riscos e mitigações
            
            4. Apêndices
               - Dados detalhados
               - Metodologia
               - Referências
            
            Formate profissionalmente com gráficos conceituais e tabelas.""",
            agent=self.report_generator,
            expected_output="Relatório executivo completo e profissional",
            context=[aws_comprehensive_task, gcp_comprehensive_task, comprehensive_comparison_task]
        )
        
        # Executar análise abrangente
        try:
            with MCPServerAdapter(self.aws_server_params) as aws_tools:
                self.aws_specialist.tools = list(aws_tools)
                
                with MCPServerAdapter(self.gcp_server_params) as gcp_tools:
                    self.gcp_specialist.tools = list(gcp_tools)
                    
                    with MCPServerAdapter(self.comparison_server_params) as comparison_tools:
                        self.cost_coordinator.tools = list(comparison_tools)
                        
                        crew = Crew(
                            agents=[self.aws_specialist, self.gcp_specialist, 
                                   self.cost_coordinator, self.report_generator],
                            tasks=[aws_comprehensive_task, gcp_comprehensive_task, 
                                  comprehensive_comparison_task, final_report_task],
                            process=Process.sequential,
                            verbose=True,
                            max_rpm=10  # Limitar RPM para evitar rate limiting
                        )
                        
                        result = crew.kickoff()
                        
                        return {
                            'analysis_type': 'comprehensive',
                            'requirements': requirements,
                            'result': str(result),
                            'timestamp': datetime.now().isoformat()
                        }
        
        except Exception as e:
            logger.error(f"Erro na análise abrangente: {e}")
            return {
                'analysis_type': 'comprehensive',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

def main():
    """Função principal para testes"""
    crew = CloudCostAnalysisCrew()
    
    # Exemplo de requisitos
    test_requirements = {
        'aws_instance_type': 't3.medium',
        'gcp_machine_type': 'e2-medium',
        'aws_region': 'us-east-1',
        'gcp_region': 'us-central1',
        'workload_type': 'general',
        'aws_storage_type': 's3_standard',
        'gcp_storage_type': 'standard',
        'storage_size_gb': 1000,
        'monthly_budget': 500,
        'performance_priority': 'balanced'
    }
    
    print("Iniciando análise de custos de computação...")
    result = crew.analyze_compute_costs(test_requirements)
    print(f"Resultado: {result}")

if __name__ == "__main__":
    main()

