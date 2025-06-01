import pytest
from pytest_mock import MockerFixture
from typing import Any, Dict

class BaseUnitTest:
    """Базовый класс для unit-тестов"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker: MockerFixture) -> None:
        """Метод настройки, который будет выполняться перед каждым тестом"""
        self.setup_mocks(mocker)
    
    def setup_mocks(self, mocker: MockerFixture) -> None:
        """Настройка mock-объектов для тестов"""
        pass
    
    @staticmethod
    def create_mock_response(
        mocker: MockerFixture, 
        status_code: int = 200, 
        json_data: Dict[str, Any] = None,
    ) -> Any:
        """
        Создает mock-объект HTTP-ответа
        
        Args:
            mocker: Фикстура pytest-mock
            status_code: Код статуса HTTP
            json_data: Данные для возврата в формате JSON
            
        Returns:
            Mock: Мок-объект ответа
        """
        mock_response = mocker.Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data or {}
        return mock_response 