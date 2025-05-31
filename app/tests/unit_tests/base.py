import pytest
from unittest.mock import Mock, patch
from typing import Any, Dict

class BaseUnitTest:
    """Базовый класс для unit-тестов"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self) -> None:
        """Метод настройки, который будет выполняться перед каждым тестом"""
        self.setup_mocks()
    
    def setup_mocks(self) -> None:
        """Настройка mock-объектов для тестов"""
        pass
    
    @staticmethod
    def create_mock_response(status_code: int = 200, json_data: Dict[str, Any] = None) -> Mock:
        """
        Создает mock-объект HTTP-ответа
        
        Args:
            status_code: Код статуса HTTP
            json_data: Данные для возврата в формате JSON
            
        Returns:
            Mock: Мок-объект ответа
        """
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data or {}
        return mock_response 