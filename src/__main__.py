import logging
import os

import click
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from dotenv import load_dotenv
from .gemini_agent import create_agent  # type: ignore[import-not-found]
from .gemini_agent_executor import (
    GeminiAgentExecutor,  # type: ignore[import-untyped]
)
from starlette.applications import Starlette


load_dotenv()

logging.basicConfig()


@click.command()
@click.option('--host', 'host', default='localhost')
@click.option('--port', 'port', default=5000)
def main(host: str, port: int):
    # Verify an API key is set.
    if not os.getenv('GEMINI_API_KEY'):
        raise ValueError('GEMINI_API_KEY environment variable not set')

    skill = AgentSkill(
        id='support_agent',
        name='Customer Support Agent',
        description='Handle multi-turn conversations for customer support',
        tags=['support', 'billing', 'technical', 'returns'],
        examples=[
            'I need to return a product.',
            'Why was I charged again?',
            'My product will not turn on.',
            'What is the refund policy?',
        ],
    )

    # AgentCard for Gemini-based agent
    agent_card = AgentCard(
        name='Customer Support Agent',
        description='An intelligent customer support agent for Nasiko that handles billing, returns, and technical queries',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )

    # Create Gemini agent
    agent_data = create_agent()

    agent_executor = GeminiAgentExecutor(
        card=agent_card,
        tools=agent_data['tools'],
        api_key=os.getenv('GEMINI_API_KEY'),
        system_prompt=agent_data['system_prompt'],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor, task_store=InMemoryTaskStore()
    )

    a2a_app = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )
    routes = a2a_app.routes()

    app = Starlette(routes=routes)

    uvicorn.run(app, host=host, port=port)


if __name__ == '__main__':
    main()