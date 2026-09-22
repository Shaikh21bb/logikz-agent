import pytest
from unittest.mock import patch, MagicMock
import os

os.environ["OPENAI_API_KEY"] = "test-key"


class TestAgentCore:
    @pytest.fixture
    def agent(self):
        from agent.agent_core import AgentCore
        with patch("agent.graph.ChatOpenAI"):
            return AgentCore(api_key="test-key")

    def test_normal_query(self, agent):
        with patch.object(agent.graph, "run") as mock_run:
            mock_run.return_value = {
                "final_answer": "📦 Товар: Сервер\n🏷 ТН ВЭД: 8471\n💰 Стоимость товара: $50,000\n🚚 Логистика: $25,000\n🧾 Таможенная стоимость: $75,000\n📊 Пошлина: $0\n🇰🇿 НДС: $9,000\n💵 Итого: $84,000\nИсточник данных: Demo / Mock",
                "trace": ["🔎 Определяю категорию товара...", "💰 Рассчитываю таможенные платежи..."],
                "observations": [],
            }
            result = agent.process_query("Импортирую серверы из Китая в Казахстан. Стоимость $50 000, вес 10 тонн.")
            assert "Сервер" in result["final_answer"]
            assert "8471" in result["final_answer"]
            assert "Итого" in result["final_answer"]

    def test_tn_ved_query(self, agent):
        with patch.object(agent.graph, "run") as mock_run:
            mock_run.return_value = {
                "final_answer": "📦 Товар: Сервер\n🏷 ТН ВЭД: 8471\n💰 Стоимость товара: $50,000\n🚚 Логистика: $0\n🧾 Таможенная стоимость: $50,000\n📊 Пошлина: $0\n🇰🇿 НДС: $6,000\n💵 Итого: $56,000\nИсточник данных: Demo / Mock",
                "trace": ["🔎 Определяю категорию товара...", "📦 Проверяю ТН ВЭД..."],
                "observations": [],
            }
            result = agent.process_query("Каков ТН ВЭД для серверов?")
            assert "8471" in result["final_answer"]

    def test_customs_query(self, agent):
        with patch.object(agent.graph, "run") as mock_run:
            mock_run.return_value = {
                "final_answer": "📦 Товар: Товары\n🏷 ТН ВЭД: 9999\n💰 Стоимость товара: $10,000\n🚚 Логистика: $0\n🧾 Таможенная стоимость: $10,000\n📊 Пошлина: $500\n🇰🇿 НДС: $1,260\n💵 Итого: $11,760\nИсточник данных: Demo / Mock",
                "trace": ["💰 Рассчитываю таможенные платежи..."],
                "observations": [],
            }
            result = agent.process_query("Рассчитай таможню на товары стоимостью $10,000")
            assert "Пошлина" in result["final_answer"]
            assert "НДС" in result["final_answer"]

    def test_tool_error(self, agent):
        with patch.object(agent.graph, "run") as mock_run:
            mock_run.return_value = {
                "final_answer": "📦 Товар: Тест\n🏷 ТН ВЭД: 9999\n💰 Стоимость товара: $0\n🚚 Логистика: $0\n🧾 Таможенная стоимость: $0\n📊 Пошлина: $0\n🇰🇿 НДС: $0\n💵 Итого: $0\nИсточник данных: Demo / Mock",
                "trace": [],
                "observations": [{"tool": "search_tn_ved_database", "error": "Tool execution failed"}],
            }
            result = agent.process_query("Тест ошибки")
            assert "Demo / Mock" in result["final_answer"]

    def test_api_unavailable(self, agent):
        agent.graph = None
        result = agent.process_query("Любой запрос")
        assert result["final_answer"] == "AI service unavailable"

    def test_final_answer_format(self, agent):
        with patch.object(agent.graph, "run") as mock_run:
            mock_run.return_value = {
                "final_answer": "📦 Товар: Сервер\n🏷 ТН ВЭД: 8471\n💰 Стоимость товара: $50,000\n🚚 Логистика: $25,000\n🧾 Таможенная стоимость: $75,000\n📊 Пошлина: $0\n🇰🇿 НДС: $9,000\n💵 Итого: $84,000\nИсточник данных: Demo / Mock",
                "trace": [],
                "observations": [],
            }
            result = agent.process_query("Тест формата")
            answer = result["final_answer"]
            assert answer.startswith("📦 Товар:")
            assert "🏷 ТН ВЭД:" in answer
            assert "💰 Стоимость товара:" in answer
            assert "🚚 Логистика:" in answer
            assert "🧾 Таможенная стоимость:" in answer
            assert "📊 Пошлина:" in answer
            assert "🇰🇿 НДС:" in answer
            assert "💵 Итого:" in answer
            assert "Источник данных:" in answer