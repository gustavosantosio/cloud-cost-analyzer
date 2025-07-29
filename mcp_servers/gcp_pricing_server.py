#!/usr/bin/env python3
"""
Google Cloud Pricing MCP Server

Este servidor MCP fornece ferramentas para análise de custos e performance do Google Cloud.
Conecta-se às APIs do Google Cloud para obter informações de preços, custos e métricas de performance.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

import httpx
from mcp.server.fastmcp import FastMCP
from google.cloud import billing_v1
from google.cloud import resourcemanager_v1
from googleapiclient.discovery import build
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError

# Configurar logging para stderr (não stdout para MCP)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Inicializar servidor MCP
mcp = FastMCP("gcp-pricing")

# Constantes
GCP_REGIONS = [
    'us-central1', 'us-east1', 'us-east4', 'us-west1', 'us-west2', 'us-west3', 'us-west4',
    'europe-west1', 'europe-west2', 'europe-west3', 'europe-west4', 'europe-west6',
    'asia-east1', 'asia-east2', 'asia-northeast1', 'asia-southeast1', 'asia-south1',
    'southamerica-east1'
]

class GCPPricingClient:
    """Cliente para interagir com APIs de preços do Google Cloud"""
    
    def __init__(self):
        try:
            # Tentar inicializar clientes Google Cloud
            self.credentials, self.project_id = default()
            self.billing_client = billing_v1.CloudCatalogClient(credentials=self.credentials)
            self.resource_client = resourcemanager_v1.ProjectsClient(credentials=self.credentials)
            logger.info("Clientes Google Cloud inicializados com sucesso")
            self.has_credentials = True
        except DefaultCredentialsError:
            logger.warning("Credenciais Google Cloud não encontradas. Usando dados simulados.")
            self.billing_client = None
            self.resource_client = None
            self.has_credentials = False
    
    async def get_compute_pricing(self, machine_type: str, region: str) -> Dict[str, Any]:
        """Obter preços de instâncias Compute Engine"""
        if not self.has_credentials:
            return self._get_mock_compute_pricing(machine_type, region)
        
        try:
            # Listar serviços para encontrar Compute Engine
            services = self.billing_client.list_services()
            compute_service = None
            
            for service in services:
                if 'Compute Engine' in service.display_name:
                    compute_service = service
                    break
            
            if not compute_service:
                return self._get_mock_compute_pricing(machine_type, region)
            
            # Listar SKUs do Compute Engine
            skus = self.billing_client.list_skus(parent=compute_service.name)
            
            for sku in skus:
                if (machine_type.lower() in sku.description.lower() and 
                    'running' in sku.description.lower() and
                    region in sku.service_regions):
                    
                    return self._parse_compute_pricing(sku, machine_type, region)
            
            return self._get_mock_compute_pricing(machine_type, region)
            
        except Exception as e:
            logger.error(f"Erro ao obter preços Compute Engine: {e}")
            return self._get_mock_compute_pricing(machine_type, region)
    
    async def get_storage_pricing(self, storage_type: str, region: str) -> Dict[str, Any]:
        """Obter preços de armazenamento"""
        if not self.has_credentials:
            return self._get_mock_storage_pricing(storage_type, region)
        
        try:
            # Listar serviços para encontrar Cloud Storage
            services = self.billing_client.list_services()
            storage_service = None
            
            for service in services:
                if 'Cloud Storage' in service.display_name:
                    storage_service = service
                    break
            
            if not storage_service:
                return self._get_mock_storage_pricing(storage_type, region)
            
            # Listar SKUs do Cloud Storage
            skus = self.billing_client.list_skus(parent=storage_service.name)
            
            for sku in skus:
                if (storage_type.lower() in sku.description.lower() and
                    region in sku.service_regions):
                    
                    return self._parse_storage_pricing(sku, storage_type, region)
            
            return self._get_mock_storage_pricing(storage_type, region)
            
        except Exception as e:
            logger.error(f"Erro ao obter preços de armazenamento: {e}")
            return self._get_mock_storage_pricing(storage_type, region)
    
    async def get_services_list(self) -> List[Dict[str, Any]]:
        """Listar serviços disponíveis do Google Cloud"""
        if not self.has_credentials:
            return self._get_mock_services_list()
        
        try:
            services = self.billing_client.list_services()
            services_list = []
            
            for service in services:
                services_list.append({
                    'service_id': service.service_id,
                    'display_name': service.display_name,
                    'business_entity_name': service.business_entity_name
                })
            
            return services_list
            
        except Exception as e:
            logger.error(f"Erro ao listar serviços: {e}")
            return self._get_mock_services_list()
    
    def _parse_compute_pricing(self, sku, machine_type: str, region: str) -> Dict[str, Any]:
        """Parsear dados de preços do Compute Engine"""
        try:
            pricing_info = sku.pricing_info[0] if sku.pricing_info else None
            if not pricing_info:
                return self._get_mock_compute_pricing(machine_type, region)
            
            # Extrair preço por hora
            tiered_rates = pricing_info.pricing_expression.tiered_rates
            if tiered_rates:
                # Pegar o primeiro tier (geralmente o único para compute)
                rate = tiered_rates[0]
                price_per_hour = float(rate.unit_price.nanos) / 1e9 + float(rate.unit_price.units)
                
                return {
                    'machine_type': machine_type,
                    'region': region,
                    'price_per_hour': price_per_hour,
                    'price_per_month': price_per_hour * 24 * 30,
                    'currency': pricing_info.pricing_expression.currency_code,
                    'pricing_model': 'On-Demand',
                    'sku_description': sku.description
                }
        except Exception as e:
            logger.error(f"Erro ao parsear preços Compute Engine: {e}")
        
        return self._get_mock_compute_pricing(machine_type, region)
    
    def _parse_storage_pricing(self, sku, storage_type: str, region: str) -> Dict[str, Any]:
        """Parsear dados de preços de armazenamento"""
        try:
            pricing_info = sku.pricing_info[0] if sku.pricing_info else None
            if not pricing_info:
                return self._get_mock_storage_pricing(storage_type, region)
            
            # Extrair preço por GB
            tiered_rates = pricing_info.pricing_expression.tiered_rates
            if tiered_rates:
                rate = tiered_rates[0]
                price_per_gb = float(rate.unit_price.nanos) / 1e9 + float(rate.unit_price.units)
                
                return {
                    'storage_type': storage_type,
                    'region': region,
                    'price_per_gb_month': price_per_gb,
                    'currency': pricing_info.pricing_expression.currency_code,
                    'sku_description': sku.description
                }
        except Exception as e:
            logger.error(f"Erro ao parsear preços de armazenamento: {e}")
        
        return self._get_mock_storage_pricing(storage_type, region)
    
    def _get_mock_compute_pricing(self, machine_type: str, region: str) -> Dict[str, Any]:
        """Dados simulados de preços Compute Engine"""
        mock_prices = {
            'e2-micro': 0.006,
            'e2-small': 0.012,
            'e2-medium': 0.024,
            'e2-standard-2': 0.048,
            'e2-standard-4': 0.096,
            'n1-standard-1': 0.0475,
            'n1-standard-2': 0.095,
            'n1-standard-4': 0.19,
            'n2-standard-2': 0.097,
            'n2-standard-4': 0.194,
            'c2-standard-4': 0.168,
            'c2-standard-8': 0.336
        }
        
        base_price = mock_prices.get(machine_type, 0.05)
        # Ajustar preço por região (simulado)
        region_multiplier = 1.15 if region.startswith('europe-') else 1.0
        price_per_hour = base_price * region_multiplier
        
        return {
            'machine_type': machine_type,
            'region': region,
            'price_per_hour': price_per_hour,
            'price_per_month': price_per_hour * 24 * 30,
            'currency': 'USD',
            'pricing_model': 'On-Demand',
            'note': 'Dados simulados - configure credenciais GCP para dados reais'
        }
    
    def _get_mock_storage_pricing(self, storage_type: str, region: str) -> Dict[str, Any]:
        """Dados simulados de preços de armazenamento"""
        mock_prices = {
            'standard': 0.020,
            'nearline': 0.010,
            'coldline': 0.004,
            'archive': 0.0012,
            'regional': 0.020,
            'multi-regional': 0.026
        }
        
        base_price = mock_prices.get(storage_type.lower(), 0.02)
        region_multiplier = 1.1 if region.startswith('europe-') else 1.0
        price_per_gb = base_price * region_multiplier
        
        return {
            'storage_type': storage_type,
            'region': region,
            'price_per_gb_month': price_per_gb,
            'currency': 'USD',
            'note': 'Dados simulados - configure credenciais GCP para dados reais'
        }
    
    def _get_mock_services_list(self) -> List[Dict[str, Any]]:
        """Lista simulada de serviços"""
        return [
            {'service_id': '6F81-5844-456A', 'display_name': 'Compute Engine', 'business_entity_name': 'Google Cloud'},
            {'service_id': '95FF-2EF5-5EA1', 'display_name': 'Cloud Storage', 'business_entity_name': 'Google Cloud'},
            {'service_id': '9662-B51E-5089', 'display_name': 'Cloud SQL', 'business_entity_name': 'Google Cloud'},
            {'service_id': 'A1E8-BE35-7EBC', 'display_name': 'BigQuery', 'business_entity_name': 'Google Cloud'},
            {'service_id': '58CD-78B0-8F9D', 'display_name': 'Cloud Functions', 'business_entity_name': 'Google Cloud'}
        ]

# Instanciar cliente GCP
gcp_client = GCPPricingClient()

@mcp.tool()
async def get_gcp_compute_pricing(machine_type: str, region: str = "us-central1") -> str:
    """
    Obter preços de instâncias Compute Engine do Google Cloud.
    
    Args:
        machine_type: Tipo da máquina (ex: e2-micro, n1-standard-1, c2-standard-4)
        region: Região do GCP (padrão: us-central1)
    
    Returns:
        Informações detalhadas de preços da instância Compute Engine
    """
    try:
        if region not in GCP_REGIONS:
            return f"Região '{region}' não suportada. Regiões disponíveis: {', '.join(GCP_REGIONS[:10])}..."
        
        pricing_data = await gcp_client.get_compute_pricing(machine_type, region)
        
        result = f"""
