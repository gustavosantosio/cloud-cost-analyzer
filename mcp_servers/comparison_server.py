#!/usr/bin/env python3
"""
Cloud Comparison MCP Server

Este servidor MCP fornece ferramentas para comparação entre provedores de nuvem.
Analisa dados de AWS e Google Cloud para gerar recomendações fundamentadas.
"""

import asyncio
import json
import logging
import math
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from mcp.server.fastmcp import FastMCP

# Configurar logging para stderr (não stdout para MCP)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Inicializar servidor MCP
mcp = FastMCP("cloud-comparison")

class CloudComparisonEngine:
    """Engine para comparação entre provedores de nuvem"""
    
    def __init__(self):
        # Fatores de peso para diferentes critérios
        self.weights = {
            'cost': 0.35,           # 35% - Custo
            'performance': 0.25,    # 25% - Performance
            'scalability': 0.20,    # 20% - Escalabilidade
            'reliability': 0.15,    # 15% - Confiabilidade
            'maintenance': 0.05     # 5% - Facilidade de manutenção
        }
        
        # Dados de performance e características dos provedores
        self.provider_characteristics = {
            'aws': {
                'performance_multiplier': 1.0,
                'scalability_score': 9.5,
                'reliability_score': 9.8,
                'maintenance_score': 8.5,
                'global_presence': 9.9,
                'service_maturity': 9.8
            },
            'gcp': {
                'performance_multiplier': 1.05,  # Ligeiramente melhor performance
                'scalability_score': 9.3,
                'reliability_score': 9.6,
                'maintenance_score': 9.2,
                'global_presence': 8.8,
                'service_maturity': 8.9
            }
        }
    
    def compare_compute_instances(self, aws_data: Dict, gcp_data: Dict, 
                                workload_requirements: Dict) -> Dict[str, Any]:
        """Comparar instâncias de computação entre AWS e GCP"""
        
        # Normalizar dados de preços
        aws_monthly_cost = aws_data.get('price_per_month', 0)
        gcp_monthly_cost = gcp_data.get('price_per_month', 0)
        
        # Calcular scores
        cost_score = self._calculate_cost_score(aws_monthly_cost, gcp_monthly_cost)
        performance_score = self._calculate_performance_score('aws', 'gcp', workload_requirements)
        scalability_score = self._calculate_scalability_score('aws', 'gcp')
        reliability_score = self._calculate_reliability_score('aws', 'gcp')
        maintenance_score = self._calculate_maintenance_score('aws', 'gcp')
        
        # Score final ponderado
        aws_final_score = (
            cost_score['aws'] * self.weights['cost'] +
            performance_score['aws'] * self.weights['performance'] +
            scalability_score['aws'] * self.weights['scalability'] +
            reliability_score['aws'] * self.weights['reliability'] +
            maintenance_score['aws'] * self.weights['maintenance']
        )
        
        gcp_final_score = (
            cost_score['gcp'] * self.weights['cost'] +
            performance_score['gcp'] * self.weights['performance'] +
            scalability_score['gcp'] * self.weights['scalability'] +
            reliability_score['gcp'] * self.weights['reliability'] +
            maintenance_score['gcp'] * self.weights['maintenance']
        )
        
        # Determinar vencedor
        winner = 'aws' if aws_final_score > gcp_final_score else 'gcp'
        
        return {
            'comparison_type': 'compute_instances',
            'aws_instance': aws_data.get('instance_type', 'N/A'),
            'gcp_instance': gcp_data.get('machine_type', 'N/A'),
            'aws_cost': aws_monthly_cost,
            'gcp_cost': gcp_monthly_cost,
            'cost_difference': abs(aws_monthly_cost - gcp_monthly_cost),
            'cost_savings_provider': 'aws' if aws_monthly_cost < gcp_monthly_cost else 'gcp',
            'cost_savings_percentage': abs((aws_monthly_cost - gcp_monthly_cost) / max(aws_monthly_cost, gcp_monthly_cost)) * 100,
            'scores': {
                'aws': {
                    'cost': cost_score['aws'],
                    'performance': performance_score['aws'],
                    'scalability': scalability_score['aws'],
                    'reliability': reliability_score['aws'],
                    'maintenance': maintenance_score['aws'],
                    'final': aws_final_score
                },
                'gcp': {
                    'cost': cost_score['gcp'],
                    'performance': performance_score['gcp'],
                    'scalability': scalability_score['gcp'],
                    'reliability': reliability_score['gcp'],
                    'maintenance': maintenance_score['gcp'],
                    'final': gcp_final_score
                }
            },
            'recommendation': {
                'winner': winner,
                'confidence': abs(aws_final_score - gcp_final_score) / 10,
                'primary_reasons': self._get_primary_reasons(winner, cost_score, performance_score, scalability_score)
            }
        }
    
    def compare_storage_options(self, aws_data: Dict, gcp_data: Dict) -> Dict[str, Any]:
        """Comparar opções de armazenamento entre AWS e GCP"""
        
        aws_cost = aws_data.get('price_per_gb_month', 0)
        gcp_cost = gcp_data.get('price_per_gb_month', 0)
        
        # Análise de custo
        cost_difference = abs(aws_cost - gcp_cost)
        cost_savings_provider = 'aws' if aws_cost < gcp_cost else 'gcp'
        cost_savings_percentage = (cost_difference / max(aws_cost, gcp_cost)) * 100
        
        # Características de armazenamento
        storage_analysis = self._analyze_storage_characteristics(
            aws_data.get('storage_type', ''),
            gcp_data.get('storage_type', '')
        )
        
        return {
            'comparison_type': 'storage',
            'aws_storage': aws_data.get('storage_type', 'N/A'),
            'gcp_storage': gcp_data.get('storage_type', 'N/A'),
            'aws_cost_per_gb': aws_cost,
            'gcp_cost_per_gb': gcp_cost,
            'cost_difference': cost_difference,
            'cost_savings_provider': cost_savings_provider,
            'cost_savings_percentage': cost_savings_percentage,
            'storage_analysis': storage_analysis,
            'recommendation': {
                'winner': cost_savings_provider,
                'confidence': min(cost_savings_percentage / 20, 1.0),  # Normalizar para 0-1
                'reasoning': f"{'AWS' if cost_savings_provider == 'aws' else 'GCP'} oferece {cost_savings_percentage:.1f}% de economia"
            }
        }
    
    def calculate_tco(self, compute_costs: Dict, storage_costs: Dict, 
                     additional_services: Dict, time_horizon_months: int = 36) -> Dict[str, Any]:
        """Calcular Total Cost of Ownership (TCO)"""
        
        # Custos base
        aws_compute_monthly = compute_costs.get('aws', 0)
        gcp_compute_monthly = compute_costs.get('gcp', 0)
        
        aws_storage_monthly = storage_costs.get('aws', 0)
        gcp_storage_monthly = storage_costs.get('gcp', 0)
        
        # Custos adicionais (rede, suporte, etc.)
        aws_additional_monthly = additional_services.get('aws', 0)
        gcp_additional_monthly = additional_services.get('gcp', 0)
        
        # Custos operacionais (estimativa)
        aws_operational_monthly = (aws_compute_monthly + aws_storage_monthly) * 0.15  # 15% dos custos de infra
        gcp_operational_monthly = (gcp_compute_monthly + gcp_storage_monthly) * 0.12  # 12% (melhor automação)
        
        # TCO total
        aws_monthly_total = aws_compute_monthly + aws_storage_monthly + aws_additional_monthly + aws_operational_monthly
        gcp_monthly_total = gcp_compute_monthly + gcp_storage_monthly + gcp_additional_monthly + gcp_operational_monthly
        
        aws_tco = aws_monthly_total * time_horizon_months
        gcp_tco = gcp_monthly_total * time_horizon_months
        
        # Análise de economia
        savings = abs(aws_tco - gcp_tco)
        savings_provider = 'aws' if aws_tco < gcp_tco else 'gcp'
        savings_percentage = (savings / max(aws_tco, gcp_tco)) * 100
        
        return {
            'time_horizon_months': time_horizon_months,
            'aws_tco': aws_tco,
            'gcp_tco': gcp_tco,
            'savings': savings,
            'savings_provider': savings_provider,
            'savings_percentage': savings_percentage,
            'breakdown': {
                'aws': {
                    'compute_monthly': aws_compute_monthly,
                    'storage_monthly': aws_storage_monthly,
                    'additional_monthly': aws_additional_monthly,
                    'operational_monthly': aws_operational_monthly,
                    'total_monthly': aws_monthly_total
                },
                'gcp': {
                    'compute_monthly': gcp_compute_monthly,
                    'storage_monthly': gcp_storage_monthly,
                    'additional_monthly': gcp_additional_monthly,
                    'operational_monthly': gcp_operational_monthly,
                    'total_monthly': gcp_monthly_total
                }
            }
        }
    
    def _calculate_cost_score(self, aws_cost: float, gcp_cost: float) -> Dict[str, float]:
        """Calcular score de custo (menor custo = maior score)"""
        if aws_cost == 0 and gcp_cost == 0:
            return {'aws': 5.0, 'gcp': 5.0}
        
        total_cost = aws_cost + gcp_cost
        if total_cost == 0:
            return {'aws': 5.0, 'gcp': 5.0}
        
        # Score inversamente proporcional ao custo
        aws_score = (gcp_cost / total_cost) * 10
        gcp_score = (aws_cost / total_cost) * 10
        
        return {'aws': aws_score, 'gcp': gcp_score}
    
    def _calculate_performance_score(self, provider1: str, provider2: str, 
                                   workload_requirements: Dict) -> Dict[str, float]:
        """Calcular score de performance"""
        aws_char = self.provider_characteristics['aws']
        gcp_char = self.provider_characteristics['gcp']
        
        # Ajustar baseado no tipo de workload
        workload_type = workload_requirements.get('type', 'general')
        
        if workload_type == 'compute_intensive':
            aws_score = 8.5
            gcp_score = 9.0  # GCP tem vantagem em compute intensivo
        elif workload_type == 'data_intensive':
            aws_score = 9.2
            gcp_score = 8.8  # AWS tem mais opções de storage
        else:  # general purpose
            aws_score = 8.8
            gcp_score = 8.9
        
        return {'aws': aws_score, 'gcp': gcp_score}
    
    def _calculate_scalability_score(self, provider1: str, provider2: str) -> Dict[str, float]:
        """Calcular score de escalabilidade"""
        return {
            'aws': self.provider_characteristics['aws']['scalability_score'],
            'gcp': self.provider_characteristics['gcp']['scalability_score']
        }
    
    def _calculate_reliability_score(self, provider1: str, provider2: str) -> Dict[str, float]:
        """Calcular score de confiabilidade"""
        return {
            'aws': self.provider_characteristics['aws']['reliability_score'],
            'gcp': self.provider_characteristics['gcp']['reliability_score']
        }
    
    def _calculate_maintenance_score(self, provider1: str, provider2: str) -> Dict[str, float]:
        """Calcular score de facilidade de manutenção"""
        return {
            'aws': self.provider_characteristics['aws']['maintenance_score'],
            'gcp': self.provider_characteristics['gcp']['maintenance_score']
        }
    
    def _get_primary_reasons(self, winner: str, cost_score: Dict, 
                           performance_score: Dict, scalability_score: Dict) -> List[str]:
        """Obter principais razões para a recomendação"""
        reasons = []
        
        if cost_score[winner] > cost_score['aws' if winner == 'gcp' else 'gcp']:
            reasons.append("Melhor custo-benefício")
        
        if performance_score[winner] > performance_score['aws' if winner == 'gcp' else 'gcp']:
            reasons.append("Superior performance")
        
        if scalability_score[winner] > scalability_score['aws' if winner == 'gcp' else 'gcp']:
            reasons.append("Melhor escalabilidade")
        
        return reasons[:3]  # Máximo 3 razões
    
    def _analyze_storage_characteristics(self, aws_type: str, gcp_type: str) -> Dict[str, Any]:
        """Analisar características dos tipos de armazenamento"""
        
        storage_characteristics = {
            's3_standard': {'durability': '99.999999999%', 'availability': '99.99%', 'use_case': 'Acesso frequente'},
            's3_ia': {'durability': '99.999999999%', 'availability': '99.9%', 'use_case': 'Acesso infrequente'},
            's3_glacier': {'durability': '99.999999999%', 'availability': 'N/A', 'use_case': 'Arquivamento'},
            'standard': {'durability': '99.999999999%', 'availability': '99.95%', 'use_case': 'Acesso frequente'},
            'nearline': {'durability': '99.999999999%', 'availability': '99.95%', 'use_case': 'Backup mensal'},
            'coldline': {'durability': '99.999999999%', 'availability': '99.95%', 'use_case': 'Arquivamento'},
            'archive': {'durability': '99.999999999%', 'availability': '99.95%', 'use_case': 'Arquivamento longo prazo'}
        }
        
        aws_char = storage_characteristics.get(aws_type, {})
        gcp_char = storage_characteristics.get(gcp_type, {})
        
        return {
            'aws_characteristics': aws_char,
            'gcp_characteristics': gcp_char,
            'comparison': {
                'durability': 'Equivalente' if aws_char.get('durability') == gcp_char.get('durability') else 'Diferente',
                'availability': 'AWS superior' if aws_char.get('availability', '0%') > gcp_char.get('availability', '0%') else 'GCP superior'
            }
        }

