import os
import json
import streamlit as st
from dotenv import load_dotenv
import openai
from openai.assistants import Assistant
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Load environment variables
load_dotenv()
LIBRENMS_API_TOKEN = os.getenv("LIBRENMS_API_TOKEN")
LIBRENMS_BASE_URL = os.getenv("LIBRENMS_BASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

# Load tools metadata
tools = {}
tools_path = "tools"
for tool_file in os.listdir(tools_path):
    if tool_file.endswith(".json"):
        with open(os.path.join(tools_path, tool_file), 'r') as f:
            tool_data = json.load(f)
            tools[tool_data['name']] = tool_data

# Load router information
with open("devices/routers.json", 'r') as f:
    routers = json.load(f)

# Streamlit app setup
st.title("Network AI Assistant")
st.write("Ask the assistant for help with your network.")

# File uploader for images
uploaded_file = st.file_uploader("Upload a screenshot or other image", type=["png", "jpg", "jpeg"])

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# User query input
user_query = st.text_input("Enter your query:", key="user_query")

# Human verification checkbox
human_verification = st.checkbox("I am not a robot")
response_placeholder = st.empty()

# Initialize the Assistant
assistant = Assistant(
    model="gpt4o-mini",
    api_key=OPENAI_API_KEY
)

# Define functions that the assistant can call
def get_router_info(router_name):
    return routers.get(router_name, "Router not found")

# Function to handle user query
async def handle_query(query):
    # Implement the logic to handle the query using OpenAI assistants API
    response = await assistant.chat(
        messages=[{"role": "user", "content": query}],
        stream=True,
        functions=[
            {
                "name": "get_router_info",
                "description": "Get information about a specific router",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "router_name": {
                            "type": "string",
                            "description": "The name of the router"
                        }
                    },
                    "required": ["router_name"]
                }
            }
        ]
    )
    async for message in response:
        if "function_call" in message:
            function_name = message["function_call"]["name"]
            arguments = message["function_call"]["arguments"]
            if function_name == "get_router_info":
                result = get_router_info(arguments["router_name"])
                response_placeholder.text(result)
        else:
            response_placeholder.text(message['content'])

# Handle user query submission
if st.button("Submit") and human_verification:
    if user_query:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_query})
        
        response_placeholder.text("Processing your query...")
        
        # Handle the query and get the response
        asyncio.run(handle_query(user_query))
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response_placeholder.text()})
        
        # Display chat history
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.write(f"**You:** {message['content']}")
            else:
                st.write(f"**Assistant:** {message['content']}")
        asyncio.run(handle_query(user_query))
    elif not human_verification:
        st.warning("Please verify that you are not a robot.")
        st.warning("Please enter a query.")
