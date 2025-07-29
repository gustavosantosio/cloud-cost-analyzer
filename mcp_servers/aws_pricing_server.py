#!/usr/bin/env python3
"""
AWS Pricing MCP Server

Este servidor MCP fornece ferramentas para análise de custos e performance da AWS.
Conecta-se às APIs da AWS para obter informações de preços, custos e métricas de performance.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

import boto3
import httpx
from mcp.server.fastmcp import FastMCP
from botocore.exceptions import ClientError, NoCredentialsError

# Configurar logging para stderr (não stdout para MCP)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Inicializar servidor MCP
mcp = FastMCP("aws-pricing")

# Constantes
AWS_REGIONS = [
    'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
    'eu-west-1', 'eu-west-2', 'eu-central-1', 'ap-southeast-1',
    'ap-southeast-2', 'ap-northeast-1', 'sa-east-1'
]

class AWSPricingClient:
    """Cliente para interagir com APIs de preços da AWS"""
    
    def __init__(self):
        try:
            # Inicializar clientes AWS
            self.pricing_client = boto3.client('pricing', region_name='us-east-1')
            self.ce_client = boto3.client('ce', region_name='us-east-1')
            self.ec2_client = boto3.client('ec2', region_name='us-east-1')
            logger.info("Clientes AWS inicializados com sucesso")
        except NoCredentialsError:
            logger.warning("Credenciais AWS não encontradas. Usando dados simulados.")
            self.pricing_client = None
            self.ce_client = None
            self.ec2_client = None
    
    async def get_ec2_pricing(self, instance_type: str, region: str) -> Dict[str, Any]:
        """Obter preços de instâncias EC2"""
        if not self.pricing_client:
            return self._get_mock_ec2_pricing(instance_type, region)
        
        try:
            response = self.pricing_client.get_products(
                ServiceCode='AmazonEC2',
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                    {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': self._get_location_name(region)},
                    {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
                    {'Type': 'TERM_MATCH', 'Field': 'operating-system', 'Value': 'Linux'}
                ]
            )
            
            if response['PriceList']:
                price_data = json.loads(response['PriceList'][0])
                return self._parse_ec2_pricing(price_data, instance_type, region)
            else:
                return self._get_mock_ec2_pricing(instance_type, region)
                
        except Exception as e:
            logger.error(f"Erro ao obter preços EC2: {e}")
            return self._get_mock_ec2_pricing(instance_type, region)
    
    async def get_storage_pricing(self, storage_type: str, region: str) -> Dict[str, Any]:
        """Obter preços de armazenamento"""
        if not self.pricing_client:
            return self._get_mock_storage_pricing(storage_type, region)
        
        try:
            service_code = 'AmazonS3' if storage_type.startswith('s3') else 'AmazonEBS'
            
            response = self.pricing_client.get_products(
                ServiceCode=service_code,
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': self._get_location_name(region)},
                    {'Type': 'TERM_MATCH', 'Field': 'storageClass', 'Value': storage_type.upper()}
                ] if service_code == 'AmazonS3' else [
                    {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': self._get_location_name(region)},
                    {'Type': 'TERM_MATCH', 'Field': 'volumeType', 'Value': storage_type}
                ]
            )
            
            if response['PriceList']:
                price_data = json.loads(response['PriceList'][0])
                return self._parse_storage_pricing(price_data, storage_type, region)
            else:
                return self._get_mock_storage_pricing(storage_type, region)
                
        except Exception as e:
            logger.error(f"Erro ao obter preços de armazenamento: {e}")
            return self._get_mock_storage_pricing(storage_type, region)
    
    async def get_cost_and_usage(self, start_date: str, end_date: str, granularity: str = 'MONTHLY') -> Dict[str, Any]:
        """Obter dados de custo e uso"""
        if not self.ce_client:
            return self._get_mock_cost_data(start_date, end_date)
        
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity=granularity,
                Metrics=['BlendedCost', 'UsageQuantity'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )
            
            return self._parse_cost_data(response)
            
        except Exception as e:
            logger.error(f"Erro ao obter dados de custo: {e}")
            return self._get_mock_cost_data(start_date, end_date)
    
    def _get_location_name(self, region: str) -> str:
        """Mapear código da região para nome da localização"""
        region_mapping = {
            'us-east-1': 'US East (N. Virginia)',
            'us-east-2': 'US East (Ohio)',
            'us-west-1': 'US West (N. California)',
            'us-west-2': 'US West (Oregon)',
            'eu-west-1': 'Europe (Ireland)',
            'eu-west-2': 'Europe (London)',
            'eu-central-1': 'Europe (Frankfurt)',
            'ap-southeast-1': 'Asia Pacific (Singapore)',
            'ap-southeast-2': 'Asia Pacific (Sydney)',
            'ap-northeast-1': 'Asia Pacific (Tokyo)',
            'sa-east-1': 'South America (São Paulo)'
        }
        return region_mapping.get(region, 'US East (N. Virginia)')
    
    def _parse_ec2_pricing(self, price_data: Dict, instance_type: str, region: str) -> Dict[str, Any]:
        """Parsear dados de preços EC2"""
        try:
            terms = price_data.get('terms', {})
            on_demand = terms.get('OnDemand', {})
            
            if on_demand:
                term_key = list(on_demand.keys())[0]
                price_dimensions = on_demand[term_key]['priceDimensions']
                price_key = list(price_dimensions.keys())[0]
                price_per_hour = float(price_dimensions[price_key]['pricePerUnit']['USD'])
                
                return {
                    'instance_type': instance_type,
                    'region': region,
                    'price_per_hour': price_per_hour,
                    'price_per_month': price_per_hour * 24 * 30,
                    'currency': 'USD',
                    'pricing_model': 'On-Demand'
                }
        except Exception as e:
            logger.error(f"Erro ao parsear preços EC2: {e}")
        
        return self._get_mock_ec2_pricing(instance_type, region)
    
    def _parse_storage_pricing(self, price_data: Dict, storage_type: str, region: str) -> Dict[str, Any]:
        """Parsear dados de preços de armazenamento"""
        try:
            terms = price_data.get('terms', {})
            on_demand = terms.get('OnDemand', {})
            
            if on_demand:
                term_key = list(on_demand.keys())[0]
                price_dimensions = on_demand[term_key]['priceDimensions']
                price_key = list(price_dimensions.keys())[0]
                price_per_gb = float(price_dimensions[price_key]['pricePerUnit']['USD'])
                
                return {
                    'storage_type': storage_type,
                    'region': region,
                    'price_per_gb_month': price_per_gb,
                    'currency': 'USD'
                }
        except Exception as e:
            logger.error(f"Erro ao parsear preços de armazenamento: {e}")
        
        return self._get_mock_storage_pricing(storage_type, region)
    
    def _parse_cost_data(self, response: Dict) -> Dict[str, Any]:
        """Parsear dados de custo e uso"""
        results = []
        
        for result in response.get('ResultsByTime', []):
            time_period = result['TimePeriod']
            groups = result.get('Groups', [])
            
            for group in groups:
                service = group['Keys'][0]
                metrics = group['Metrics']
                
                results.append({
                    'time_period': time_period,
                    'service': service,
                    'blended_cost': float(metrics.get('BlendedCost', {}).get('Amount', 0)),
                    'usage_quantity': float(metrics.get('UsageQuantity', {}).get('Amount', 0)),
                    'currency': metrics.get('BlendedCost', {}).get('Unit', 'USD')
                })
        
        return {'cost_data': results}
    
    def _get_mock_ec2_pricing(self, instance_type: str, region: str) -> Dict[str, Any]:
        """Dados simulados de preços EC2"""
        mock_prices = {
            't3.micro': 0.0104,
            't3.small': 0.0208,
            't3.medium': 0.0416,
            't3.large': 0.0832,
            'm5.large': 0.096,
            'm5.xlarge': 0.192,
            'c5.large': 0.085,
            'c5.xlarge': 0.17
        }
        
        base_price = mock_prices.get(instance_type, 0.1)
        # Ajustar preço por região (simulado)
        region_multiplier = 1.2 if region.startswith('eu-') else 1.0
        price_per_hour = base_price * region_multiplier
        
        return {
            'instance_type': instance_type,
            'region': region,
            'price_per_hour': price_per_hour,
            'price_per_month': price_per_hour * 24 * 30,
            'currency': 'USD',
            'pricing_model': 'On-Demand',
            'note': 'Dados simulados - configure credenciais AWS para dados reais'
        }
    
    def _get_mock_storage_pricing(self, storage_type: str, region: str) -> Dict[str, Any]:
        """Dados simulados de preços de armazenamento"""
        mock_prices = {
            's3_standard': 0.023,
            's3_ia': 0.0125,
            's3_glacier': 0.004,
            'gp2': 0.10,
            'gp3': 0.08,
            'io1': 0.125
        }
        
        base_price = mock_prices.get(storage_type, 0.1)
        region_multiplier = 1.1 if region.startswith('eu-') else 1.0
        price_per_gb = base_price * region_multiplier
        
        return {
            'storage_type': storage_type,
            'region': region,
            'price_per_gb_month': price_per_gb,
            'currency': 'USD',
            'note': 'Dados simulados - configure credenciais AWS para dados reais'
        }
    
    def _get_mock_cost_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Dados simulados de custo"""
        return {
            'cost_data': [
                {
                    'time_period': {'Start': start_date, 'End': end_date},
                    'service': 'Amazon Elastic Compute Cloud - Compute',
                    'blended_cost': 150.75,
                    'usage_quantity': 720.0,
                    'currency': 'USD'
                },
                {
                    'time_period': {'Start': start_date, 'End': end_date},
                    'service': 'Amazon Simple Storage Service',
                    'blended_cost': 25.30,
                    'usage_quantity': 1000.0,
                    'currency': 'USD'
                }
            ],
            'note': 'Dados simulados - configure credenciais AWS para dados reais'
        }

