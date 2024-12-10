import logging
from semantic_kernel.agents import ChatCompletionAgent

logger = logging.getLogger("uvicorn.error")


class StockAgent(ChatCompletionAgent):
    def __init__(self, kernel, execution_settings):
        ChatCompletionAgent.__init__(
            self,
            kernel=kernel,
            name="stock-agent",
            instructions="""You are the stock agent.
              You are responsible for providing stock prices related to the stock market.
            """,
            execution_settings=execution_settings
        )


__all__ = ["StockAgent"]