Preços Google Cloud Compute Engine - {machine_type} em {region}:

💰 Preço por hora: ${pricing_data['price_per_hour']:.4f}
📅 Preço mensal estimado: ${pricing_data['price_per_month']:.2f}
🏷️ Modelo de preços: {pricing_data['pricing_model']}
💱 Moeda: {pricing_data['currency']}

Especificações da instância:
- Tipo: {pricing_data['machine_type']}
- Região: {pricing_data['region']}
"""
        
        if 'sku_description' in pricing_data:
            result += f"- Descrição: {pricing_data['sku_description']}\n"
        
        if 'note' in pricing_data:
            result += f"\n⚠️ Nota: {pricing_data['note']}"
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao obter preços Compute Engine: {e}")
        return f"Erro ao obter preços Compute Engine: {str(e)}"

@mcp.tool()
async def get_gcp_storage_pricing(storage_type: str, region: str = "us-central1") -> str:
    """
    Obter preços de armazenamento do Google Cloud.
    
    Args:
        storage_type: Tipo de armazenamento (standard, nearline, coldline, archive, regional, multi-regional)
        region: Região do GCP (padrão: us-central1)
    
    Returns:
        Informações detalhadas de preços de armazenamento
    """
    try:
        if region not in GCP_REGIONS:
            return f"Região '{region}' não suportada. Regiões disponíveis: {', '.join(GCP_REGIONS[:10])}..."
        
        pricing_data = await gcp_client.get_storage_pricing(storage_type, region)
        
        result = f"""
