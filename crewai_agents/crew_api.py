#!/usr/bin/env python3
"""
Cloud Cost Analysis API

API Flask para expor as funcionalidades do sistema CrewAI de análise de custos de nuvem.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any

from flask import Flask, request, jsonify
from flask_cors import CORS

from cloud_cost_crew import CloudCostAnalysisCrew

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar aplicação Flask
app = Flask(__name__)
CORS(app)  # Permitir CORS para todas as rotas

# Instanciar crew
crew = CloudCostAnalysisCrew()

@app.route('/health', methods=['GET'])
def health_check():
    """Verificação de saúde da API"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Cloud Cost Analysis API'
    })

@app.route('/api/analyze/compute', methods=['POST'])
def analyze_compute_costs():
    """Analisar custos de computação"""
    try:
        # Validar dados de entrada
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados JSON requeridos'}), 400
        
        # Parâmetros padrão
        requirements = {
            'aws_instance_type': data.get('aws_instance_type', 't3.medium'),
            'gcp_machine_type': data.get('gcp_machine_type', 'e2-medium'),
            'aws_region': data.get('aws_region', 'us-east-1'),
            'gcp_region': data.get('gcp_region', 'us-central1'),
            'workload_type': data.get('workload_type', 'general')
        }
        
        logger.info(f"Iniciando análise de computação com requisitos: {requirements}")
        
        # Executar análise
        result = crew.analyze_compute_costs(requirements)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Erro na análise de computação: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/analyze/storage', methods=['POST'])
def analyze_storage_costs():
    """Analisar custos de armazenamento"""
    try:
        # Validar dados de entrada
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados JSON requeridos'}), 400
        
        # Parâmetros padrão
        requirements = {
            'aws_storage_type': data.get('aws_storage_type', 's3_standard'),
            'gcp_storage_type': data.get('gcp_storage_type', 'standard'),
            'aws_region': data.get('aws_region', 'us-east-1'),
            'gcp_region': data.get('gcp_region', 'us-central1'),
            'storage_size_gb': data.get('storage_size_gb', 1000)
        }
        
        logger.info(f"Iniciando análise de armazenamento com requisitos: {requirements}")
        
        # Executar análise
        result = crew.analyze_storage_costs(requirements)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Erro na análise de armazenamento: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/analyze/comprehensive', methods=['POST'])
def comprehensive_analysis():
    """Análise abrangente de custos"""
    try:
        # Validar dados de entrada
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados JSON requeridos'}), 400
        
        # Parâmetros padrão
        requirements = {
            'aws_instance_type': data.get('aws_instance_type', 't3.medium'),
            'gcp_machine_type': data.get('gcp_machine_type', 'e2-medium'),
            'aws_region': data.get('aws_region', 'us-east-1'),
            'gcp_region': data.get('gcp_region', 'us-central1'),
            'workload_type': data.get('workload_type', 'general'),
            'aws_storage_type': data.get('aws_storage_type', 's3_standard'),
            'gcp_storage_type': data.get('gcp_storage_type', 'standard'),
            'storage_size_gb': data.get('storage_size_gb', 1000),
            'monthly_budget': data.get('monthly_budget', 500),
            'performance_priority': data.get('performance_priority', 'balanced'),
            'time_horizon_months': data.get('time_horizon_months', 36)
        }
        
        logger.info(f"Iniciando análise abrangente com requisitos: {requirements}")
        
        # Executar análise
        result = crew.comprehensive_analysis(requirements)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Erro na análise abrangente: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/providers/info', methods=['GET'])