# Instanciar cliente AWS
aws_client = AWSPricingClient()

@mcp.tool()
async def get_aws_ec2_pricing(instance_type: str, region: str = "us-east-1") -> str:
    """
    Obter preços de instâncias EC2 da AWS.
    
    Args:
        instance_type: Tipo da instância EC2 (ex: t3.micro, m5.large, c5.xlarge)
        region: Região da AWS (padrão: us-east-1)
    
    Returns:
        Informações detalhadas de preços da instância EC2
    """
    try:
        if region not in AWS_REGIONS:
            return f"Região '{region}' não suportada. Regiões disponíveis: {', '.join(AWS_REGIONS)}"
        
        pricing_data = await aws_client.get_ec2_pricing(instance_type, region)
        
        result = f"""
Preços AWS EC2 - {instance_type} em {region}:

💰 Preço por hora: ${pricing_data['price_per_hour']:.4f}
📅 Preço mensal estimado: ${pricing_data['price_per_month']:.2f}
🏷️ Modelo de preços: {pricing_data['pricing_model']}
💱 Moeda: {pricing_data['currency']}

Especificações da instância:
- Tipo: {pricing_data['instance_type']}
- Região: {pricing_data['region']}
"""
        
        if 'note' in pricing_data:
            result += f"\n⚠️ Nota: {pricing_data['note']}"
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao obter preços EC2: {e}")
        return f"Erro ao obter preços EC2: {str(e)}"