Preços Google Cloud Storage - {storage_type} em {region}:

💾 Preço por GB/mês: ${pricing_data['price_per_gb_month']:.4f}
💱 Moeda: {pricing_data['currency']}

Especificações do armazenamento:
- Tipo: {pricing_data['storage_type']}
- Região: {pricing_data['region']}
- Serviço: Cloud Storage

Estimativas de custo:
- 100 GB: ${pricing_data['price_per_gb_month'] * 100:.2f}/mês
- 1 TB: ${pricing_data['price_per_gb_month'] * 1024:.2f}/mês
- 10 TB: ${pricing_data['price_per_gb_month'] * 10240:.2f}/mês

Características do tipo de armazenamento:
"""
        
        # Adicionar informações sobre o tipo de armazenamento
        storage_info = {
            'standard': 'Acesso frequente, alta disponibilidade',
            'nearline': 'Acesso mensal, backup e arquivamento',
            'coldline': 'Acesso trimestral, arquivamento de longo prazo',
            'archive': 'Acesso anual, arquivamento de muito longo prazo',
            'regional': 'Armazenamento em região específica',
            'multi-regional': 'Armazenamento distribuído globalmente'
        }
        
        if storage_type.lower() in storage_info:
            result += f"- {storage_info[storage_type.lower()]}\n"
        
        if 'note' in pricing_data:
            result += f"\n⚠️ Nota: {pricing_data['note']}"
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao obter preços de armazenamento: {e}")
        return f"Erro ao obter preços de armazenamento: {str(e)}"

@mcp.tool()
async def compare_gcp_instances(machine_types: str, region: str = "us-central1") -> str:
    """
    Comparar preços de múltiplas instâncias Compute Engine.
    
    Args:
        machine_types: Lista de tipos de máquina separados por vírgula (ex: "e2-micro,e2-small,n1-standard-1")
        region: Região do GCP (padrão: us-central1)
    
    Returns:
        Comparação detalhada de preços entre instâncias
    """
    try:
        if region not in GCP_REGIONS:
            return f"Região '{region}' não suportada. Regiões disponíveis: {', '.join(GCP_REGIONS[:10])}..."
        
        machine_list = [machine.strip() for machine in machine_types.split(',')]
        
        result = f"""
