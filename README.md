# Customer Support Automation Agent

An intelligent, autonomous customer support agent built with the A2A (Agent2Agent) SDK and powered by Official Google GenAI SDK (`google-genai`).

## Features

- **Multi-Turn Conversations**: Maintains context with users smoothly.
- **Knowledge Base Retrieval**: Extends the agent's knowledge by fetching context directly from `support_toolset.py` using function calling.
- **Escalation Management**: Forwards to Tier-2 support for complex technical issues, anger, or fraud handling.
- **Intent Classification**: Prioritizes actions based on whether the query was about billing, returns, or technical support.

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. Set up environment variables:
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key"
   ```

## Usage

### Running the Agent

```bash
python -m src --host localhost --port 5000
```

### Available Functions

#### query_knowledge_base
When the agent needs information on the store's refund or technical policy, it searches `knowledge_base.json`.

#### escalate_to_human
Automatically kicks into gear when the customer requires human interaction.

## Environment Variables

- `GEMINI_API_KEY`: Required for Google GenAI LLM execution and function calling.
- `PORT`: Server port (optional, default: 5000)
- `HOST`: Server host (optional, default: localhost)