@mcp.tool()
async def get_aws_storage_pricing(storage_type: str, region: str = "us-east-1") -> str:
    """
    Obter preços de armazenamento da AWS.
    
    Args:
        storage_type: Tipo de armazenamento (s3_standard, s3_ia, s3_glacier, gp2, gp3, io1)
        region: Região da AWS (padrão: us-east-1)
    
    Returns:
        Informações detalhadas de preços de armazenamento
    """
    try:
        if region not in AWS_REGIONS:
            return f"Região '{region}' não suportada. Regiões disponíveis: {', '.join(AWS_REGIONS)}"
        
        pricing_data = await aws_client.get_storage_pricing(storage_type, region)
        
        service_name = "Amazon S3" if storage_type.startswith('s3') else "Amazon EBS"
        
        result = f"""
Preços AWS {service_name} - {storage_type} em {region}:

💾 Preço por GB/mês: ${pricing_data['price_per_gb_month']:.4f}
💱 Moeda: {pricing_data['currency']}

Especificações do armazenamento:
- Tipo: {pricing_data['storage_type']}
- Região: {pricing_data['region']}
- Serviço: {service_name}

Estimativas de custo:
- 100 GB: ${pricing_data['price_per_gb_month'] * 100:.2f}/mês
- 1 TB: ${pricing_data['price_per_gb_month'] * 1024:.2f}/mês
- 10 TB: ${pricing_data['price_per_gb_month'] * 10240:.2f}/mês
"""
        
        if 'note' in pricing_data:
            result += f"\n⚠️ Nota: {pricing_data['note']}"
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao obter preços de armazenamento: {e}")
        return f"Erro ao obter preços de armazenamento: {str(e)}"

