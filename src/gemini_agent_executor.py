import json
import logging
import inspect
from typing import Any

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    AgentCard,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils.errors import ServerError
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class GeminiAgentExecutor(AgentExecutor):
    """An AgentExecutor that runs a Google GenAI-based Agent."""
    def __init__(
        self,
        card: AgentCard,
        tools: dict[str, Any],
        api_key: str,
        system_prompt: str,
    ):
        self._card = card
        self.tools = tools
        self.client = genai.Client(api_key=api_key)
        self.model = 'gemini-2.5-flash'
        self.system_prompt = system_prompt
        self.chat = None

    async def _process_request(
        self,
        message_text: str,
        context: RequestContext,
        task_updater: TaskUpdater,
    ) -> None:
        
        gemini_tool = types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name='query_knowledge_base',
                    description='Search the Aura Electronics knowledge base.',
                    parameters=types.Schema(
                        type='OBJECT',
                        properties={
                            'search_term': types.Schema(
                                type='STRING',
                                description="A short keyword (e.g., 'AuraSync', 'refund')."
                            )
                        },
                        required=['search_term']
                    )
                ),
                types.FunctionDeclaration(
                    name='escalate_to_human',
                    description='Escalate to a human Tier 2 agent for critical issues.',
                    parameters=types.Schema(
                        type='OBJECT',
                        properties={
                            'reason': types.Schema(type='STRING', description="Why this is being escalated."),
                            'context_summary': types.Schema(type='STRING', description="A summary of the issue so far.")
                        },
                        required=['reason', 'context_summary']
                    )
                )
            ]
        )

        config = types.GenerateContentConfig(
            system_instruction=self.system_prompt,
            temperature=0.1,
            tools=[gemini_tool],
        )

        max_iterations = 10
        iteration = 0
        
        if not self.chat:
            self.chat = self.client.chats.create(
                model=self.model,
                config=config,
            )

        try:
            response = self.chat.send_message(message_text)

            while iteration < max_iterations:
                iteration += 1

                if not response.function_calls:
                    if response.text:
                        parts = [TextPart(text=response.text)]
                        await task_updater.add_artifact(parts)
                        await task_updater.complete()
                    break

                parts_to_send = []
                for function_call in response.function_calls:
                    function_name = function_call.name
                    function_args = function_call.args
                    
                    arg_dict = {k: v for k, v in function_args.items()}
                    await task_updater.update_status(
                        TaskState.working,
                        message=task_updater.new_agent_message(
                            [TextPart(text=f'Executing tool: {function_name}')]
                        ),
                    )

                    if function_name in self.tools:
                        tool_ref = self.tools[function_name]
                        # If tool_ref is the SupportToolset instance, grab the method via getattr
                        if not callable(tool_ref) and hasattr(tool_ref, function_name):
                            method = getattr(tool_ref, function_name)
                        else:
                            method = tool_ref
                            
                        if inspect.iscoroutinefunction(method):
                            result = await method(**arg_dict)
                        else:
                            result = method(**arg_dict)
                    else:
                        result = f'Function {function_name} not found'

                    part = types.Part.from_function_response(
                        name=function_name,
                        response={"result": result}
                    )
                    parts_to_send.append(part)
                    
                response = self.chat.send_message(parts_to_send)

            # ... rest of the error handling remains the same ...

            if iteration >= max_iterations:
                error_parts = [
                    TextPart(
                        text='Sorry, the request has exceeded the maximum number of iterations.'
                    )
                ]
                await task_updater.add_artifact(error_parts)
                await task_updater.complete()

        except Exception as e:
            logger.error(f'Error in Gemini API call: {e}')
            error_parts = [
                TextPart(
                    text=f'Sorry, an error occurred while processing the request: {e!s}'
                )
            ]
            await task_updater.add_artifact(error_parts)
            await task_updater.complete()


    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ):
        # Run the agent until complete
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        # Immediately notify that the task is submitted.
        if not context.current_task:
            await updater.submit()
        await updater.start_work()

        # Extract text from message parts
        message_text = ''
        for part in context.message.parts:
            if isinstance(part.root, TextPart):
                message_text += part.root.text

        await self._process_request(message_text, context, updater)
        logger.debug('[Supporter Agent] execute exiting')

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        # Ideally: kill any ongoing tasks.
        raise ServerError(error=UnsupportedOperationError())
