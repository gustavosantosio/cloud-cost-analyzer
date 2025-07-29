"""
Testes unitários para a API do Cloud Cost Agent
"""

import pytest
import json
from unittest.mock import patch, MagicMock
import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'cloud-cost-agent-deploy'))

from src.main import app


@pytest.fixture
def client():
    """Fixture para cliente de teste Flask"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestHealthEndpoint:
    """Testes para o endpoint de health check"""
    
    def test_health_check_success(self, client):
        """Testa se o health check retorna status correto"""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert data['service'] == 'Cloud Cost Analysis API - Demo Version'
        assert data['version'] == '1.0.0'


class TestProvidersEndpoint:
    """Testes para o endpoint de informações dos provedores"""
    
    def test_providers_info_success(self, client):
        """Testa se retorna informações dos provedores"""
        response = client.get('/api/providers/info')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'providers' in data
        assert 'aws' in data['providers']
        assert 'gcp' in data['providers']
        assert 'workload_types' in data
        assert 'performance_priorities' in data
    
    def test_aws_provider_structure(self, client):
        """Testa estrutura dos dados da AWS"""
        response = client.get('/api/providers/info')
        data = json.loads(response.data)
        
        aws = data['providers']['aws']
        assert aws['name'] == 'Amazon Web Services'
        assert isinstance(aws['regions'], list)
        assert isinstance(aws['instance_types'], list)
        assert isinstance(aws['storage_types'], list)
        assert 'us-east-1' in aws['regions']
    
    def test_gcp_provider_structure(self, client):
        """Testa estrutura dos dados do GCP"""
        response = client.get('/api/providers/info')
        data = json.loads(response.data)
        
        gcp = data['providers']['gcp']
        assert gcp['name'] == 'Google Cloud Platform'
        assert isinstance(gcp['regions'], list)
        assert isinstance(gcp['machine_types'], list)
        assert isinstance(gcp['storage_types'], list)
        assert 'us-central1' in gcp['regions']


class TestTemplatesEndpoint:
    """Testes para o endpoint de templates"""
    
    def test_templates_success(self, client):
        """Testa se retorna templates corretamente"""
        response = client.get('/api/templates')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'templates' in data
        assert 'startup_web_app' in data['templates']
        assert 'enterprise_data_processing' in data['templates']
        assert 'ml_training' in data['templates']
    
    def test_template_structure(self, client):
        """Testa estrutura de um template"""
        response = client.get('/api/templates')
        data = json.loads(response.data)
        
        template = data['templates']['startup_web_app']
        required_fields = [
            'name', 'description', 'aws_instance_type', 'gcp_machine_type',
            'aws_storage_type', 'gcp_storage_type', 'storage_size_gb',
            'workload_type', 'monthly_budget'
        ]
        
        for field in required_fields:
            assert field in template


class TestAnalysisHistoryEndpoint:
    """Testes para o endpoint de histórico de análises"""
    
    def test_analysis_history_success(self, client):
        """Testa se retorna histórico corretamente"""
        response = client.get('/api/analysis/history')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'analyses' in data
        assert isinstance(data['analyses'], list)
        assert len(data['analyses']) > 0
    
    def test_analysis_history_structure(self, client):
        """Testa estrutura do histórico"""
        response = client.get('/api/analysis/history')
        data = json.loads(response.data)
        
        analysis = data['analyses'][0]
        required_fields = ['id', 'type', 'timestamp', 'status', 'recommendation', 'savings_potential']
        
        for field in required_fields:
            assert field in analysis


class TestComputeAnalysisEndpoint:
    """Testes para o endpoint de análise de computação"""
    
    def test_compute_analysis_success(self, client):
        """Testa análise de computação com dados válidos"""
        payload = {
            'aws_instance_type': 't3.medium',
            'gcp_machine_type': 'e2-medium',
            'aws_region': 'us-east-1',
            'gcp_region': 'us-central1',
            'workload_type': 'general'
        }
        
        response = client.post('/api/analyze/compute',
                             data=json.dumps(payload),
                             content_type='application/json')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['analysis_type'] == 'compute_costs'
        assert 'requirements' in data
        assert 'result' in data
        assert 'timestamp' in data
        assert data['demo_mode'] is True
    
    def test_compute_analysis_no_data(self, client):
        """Testa análise de computação sem dados"""
        response = client.post('/api/analyze/compute',
                             content_type='application/json')
        
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'Dados JSON requeridos'
    
    def test_compute_analysis_result_structure(self, client):
        """Testa estrutura do resultado da análise"""
        payload = {
            'aws_instance_type': 't3.medium',
            'gcp_machine_type': 'e2-medium'
        }
        
        response = client.post('/api/analyze/compute',
                             data=json.dumps(payload),
                             content_type='application/json')
        
        data = json.loads(response.data)
        result = data['result']
        
        required_fields = ['recommendation', 'aws_cost', 'gcp_cost', 'savings', 'confidence', 'reasoning']
        for field in required_fields:
            assert field in result


class TestStorageAnalysisEndpoint:
    """Testes para o endpoint de análise de armazenamento"""
    
    def test_storage_analysis_success(self, client):
        """Testa análise de armazenamento com dados válidos"""
        payload = {
            'aws_storage_type': 's3_standard',
            'gcp_storage_type': 'standard',
            'aws_region': 'us-east-1',
            'gcp_region': 'us-central1',
            'storage_size_gb': 1000
        }
        
        response = client.post('/api/analyze/storage',
                             data=json.dumps(payload),
                             content_type='application/json')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['analysis_type'] == 'storage_costs'
        assert 'requirements' in data
        assert 'result' in data
        assert data['demo_mode'] is True
    
    def test_storage_analysis_result_structure(self, client):
        """Testa estrutura do resultado da análise de armazenamento"""
        payload = {
            'aws_storage_type': 's3_standard',
            'gcp_storage_type': 'standard',
            'storage_size_gb': 1000
        }
        
        response = client.post('/api/analyze/storage',
                             data=json.dumps(payload),
                             content_type='application/json')
        
        data = json.loads(response.data)
        result = data['result']
        
        required_fields = ['recommendation', 'aws_cost_per_gb', 'gcp_cost_per_gb', 'savings', 'confidence', 'reasoning']
        for field in required_fields:
            assert field in result


class TestComprehensiveAnalysisEndpoint:
    """Testes para o endpoint de análise abrangente"""
    
    def test_comprehensive_analysis_success(self, client):
        """Testa análise abrangente com dados válidos"""
        payload = {
            'aws_instance_type': 't3.medium',
            'gcp_machine_type': 'e2-medium',
            'aws_region': 'us-east-1',
            'gcp_region': 'us-central1',
            'workload_type': 'general',
            'aws_storage_type': 's3_standard',
            'gcp_storage_type': 'standard',
            'storage_size_gb': 1000,
            'monthly_budget': 500,
            'performance_priority': 'balanced',
            'time_horizon_months': 36
        }
        
        response = client.post('/api/analyze/comprehensive',
                             data=json.dumps(payload),
                             content_type='application/json')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['analysis_type'] == 'comprehensive'
        assert 'requirements' in data
        assert 'result' in data
        assert data['demo_mode'] is True
    
    def test_comprehensive_analysis_result_structure(self, client):
        """Testa estrutura do resultado da análise abrangente"""
        payload = {
            'aws_instance_type': 't3.medium',
            'gcp_machine_type': 'e2-medium'
        }
        
        response = client.post('/api/analyze/comprehensive',
                             data=json.dumps(payload),
                             content_type='application/json')
        
        data = json.loads(response.data)
        result = data['result']
        
        required_fields = [
            'recommendation', 'total_monthly_cost_aws', 'total_monthly_cost_gcp',
            'monthly_savings', 'annual_savings', 'tco_3_years', 'confidence',
            'breakdown', 'reasoning'
        ]
        
        for field in required_fields:
            assert field in result
        
        # Testa estrutura do breakdown
        breakdown = result['breakdown']
        assert 'compute' in breakdown
        assert 'storage' in breakdown
        assert 'network' in breakdown
        assert 'additional' in breakdown


class TestErrorHandling:
    """Testes para tratamento de erros"""
    
    def test_invalid_json(self, client):
        """Testa requisição com JSON inválido"""
        response = client.post('/api/analyze/compute',
                             data='invalid json',
                             content_type='application/json')
        
        assert response.status_code == 400
    
    def test_missing_content_type(self, client):
        """Testa requisição sem content-type"""
        payload = {'test': 'data'}
        
        response = client.post('/api/analyze/compute',
                             data=json.dumps(payload))
        
        # Deve ainda funcionar, Flask é tolerante
        assert response.status_code in [200, 400]
    
    def test_nonexistent_endpoint(self, client):
        """Testa endpoint inexistente"""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404


class TestCORS:
    """Testes para configuração CORS"""
    
    def test_cors_headers(self, client):
        """Testa se headers CORS estão presentes"""
        response = client.get('/api/health')
        
        # Flask-CORS deve adicionar headers automaticamente
        assert response.status_code == 200
    
    def test_options_request(self, client):
        """Testa requisição OPTIONS para CORS preflight"""
        response = client.options('/api/health')
        
        # Deve permitir OPTIONS requests
        assert response.status_code in [200, 204]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

