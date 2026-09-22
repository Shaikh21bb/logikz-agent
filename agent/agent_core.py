import os
from typing import Dict, Any
from loguru import logger

from .graph import AgentGraph


class AgentCore:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.graph = None
        self._init_graph()

    def _init_graph(self):
        try:
            self.graph = AgentGraph(api_key=self.api_key)
            logger.info("Agent graph initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agent graph: {e}")
            self.graph = None

    def process_query(self, user_query: str) -> Dict[str, Any]:
        if not self.graph:
            return {
                "final_answer": "AI service unavailable",
                "trace": [],
                "observations": [],
                "error": "Graph not initialized"
            }

        logger.info(f"Processing query: {user_query[:100]}")
        try:
            result = self.graph.run(user_query)
            logger.info("Query processed successfully")
            return result
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "final_answer": "AI service unavailable",
                "trace": [],
                "observations": [],
                "error": str(e)
            }

    def is_available(self) -> bool:
        return self.graph is not None