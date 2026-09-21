import sys
from pathlib import Path

from google.adk.agents.llm_agent import Agent

# Find the shared configuration when ADK runs from the workspace directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from llm_config import create_model

root_agent = Agent(
    model=create_model(),
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction='Answer user questions to the best of your knowledge',
)
