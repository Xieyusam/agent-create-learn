import os
import sys
import pytest
from unittest.mock import Mock, patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.customer_service import CustomerServiceAgent  # noqa: E402


@patch("app.customer_service.ProductRAG")
@patch("app.customer_service.ChatOpenAI")
def test_env_placeholder_parsing_success(mock_chat_openai, mock_rag, monkeypatch):
    monkeypatch.setenv("DOUBAO_API_KEY", "sk-test-123")
    mock_chat_openai.return_value = Mock()
    mock_rag.return_value = Mock()
    monkeypatch.setenv("APP_CONFIG_PATH", os.path.join(PROJECT_ROOT, "config.yaml"))
    agent = CustomerServiceAgent()
    assert agent is not None


@patch("app.customer_service.ProductRAG")
@patch("app.customer_service.ChatOpenAI")
def test_missing_env_variable_error(mock_chat_openai, mock_rag, monkeypatch):
    mock_chat_openai.return_value = Mock()
    mock_rag.return_value = Mock()
    monkeypatch.delenv("DOUBAO_API_KEY", raising=False)
    monkeypatch.setenv("APP_CONFIG_PATH", os.path.join(PROJECT_ROOT, "config.yaml"))
    with pytest.raises(ValueError):
        CustomerServiceAgent()


@patch("app.customer_service.ProductRAG")
@patch("app.customer_service.ChatOpenAI")
def test_workflow_initialization(mock_chat_openai, mock_rag, monkeypatch):
    monkeypatch.setenv("DOUBAO_API_KEY", "sk-test-123")
    mock_chat_openai.return_value = Mock()
    mock_rag.return_value = Mock()
    monkeypatch.setenv("APP_CONFIG_PATH", os.path.join(PROJECT_ROOT, "config.yaml"))
    agent = CustomerServiceAgent()
    assert agent.graph is not None