def get_providers_info():
    """Obter informações sobre provedores suportados"""
    return jsonify({
        'providers': {
            'aws': {
                'name': 'Amazon Web Services',
                'regions': [
                    'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
                    'eu-west-1', 'eu-west-2', 'eu-central-1',
                    'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1',
                    'sa-east-1'
                ],
                'instance_types': [
                    't3.micro', 't3.small', 't3.medium', 't3.large',
                    'm5.large', 'm5.xlarge', 'm5.2xlarge',
                    'c5.large', 'c5.xlarge', 'c5.2xlarge'
                ],
                'storage_types': [
                    's3_standard', 's3_ia', 's3_glacier',
                    'gp2', 'gp3', 'io1'
                ]
            },
            'gcp': {
                'name': 'Google Cloud Platform',
                'regions': [
                    'us-central1', 'us-east1', 'us-east4', 'us-west1', 'us-west2',
                    'europe-west1', 'europe-west2', 'europe-west3', 'europe-west4',
                    'asia-east1', 'asia-southeast1', 'asia-northeast1',
                    'southamerica-east1'
                ],
                'machine_types': [
                    'e2-micro', 'e2-small', 'e2-medium', 'e2-standard-2', 'e2-standard-4',
                    'n1-standard-1', 'n1-standard-2', 'n1-standard-4',
                    'n2-standard-2', 'n2-standard-4',
                    'c2-standard-4', 'c2-standard-8'
                ],
                'storage_types': [
                    'standard', 'nearline', 'coldline', 'archive',
                    'regional', 'multi-regional'
                ]
            }
        },
        'workload_types': [
            'general', 'compute_intensive', 'data_intensive',
            'web_application', 'batch_processing', 'machine_learning'
        ],
        'performance_priorities': [
            'cost_optimized', 'balanced', 'performance_optimized'
        ]
    })

@app.route('/api/analysis/history', methods=['GET'])
def get_analysis_history():
    """Obter histórico de análises (simulado)"""
    # Em uma implementação real, isso viria de um banco de dados
    return jsonify({
        'analyses': [
            {
                'id': '1',
                'type': 'comprehensive',
                'timestamp': '2025-01-15T10:30:00Z',
                'status': 'completed',
                'recommendation': 'AWS',
                'savings_potential': 25.5
            },
            {
                'id': '2',
                'type': 'compute',
                'timestamp': '2025-01-14T15:45:00Z',
                'status': 'completed',
                'recommendation': 'GCP',
                'savings_potential': 18.2
            }
        ]
    })

@app.route('/api/templates', methods=['GET'])
def get_analysis_templates():
    """Obter templates de análise pré-configurados"""
    return jsonify({
        'templates': {
            'startup_web_app': {
                'name': 'Startup Web Application',
                'description': 'Configuração típica para aplicação web de startup',
                'aws_instance_type': 't3.small',
                'gcp_machine_type': 'e2-small',
                'aws_storage_type': 's3_standard',
                'gcp_storage_type': 'standard',
                'storage_size_gb': 100,
                'workload_type': 'web_application',
                'monthly_budget': 200
            },
            'enterprise_data_processing': {
                'name': 'Enterprise Data Processing',
                'description': 'Configuração para processamento de dados empresariais',
                'aws_instance_type': 'c5.2xlarge',
                'gcp_machine_type': 'c2-standard-8',
                'aws_storage_type': 's3_standard',
                'gcp_storage_type': 'standard',
                'storage_size_gb': 10000,
                'workload_type': 'data_intensive',
                'monthly_budget': 2000
            },
            'ml_training': {
                'name': 'Machine Learning Training',
                'description': 'Configuração para treinamento de modelos ML',
                'aws_instance_type': 'm5.xlarge',
                'gcp_machine_type': 'n2-standard-4',
                'aws_storage_type': 's3_standard',
                'gcp_storage_type': 'standard',
                'storage_size_gb': 5000,
                'workload_type': 'machine_learning',
                'monthly_budget': 1000
            }
        }
    })

@app.errorhandler(404)
def not_found(error):
    """Handler para rotas não encontradas"""
    return jsonify({
        'error': 'Endpoint não encontrado',
        'message': 'Verifique a documentação da API para endpoints disponíveis'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handler para erros internos"""
    return jsonify({
        'error': 'Erro interno do servidor',
        'message': 'Ocorreu um erro inesperado. Tente novamente mais tarde.'
    }), 500

if __name__ == '__main__':
    # Configurar porta e host
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Iniciando Cloud Cost Analysis API em {host}:{port}")
    
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )

