import os
import json
import streamlit as st
from dotenv import load_dotenv
import openai
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

# User query input
user_query = st.text_input("Enter your query:")

# Placeholder for assistant response
response_placeholder = st.empty()

# Function to handle user query
async def handle_query(query):
    # Implement the logic to handle the query using OpenAI API and tools
    response = await openai.Completion.acreate(
        engine="gpt4o-mini",
        prompt=query,
        max_tokens=150,
        stream=True
    )
    async for message in response:
        response_placeholder.text(message['choices'][0]['text'])

# Handle user query submission
if st.button("Submit"):
    if user_query:
        response_placeholder.text("Processing your query...")
        asyncio.run(handle_query(user_query))
    else:
        st.warning("Please enter a query.")
