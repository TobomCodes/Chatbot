import os
import chainlit as cl
from llama_index.agent.openai import OpenAIAgent
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.llms.openai import OpenAI
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.readers.file import UnstructuredReader
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage, Settings
import openai
import nest_asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Document loading and indexing
floors = list(range(1, 51))  # List of floors from 1 to 50
loader = UnstructuredReader()
doc_set = {}

# Load documents for each floor
for floor in floors:
    # Load data for the current floor
    levels = loader.load_data(file=Path(f"./heavenly_tower_floors/floor_{floor}.txt"), split_documents=False)

    # Add metadata for each document
    for d in levels:
        d.metadata = {"floor": floor}  # Add floor metadata

    # Store documents in the dictionary
    doc_set[floor] = levels

# Initialize simple vector indices
Settings.chunk_size = 512
index_set = {}

# Create vector store indices for each floor
for floor in floors:
    storage_context = StorageContext.from_defaults()
    cur_index = VectorStoreIndex.from_documents(doc_set[floor], storage_context=storage_context)
    index_set[floor] = cur_index
    storage_context.persist(persist_dir=f"./storage/{floor}")

# Load indices from disk
for floor in floors:
    storage_context = StorageContext.from_defaults(persist_dir=f"./storage/{floor}")
    cur_index = load_index_from_storage(storage_context)
    index_set[floor] = cur_index

# Create query engine tools
individual_query_engine_tools = [
    QueryEngineTool(
        query_engine=index_set[floor].as_query_engine(),
        metadata=ToolMetadata(
            name=f"vector_index_{floor}",
            description=f"useful for when you want to answer queries about a single floor",
        ),
    )
]

# Create a sub-question query engine
query_engine = SubQuestionQueryEngine.from_defaults(
    query_engine_tools=individual_query_engine_tools,
    llm=OpenAI(model="gpt-3.5-turbo"),
)

# Query engine tool for complex queries
query_engine_tool = QueryEngineTool(
    query_engine=query_engine,
    metadata=ToolMetadata(
        name="sub_question_query_engine",
        description=f"useful for when you want to answer queries about multiple floors",
    )
)

# Combine tools for the agent
tools = individual_query_engine_tools + [query_engine_tool]
agent = OpenAIAgent.from_tools(tools)

# Message handling for incoming user messages
@cl.on_message
async def main(message: str):
    # Retrieve and manage conversation history
    conversation_history = cl.user_session.get("conversation_history") or []
    user_message = message.content
    conversation_history.append({"user": user_message})

    # Generate a response from the agent
    response = agent.chat(user_message)
    conversation_history.append({"bot": response})

    # Update session with new conversation history
    cl.user_session.set("conversation_history", conversation_history)

    # Send the response back to the UI
    await cl.Message(content=str(response)).send()

# Authentication callback for user login
@cl.password_auth_callback
def auth_callback(username: str, password: str):
    if (username, password) == (os.getenv("ADMIN_USERNAME"), os.getenv("ADMIN_PASSWORD")):
        return cl.User(
            identifier="admin",
            metadata={"role": "admin", "provider": "credentials"}
        )
    else:
        return None