Comparação de Instâncias Compute Engine GCP em {region}:

{'Tipo':<20} {'$/hora':<10} {'$/mês':<12} {'Economia vs Maior':<20}
{'-' * 65}
"""
        
        pricing_data = []
        for machine_type in machine_list:
            data = await gcp_client.get_compute_pricing(machine_type, region)
            pricing_data.append(data)
        
        # Ordenar por preço
        pricing_data.sort(key=lambda x: x['price_per_hour'])
        
        max_price = max(data['price_per_hour'] for data in pricing_data)
        
        for data in pricing_data:
            savings = ((max_price - data['price_per_hour']) / max_price) * 100
            result += f"{data['machine_type']:<20} ${data['price_per_hour']:<9.4f} ${data['price_per_month']:<11.2f} {savings:<19.1f}%\n"
        
        result += f"""
{'-' * 65}

💡 Recomendações:
- Mais econômica: {pricing_data[0]['machine_type']} (${pricing_data[0]['price_per_hour']:.4f}/hora)
- Mais cara: {pricing_data[-1]['machine_type']} (${pricing_data[-1]['price_per_hour']:.4f}/hora)
- Economia máxima: {((max_price - pricing_data[0]['price_per_hour']) / max_price) * 100:.1f}%

💡 Dicas GCP:
- Instâncias E2 são otimizadas para custo-benefício
- Instâncias N1 são de propósito geral
- Instâncias C2 são otimizadas para computação
"""
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao comparar instâncias: {e}")
        return f"Erro ao comparar instâncias: {str(e)}"

@mcp.tool()
async def get_gcp_services_list() -> str:
    """
    Listar serviços disponíveis do Google Cloud.
    
    Returns:
        Lista de serviços GCP com IDs e nomes
    """
    try:
        services = await gcp_client.get_services_list()
        
        result = """
Serviços Google Cloud Disponíveis:

🔧 Principais Serviços:
"""
        
        for service in services[:20]:  # Limitar a 20 serviços
            result += f"""
- {service['display_name']}
  ID: {service['service_id']}
  Entidade: {service['business_entity_name']}
"""
        
        result += f"""
📊 Total de serviços listados: {len(services[:20])}