# Instanciar engine de comparação
comparison_engine = CloudComparisonEngine()

@mcp.tool()
async def compare_cloud_instances(aws_instance_data: str, gcp_instance_data: str, 
                                workload_type: str = "general") -> str:
    """
    Comparar instâncias entre AWS e Google Cloud.
    
    Args:
        aws_instance_data: Dados da instância AWS em formato JSON
        gcp_instance_data: Dados da instância GCP em formato JSON
        workload_type: Tipo de workload (general, compute_intensive, data_intensive)
    
    Returns:
        Análise comparativa detalhada entre as instâncias
    """
    try:
        # Parsear dados JSON
        aws_data = json.loads(aws_instance_data)
        gcp_data = json.loads(gcp_instance_data)
        
        workload_requirements = {'type': workload_type}
        
        # Realizar comparação
        comparison = comparison_engine.compare_compute_instances(
            aws_data, gcp_data, workload_requirements
        )
        
        winner_name = "AWS" if comparison['recommendation']['winner'] == 'aws' else "Google Cloud"
        confidence = comparison['recommendation']['confidence']
        
        result = f"""
🔍 Comparação de Instâncias de Nuvem

📊 Instâncias Comparadas:
- AWS: {comparison['aws_instance']}
- GCP: {comparison['gcp_instance']}

💰 Análise de Custos:
- AWS: ${comparison['aws_cost']:.2f}/mês
- GCP: ${comparison['gcp_cost']:.2f}/mês
- Diferença: ${comparison['cost_difference']:.2f}/mês
- Economia com {comparison['cost_savings_provider'].upper()}: {comparison['cost_savings_percentage']:.1f}%

📈 Scores Detalhados (0-10):

AWS:
- Custo: {comparison['scores']['aws']['cost']:.1f}/10
- Performance: {comparison['scores']['aws']['performance']:.1f}/10
- Escalabilidade: {comparison['scores']['aws']['scalability']:.1f}/10
- Confiabilidade: {comparison['scores']['aws']['reliability']:.1f}/10
- Manutenção: {comparison['scores']['aws']['maintenance']:.1f}/10
- Score Final: {comparison['scores']['aws']['final']:.1f}/10

Google Cloud:
- Custo: {comparison['scores']['gcp']['cost']:.1f}/10
- Performance: {comparison['scores']['gcp']['performance']:.1f}/10
- Escalabilidade: {comparison['scores']['gcp']['scalability']:.1f}/10
- Confiabilidade: {comparison['scores']['gcp']['reliability']:.1f}/10
- Manutenção: {comparison['scores']['gcp']['maintenance']:.1f}/10
- Score Final: {comparison['scores']['gcp']['final']:.1f}/10

🏆 RECOMENDAÇÃO: {winner_name}
📊 Confiança: {confidence:.1%}

💡 Principais Razões:
"""
        
        for reason in comparison['recommendation']['primary_reasons']:
            result += f"- {reason}\n"
        
        result += f"""
🎯 Tipo de Workload: {workload_type}

💡 Considerações Adicionais:
- Para workloads compute-intensivos, GCP pode ter vantagem
- Para workloads data-intensivos, AWS oferece mais opções
- Considere também fatores como localização geográfica e compliance
"""
        
        return result
        
    except json.JSONDecodeError:
        return "Erro: Dados JSON inválidos fornecidos"
    except Exception as e:
        logger.error(f"Erro na comparação de instâncias: {e}")
        return f"Erro na comparação de instâncias: {str(e)}"

@mcp.tool()
async def compare_storage_costs(aws_storage_data: str, gcp_storage_data: str) -> str:
    """
    Comparar custos de armazenamento entre AWS e Google Cloud.
    
    Args:
        aws_storage_data: Dados de armazenamento AWS em formato JSON
        gcp_storage_data: Dados de armazenamento GCP em formato JSON
    
    Returns:
        Análise comparativa de custos de armazenamento
    """
    try:
        # Parsear dados JSON
        aws_data = json.loads(aws_storage_data)
        gcp_data = json.loads(gcp_storage_data)
        
        # Realizar comparação
        comparison = comparison_engine.compare_storage_options(aws_data, gcp_data)
        
        winner_name = "AWS" if comparison['recommendation']['winner'] == 'aws' else "Google Cloud"
        
        result = f"""
💾 Comparação de Armazenamento em Nuvem

📊 Tipos de Armazenamento:
- AWS: {comparison['aws_storage']}
- GCP: {comparison['gcp_storage']}

💰 Análise de Custos por GB/mês:
- AWS: ${comparison['aws_cost_per_gb']:.4f}
- GCP: ${comparison['gcp_cost_per_gb']:.4f}
- Diferença: ${comparison['cost_difference']:.4f}
- Economia com {comparison['cost_savings_provider'].upper()}: {comparison['cost_savings_percentage']:.1f}%

📈 Estimativas de Custo Mensal:
- 100 GB: AWS ${comparison['aws_cost_per_gb'] * 100:.2f} vs GCP ${comparison['gcp_cost_per_gb'] * 100:.2f}
- 1 TB: AWS ${comparison['aws_cost_per_gb'] * 1024:.2f} vs GCP ${comparison['gcp_cost_per_gb'] * 1024:.2f}
- 10 TB: AWS ${comparison['aws_cost_per_gb'] * 10240:.2f} vs GCP ${comparison['gcp_cost_per_gb'] * 10240:.2f}

🏆 RECOMENDAÇÃO: {winner_name}
📊 Confiança: {comparison['recommendation']['confidence']:.1%}
💡 Razão: {comparison['recommendation']['reasoning']}

🔍 Características Técnicas:
"""
        
        # Adicionar características se disponíveis
        if 'storage_analysis' in comparison:
            aws_char = comparison['storage_analysis']['aws_characteristics']
            gcp_char = comparison['storage_analysis']['gcp_characteristics']
            
            if aws_char:
                result += f"\nAWS ({comparison['aws_storage']}):\n"
                for key, value in aws_char.items():
                    result += f"- {key.title()}: {value}\n"
            
            if gcp_char:
                result += f"\nGCP ({comparison['gcp_storage']}):\n"
                for key, value in gcp_char.items():
                    result += f"- {key.title()}: {value}\n"
        
        return result
        
    except json.JSONDecodeError:
        return "Erro: Dados JSON inválidos fornecidos"
    except Exception as e:
        logger.error(f"Erro na comparação de armazenamento: {e}")
        return f"Erro na comparação de armazenamento: {str(e)}"