@mcp.tool()
async def get_aws_cost_analysis(months_back: int = 3) -> str:
    """
    Analisar custos históricos da AWS.
    
    Args:
        months_back: Número de meses para análise (padrão: 3)
    
    Returns:
        Análise detalhada dos custos históricos
    """
    try:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=months_back * 30)).strftime('%Y-%m-%d')
        
        cost_data = await aws_client.get_cost_and_usage(start_date, end_date)
        
        result = f"""
Análise de Custos AWS ({start_date} a {end_date}):

📊 Resumo por Serviço:
"""
        
        total_cost = 0
        for item in cost_data['cost_data']:
            service = item['service']
            cost = item['blended_cost']
            total_cost += cost
            
            result += f"""
🔹 {service}:
   💰 Custo: ${cost:.2f}
   📈 Uso: {item['usage_quantity']:.1f} unidades
"""
        
        result += f"""
💵 Custo Total: ${total_cost:.2f}
📅 Período: {months_back} meses
💱 Moeda: USD
"""
        
        if 'note' in cost_data:
            result += f"\n⚠️ Nota: {cost_data['note']}"
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao analisar custos: {e}")
        return f"Erro ao analisar custos: {str(e)}"

@mcp.tool()
async def compare_aws_instances(instance_types: str, region: str = "us-east-1") -> str:
    """
    Comparar preços de múltiplas instâncias EC2.
    
    Args:
        instance_types: Lista de tipos de instância separados por vírgula (ex: "t3.micro,t3.small,m5.large")
        region: Região da AWS (padrão: us-east-1)
    
    Returns:
        Comparação detalhada de preços entre instâncias
    """
    try:
        if region not in AWS_REGIONS:
            return f"Região '{region}' não suportada. Regiões disponíveis: {', '.join(AWS_REGIONS)}"
        
        instance_list = [inst.strip() for inst in instance_types.split(',')]
        
        result = f"""
Comparação de Instâncias EC2 AWS em {region}:

{'Tipo':<15} {'$/hora':<10} {'$/mês':<12} {'Economia vs Maior':<20}
{'-' * 60}
"""
        
        pricing_data = []
        for instance_type in instance_list:
            data = await aws_client.get_ec2_pricing(instance_type, region)
            pricing_data.append(data)
        
        # Ordenar por preço
        pricing_data.sort(key=lambda x: x['price_per_hour'])
        
        max_price = max(data['price_per_hour'] for data in pricing_data)
        
        for data in pricing_data:
            savings = ((max_price - data['price_per_hour']) / max_price) * 100
            result += f"{data['instance_type']:<15} ${data['price_per_hour']:<9.4f} ${data['price_per_month']:<11.2f} {savings:<19.1f}%\n"
        
        result += f"""
{'-' * 60}

💡 Recomendações:
- Mais econômica: {pricing_data[0]['instance_type']} (${pricing_data[0]['price_per_hour']:.4f}/hora)
- Mais cara: {pricing_data[-1]['instance_type']} (${pricing_data[-1]['price_per_hour']:.4f}/hora)
- Economia máxima: {((max_price - pricing_data[0]['price_per_hour']) / max_price) * 100:.1f}%
"""
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao comparar instâncias: {e}")
        return f"Erro ao comparar instâncias: {str(e)}"

@mcp.tool()
async def get_aws_regions_info() -> str:
    """
    Obter informações sobre regiões AWS disponíveis.
    
    Returns:
        Lista de regiões AWS suportadas com informações básicas
    """
    result = """
Regiões AWS Disponíveis:

🌍 América do Norte:
- us-east-1: US East (N. Virginia) - Região principal
- us-east-2: US East (Ohio)
- us-west-1: US West (N. California)
- us-west-2: US West (Oregon)

🌍 Europa:
- eu-west-1: Europe (Ireland)
- eu-west-2: Europe (London)
- eu-central-1: Europe (Frankfurt)

🌍 Ásia-Pacífico:
- ap-southeast-1: Asia Pacific (Singapore)
- ap-southeast-2: Asia Pacific (Sydney)
- ap-northeast-1: Asia Pacific (Tokyo)

🌍 América do Sul:
- sa-east-1: South America (São Paulo)

💡 Dicas:
- us-east-1 geralmente tem os menores preços
- Escolha a região mais próxima dos seus usuários
- Algumas regiões podem ter preços ligeiramente diferentes
"""
    
    return result

if __name__ == "__main__":
    # Executar servidor MCP
    mcp.run(transport='stdio')

