import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'cloud-cost-agent-secret-key-2025'

# Habilitar CORS
CORS(app)

# Rotas da API do Cloud Cost Agent (versão demo)
@app.route('/api/health', methods=['GET'])
def health_check():
    """Verificação de saúde da API"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Cloud Cost Analysis API - Demo Version',
        'version': '1.0.0'
    })

@app.route('/api/analyze/compute', methods=['POST'])
def analyze_compute_costs():
    """Analisar custos de computação (versão demo)"""
    try:
        # Validar dados de entrada
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados JSON requeridos'}), 400
        
        # Simular análise
        import time
        time.sleep(2)  # Simular processamento
        
        # Resultado simulado
        result = {
            'analysis_type': 'compute_costs',
            'requirements': data,
            'result': {
                'recommendation': 'AWS' if hash(str(data)) % 2 == 0 else 'GCP',
                'aws_cost': 156.80,
                'gcp_cost': 204.30,
                'savings': 23.5,
                'confidence': 87,
                'reasoning': 'Baseado na análise de custos, performance e escalabilidade'
            },
            'timestamp': datetime.now().isoformat(),
            'demo_mode': True
        }
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Erro na análise de computação: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/analyze/storage', methods=['POST'])
def analyze_storage_costs():
    """Analisar custos de armazenamento (versão demo)"""
    try:
        # Validar dados de entrada
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados JSON requeridos'}), 400
        
        # Simular análise
        import time
        time.sleep(1.5)  # Simular processamento
        
        # Resultado simulado
        result = {
            'analysis_type': 'storage_costs',
            'requirements': data,
            'result': {
                'recommendation': 'GCP' if hash(str(data)) % 3 == 0 else 'AWS',
                'aws_cost_per_gb': 0.023,
                'gcp_cost_per_gb': 0.020,
                'savings': 13.0,
                'confidence': 92,
                'reasoning': 'GCP oferece melhor custo-benefício para armazenamento'
            },
            'timestamp': datetime.now().isoformat(),
            'demo_mode': True
        }
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Erro na análise de armazenamento: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/analyze/comprehensive', methods=['POST'])
def comprehensive_analysis():
    """Análise abrangente de custos (versão demo)"""
    try:
        # Validar dados de entrada
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados JSON requeridos'}), 400
        
        # Simular análise mais longa
        import time
        time.sleep(3)  # Simular processamento
        
        # Resultado simulado
        result = {
            'analysis_type': 'comprehensive',
            'requirements': data,
            'result': {
                'recommendation': 'AWS',
                'total_monthly_cost_aws': 245.60,
                'total_monthly_cost_gcp': 298.40,
                'monthly_savings': 52.80,
                'annual_savings': 633.60,
                'tco_3_years': 1900.80,
                'confidence': 89,
                'breakdown': {
                    'compute': {'aws': 156.80, 'gcp': 204.30},
                    'storage': {'aws': 23.00, 'gcp': 20.00},
                    'network': {'aws': 45.80, 'gcp': 54.10},
                    'additional': {'aws': 20.00, 'gcp': 20.00}
                },
                'reasoning': 'AWS oferece melhor custo-benefício geral considerando todos os fatores'
            },
            'timestamp': datetime.now().isoformat(),
            'demo_mode': True
        }
        
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
            },
            {
                'id': '3',
                'type': 'storage',
                'timestamp': '2025-01-13T09:15:00Z',
                'status': 'completed',
                'recommendation': 'GCP',
                'savings_potential': 13.0
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

# Servir frontend React
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    logger.info("🚀 Iniciando Cloud Cost Analysis API (Demo Version)...")
    logger.info(f"📁 Static folder: {app.static_folder}")
    logger.info("🎯 Modo Demo: Análises simuladas para demonstração")
    
    app.run(host='0.0.0.0', port=5000, debug=False)

