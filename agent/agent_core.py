import os
from typing import Dict, Any, Optional, AsyncGenerator
from loguru import logger

from .graph import AgentGraph
from .models import AgentConfig


class AgentCore:
    def __init__(
        self, 
        api_key: Optional[str] = None,
        config: Optional[AgentConfig] = None
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.config = config or AgentConfig()
        self.graph: Optional[AgentGraph] = None
        self._init_graph()

    def _init_graph(self):
        try:
            self.graph = AgentGraph(config=self.config, api_key=self.api_key)
            logger.info("Agent graph initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agent graph: {e}")
            self.graph = None

    def process_query(self, user_query: str) -> Dict[str, Any]:
        if not self.graph:
            logger.warning("Graph not initialized, returning error")
            return {
                "final_answer": "AI service unavailable",
                "trace": [],
                "observations": [],
                "plan": [],
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
                "plan": [],
                "error": str(e)
            }

    async def process_query_stream(self, user_query: str) -> AsyncGenerator[Dict[str, Any], None]:
        if not self.graph:
            yield {"type": "error", "content": "AI service unavailable"}
            return

        logger.info(f"Streaming query: {user_query[:100]}")
        
        try:
            initial_state = self.graph.graph.get_state({})
            # For now, just yield the final result
            result = self.graph.run(user_query)
            
            for trace_item in result.get("trace", []):
                yield {"type": "trace", "content": trace_item}
            
            yield {"type": "final_answer", "content": result.get("final_answer", "")}
            
        except Exception as e:
            logger.error(f"Error streaming query: {e}")
            yield {"type": "error", "content": "AI service unavailable"}

    def is_available(self) -> bool:
        return self.graph is not None

    def get_config(self) -> AgentConfig:
        return self.config