@mcp.tool()
async def calculate_total_cost_ownership(compute_costs_json: str, storage_costs_json: str, 
                                       additional_services_json: str = '{"aws": 0, "gcp": 0}',
                                       time_horizon_months: int = 36) -> str:
    """
    Calcular Total Cost of Ownership (TCO) para ambos os provedores.
    
    Args:
        compute_costs_json: Custos mensais de computação em JSON {"aws": valor, "gcp": valor}
        storage_costs_json: Custos mensais de armazenamento em JSON {"aws": valor, "gcp": valor}
        additional_services_json: Custos adicionais mensais em JSON {"aws": valor, "gcp": valor}
        time_horizon_months: Horizonte de tempo em meses (padrão: 36)
    
    Returns:
        Análise detalhada do TCO
    """
    try:
        # Parsear dados JSON
        compute_costs = json.loads(compute_costs_json)
        storage_costs = json.loads(storage_costs_json)
        additional_services = json.loads(additional_services_json)
        
        # Calcular TCO
        tco_analysis = comparison_engine.calculate_tco(
            compute_costs, storage_costs, additional_services, time_horizon_months
        )
        
        winner_name = "AWS" if tco_analysis['savings_provider'] == 'aws' else "Google Cloud"
        
        result = f"""
💼 Análise de Total Cost of Ownership (TCO)

⏰ Horizonte de Tempo: {time_horizon_months} meses ({time_horizon_months/12:.1f} anos)

💰 TCO Total:
- AWS: ${tco_analysis['aws_tco']:,.2f}
- GCP: ${tco_analysis['gcp_tco']:,.2f}
- Economia com {winner_name}: ${tco_analysis['savings']:,.2f} ({tco_analysis['savings_percentage']:.1f}%)

📊 Breakdown Mensal:

AWS:
- Computação: ${tco_analysis['breakdown']['aws']['compute_monthly']:.2f}
- Armazenamento: ${tco_analysis['breakdown']['aws']['storage_monthly']:.2f}
- Serviços Adicionais: ${tco_analysis['breakdown']['aws']['additional_monthly']:.2f}
- Custos Operacionais: ${tco_analysis['breakdown']['aws']['operational_monthly']:.2f}
- Total Mensal: ${tco_analysis['breakdown']['aws']['total_monthly']:.2f}

Google Cloud:
- Computação: ${tco_analysis['breakdown']['gcp']['compute_monthly']:.2f}
- Armazenamento: ${tco_analysis['breakdown']['gcp']['storage_monthly']:.2f}
- Serviços Adicionais: ${tco_analysis['breakdown']['gcp']['additional_monthly']:.2f}
- Custos Operacionais: ${tco_analysis['breakdown']['gcp']['operational_monthly']:.2f}
- Total Mensal: ${tco_analysis['breakdown']['gcp']['total_monthly']:.2f}

🏆 RECOMENDAÇÃO: {winner_name}

💡 Insights:
- Economia anual: ${tco_analysis['savings'] / (time_horizon_months/12):,.2f}
- Economia mensal: ${tco_analysis['savings'] / time_horizon_months:,.2f}
- ROI da migração: {tco_analysis['savings_percentage']:.1f}%

📈 Projeções:
- 1 ano: ${winner_name} economiza ${tco_analysis['savings'] / time_horizon_months * 12:,.2f}
- 3 anos: ${winner_name} economiza ${tco_analysis['savings']:,.2f}
- 5 anos: ${winner_name} economiza ${tco_analysis['savings'] / time_horizon_months * 60:,.2f}

⚠️ Considerações:
- Custos operacionais incluem gerenciamento, monitoramento e suporte
- GCP tem custos operacionais ligeiramente menores devido à melhor automação
- Preços podem variar com descontos por volume e contratos empresariais
"""
        
        return result
        
    except json.JSONDecodeError:
        return "Erro: Dados JSON inválidos fornecidos"
    except Exception as e:
        logger.error(f"Erro no cálculo de TCO: {e}")
        return f"Erro no cálculo de TCO: {str(e)}"