💡 Principais categorias:
- Compute: Compute Engine, App Engine, Cloud Functions
- Storage: Cloud Storage, Persistent Disk
- Database: Cloud SQL, Firestore, BigQuery
- Networking: VPC, Load Balancing, CDN
- AI/ML: AI Platform, AutoML, Vision API
"""
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao listar serviços: {e}")
        return f"Erro ao listar serviços: {str(e)}"

@mcp.tool()
async def get_gcp_regions_info() -> str:
    """
    Obter informações sobre regiões GCP disponíveis.
    
    Returns:
        Lista de regiões GCP suportadas com informações básicas
    """
    result = """
Regiões Google Cloud Disponíveis:

🌍 América do Norte:
- us-central1: Iowa (Central US)
- us-east1: South Carolina (East US)
- us-east4: Northern Virginia (East US)
- us-west1: Oregon (West US)
- us-west2: Los Angeles (West US)
- us-west3: Salt Lake City (West US)
- us-west4: Las Vegas (West US)

🌍 Europa:
- europe-west1: Belgium (West Europe)
- europe-west2: London (West Europe)
- europe-west3: Frankfurt (West Europe)
- europe-west4: Netherlands (West Europe)
- europe-west6: Zurich (West Europe)

🌍 Ásia-Pacífico:
- asia-east1: Taiwan (East Asia)
- asia-east2: Hong Kong (East Asia)
- asia-northeast1: Tokyo (Northeast Asia)
- asia-southeast1: Singapore (Southeast Asia)
- asia-south1: Mumbai (South Asia)

🌍 América do Sul:
- southamerica-east1: São Paulo (South America)

💡 Dicas:
- us-central1 geralmente tem bons preços e disponibilidade
- Escolha a região mais próxima dos seus usuários
- Algumas regiões têm recursos específicos disponíveis
- Considere latência e conformidade regulatória
"""
    
    return result

@mcp.tool()
async def calculate_gcp_sustained_use_discount(machine_type: str, hours_per_month: int, region: str = "us-central1") -> str:
    """
    Calcular desconto por uso sustentado do GCP.
    
    Args:
        machine_type: Tipo da máquina (ex: n1-standard-1)
        hours_per_month: Horas de uso por mês
        region: Região do GCP (padrão: us-central1)
    
    Returns:
        Cálculo detalhado do desconto por uso sustentado
    """
    try:
        pricing_data = await gcp_client.get_compute_pricing(machine_type, region)
        base_price_per_hour = pricing_data['price_per_hour']
        
        # Calcular desconto por uso sustentado (simplificado)
        # GCP oferece descontos automáticos baseados no uso mensal
        usage_percentage = min(hours_per_month / (24 * 30), 1.0)
        
        # Desconto progressivo (simplificado)
        if usage_percentage >= 0.25:  # 25% do mês
            discount_rate = min(0.30, usage_percentage * 0.30)  # Até 30% de desconto
        else:
            discount_rate = 0
        
        original_cost = base_price_per_hour * hours_per_month
        discounted_cost = original_cost * (1 - discount_rate)
        savings = original_cost - discounted_cost
        
        result = f"""
Cálculo de Desconto por Uso Sustentado GCP:

🖥️ Instância: {machine_type} em {region}
⏰ Uso mensal: {hours_per_month} horas ({usage_percentage:.1%} do mês)

💰 Custos:
- Preço base por hora: ${base_price_per_hour:.4f}
- Custo sem desconto: ${original_cost:.2f}
- Taxa de desconto: {discount_rate:.1%}
- Custo com desconto: ${discounted_cost:.2f}
- Economia mensal: ${savings:.2f}

📊 Análise:
- Economia anual: ${savings * 12:.2f}
- Percentual de economia: {(savings/original_cost)*100:.1f}%

💡 Sobre o Desconto por Uso Sustentado:
- Aplicado automaticamente pelo GCP
- Baseado no uso mensal de cada tipo de máquina
- Não requer compromisso antecipado
- Máximo de 30% de desconto para uso contínuo
"""
        
        if usage_percentage < 0.25:
            result += "\n⚠️ Para obter descontos, considere usar a instância por mais de 25% do mês."
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao calcular desconto: {e}")
        return f"Erro ao calcular desconto: {str(e)}"

if __name__ == "__main__":
    # Executar servidor MCP
    mcp.run(transport='stdio')