@mcp.tool()
async def generate_migration_recommendation(current_provider: str, target_provider: str,
                                          workload_description: str, budget_constraints: str = "moderate") -> str:
    """
    Gerar recomendação de migração entre provedores de nuvem.
    
    Args:
        current_provider: Provedor atual (aws ou gcp)
        target_provider: Provedor alvo (aws ou gcp)
        workload_description: Descrição do workload atual
        budget_constraints: Restrições orçamentárias (tight, moderate, flexible)
    
    Returns:
        Recomendação detalhada de migração
    """
    try:
        current_name = "AWS" if current_provider.lower() == 'aws' else "Google Cloud"
        target_name = "AWS" if target_provider.lower() == 'aws' else "Google Cloud"
        
        # Análise de complexidade baseada na descrição do workload
        complexity_score = len(workload_description.split()) / 10  # Simplificado
        complexity_level = "Baixa" if complexity_score < 2 else "Média" if complexity_score < 5 else "Alta"
        
        # Estimativa de tempo baseada na complexidade
        if complexity_level == "Baixa":
            migration_time = "2-4 semanas"
            effort_level = "Baixo"
        elif complexity_level == "Média":
            migration_time = "1-3 meses"
            effort_level = "Médio"
        else:
            migration_time = "3-6 meses"
            effort_level = "Alto"
        
        # Custos estimados de migração
        budget_multipliers = {"tight": 0.7, "moderate": 1.0, "flexible": 1.3}
        base_cost = 5000 if complexity_level == "Baixa" else 15000 if complexity_level == "Média" else 35000
        estimated_cost = base_cost * budget_multipliers.get(budget_constraints, 1.0)
        
        result = f"""
🚀 Recomendação de Migração de Nuvem

📋 Resumo da Migração:
- De: {current_name}
- Para: {target_name}
- Workload: {workload_description}
- Complexidade: {complexity_level}

⏱️ Estimativas:
- Tempo de migração: {migration_time}
- Nível de esforço: {effort_level}
- Custo estimado: ${estimated_cost:,.2f}
- Restrição orçamentária: {budget_constraints.title()}

📊 Fases da Migração:

1. 📋 Planejamento e Avaliação (10-15% do tempo)
   - Auditoria da infraestrutura atual
   - Mapeamento de dependências
   - Definição da arquitetura alvo

2. 🔧 Preparação e Setup (20-25% do tempo)
   - Configuração do ambiente {target_name}
   - Setup de ferramentas de migração
   - Testes de conectividade

3. 📦 Migração de Dados (30-40% do tempo)
   - Migração de bancos de dados
   - Transferência de arquivos
   - Sincronização de dados

4. 🔄 Migração de Aplicações (25-30% do tempo)
   - Refatoração de código (se necessário)
   - Configuração de serviços
   - Testes de funcionalidade

5. ✅ Validação e Go-Live (10-15% do tempo)
   - Testes de performance
   - Validação de segurança
   - Cutover final

💡 Recomendações Específicas para {target_name}:
"""
        
        if target_provider.lower() == 'aws':
            result += """
- Use AWS Migration Hub para centralizar o processo
- Considere AWS Database Migration Service para BDs
- Aproveite AWS Well-Architected Framework
- Implemente AWS CloudFormation para IaC
"""
        else:
            result += """
- Use Google Cloud Migration Center
- Aproveite Database Migration Service do GCP
- Implemente Deployment Manager para IaC
- Considere Anthos para workloads híbridos
"""
        
        result += f"""
⚠️ Riscos e Mitigações:

Riscos Principais:
- Downtime durante migração
- Perda de dados
- Problemas de performance
- Custos inesperados

Mitigações:
- Migração em fases com rollback
- Backup completo antes da migração
- Testes extensivos em ambiente de staging
- Monitoramento contínuo de custos

💰 Análise de ROI:
- Payback estimado: 6-12 meses
- Economia anual esperada: 15-30%
- Benefícios adicionais: Melhor performance, escalabilidade

📞 Próximos Passos:
1. Realizar assessment detalhado da infraestrutura
2. Criar plano de migração detalhado
3. Configurar ambiente de teste
4. Executar migração piloto
5. Implementar migração completa

🎯 Fatores de Sucesso:
- Envolvimento da equipe técnica
- Comunicação clara com stakeholders
- Testes rigorosos em cada fase
- Monitoramento contínuo pós-migração
"""
        
        return result
        
    except Exception as e:
        logger.error(f"Erro na recomendação de migração: {e}")
        return f"Erro na recomendação de migração: {str(e)}"

if __name__ == "__main__":
    # Executar servidor MCP
    mcp.run(transport='stdio')

