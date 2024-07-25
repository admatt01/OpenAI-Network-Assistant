import os
import logging
import json
import time
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import uuid
import asyncio
from tools.get_local_time import get_local_time
from tools.librenms_bgp import librenms_bgp
from tools.librenms_arp import librenms_arp
from tools.librenms_get_device_info import librenms_get_device_info
from tools.librenms_syslog import librenms_syslog
from tools.librenms_list_networks import librenms_list_networks
from tools.show_commands import show_commands
from tools.config_commands import config_commands
from tools.librenms_get_interface_info import librenms_get_interface_info

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# Declare the Assistant's ID
assistant_id = os.environ.get('OPENAI_ASSISTANT_ID')

# Initialize session state variables
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "openai_model" not in st.session_state:
    st.session_state.openai_model = "gpt-4o-mini-2024-07-18"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tool_results" not in st.session_state:
    st.session_state.tool_results = {}

# Set up Streamlit page
st.set_page_config(page_title="GPT4 Network Assistant", page_icon=":speech_balloon:")
st.title("Welcome to the GPT4 Network Assistant")

# Sidebar with Restart Session button and model selection
if st.sidebar.button("Restart Session"):
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.thread_id = None
    st.session_state.messages = []
    st.session_state.tool_results = {}
    st.rerun()
    
st.sidebar.markdown("<br>", unsafe_allow_html=True) 

# Add model selection dropdown to sidebar
model_options = ["gpt-4o-mini-2024-07-18", "gpt-4o", "gpt-4-turbo-preview"]
st.session_state.openai_model = st.sidebar.selectbox(
    "Select Model",
    options=model_options,
    index=model_options.index(st.session_state.openai_model)
)

st.sidebar.markdown("<br>", unsafe_allow_html=True) 

# Function to poll run status
async def poll_run(client, thread_id, run_id, timeout=300):
    start_time = time.time()
    while time.time() - start_time < timeout:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if run.status in ['completed', 'requires_action', 'failed']:
            return run
        await asyncio.sleep(1)
    raise TimeoutError("Run polling timed out")

# Asynchronous function to handle tool execution
async def execute_tool(tool_call):
    tool_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    logger.info(f"Processing tool: {tool_name} with args: {arguments}")

    try:
        if tool_name == "get_local_time":
            output = str(get_local_time(arguments))
        elif tool_name == "librenms_bgp":
            bgp_result = librenms_bgp(**arguments)
            output = json.dumps(bgp_result, indent=2)
        elif tool_name == "librenms_arp":
            arp_result = librenms_arp(**arguments)
            output = json.dumps(arp_result, indent=2)
        elif tool_name == "librenms_get_device_info":
            device_info_result = librenms_get_device_info(**arguments)
            output = json.dumps(device_info_result, indent=2)
        elif tool_name == "librenms_syslog":
            syslog_result = librenms_syslog(**arguments)
            output = json.dumps(syslog_result, indent=2)
        elif tool_name == "librenms_list_networks":
            network_list_result = librenms_list_networks(**arguments)
            output = json.dumps(network_list_result, indent=2)
        elif tool_name == "librenms_get_interface_info":
            interface_info_result = librenms_get_interface_info(**arguments)
            output = json.dumps(interface_info_result, indent=2)
        elif tool_name == "show_commands":
            show_result = show_commands(**arguments)
            output = json.dumps(show_result, indent=2)
        elif tool_name == "config_commands":
            config_result = config_commands(**arguments)
            output = json.dumps(config_result, indent=2)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

        # Store tool result
        st.session_state.tool_results[tool_name] = output
        return {"tool_call_id": tool_call.id, "output": output}
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}")
        return {"tool_call_id": tool_call.id, "output": f"Error: {str(e)}"}

# Main chat logic
if not st.session_state.thread_id:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    
    # Add introduction message
    intro_message = "Hello! I'm your GPT4 Network Assistant. I'm fast and cheap but I'm not easy. How can I help you today?"
    st.session_state.messages.append({"role": "assistant", "content": intro_message})

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Get user input
if prompt := st.chat_input("Enter your message"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Create message in the thread
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=prompt
    )

    # Create and poll the run
    with st.spinner("Assistant is thinking..."):
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_id,
            model=st.session_state.openai_model  # Use the selected model
        )
        run = asyncio.run(poll_run(client, st.session_state.thread_id, run.id))

    # Handle different run statuses
    while run.status == 'requires_action':
        tool_calls = run.required_action.submit_tool_outputs.tool_calls
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tasks = [execute_tool(tool_call) for tool_call in tool_calls]
        tool_outputs = loop.run_until_complete(asyncio.gather(*tasks))

        # Submit tool outputs and poll again
        run = client.beta.threads.runs.submit_tool_outputs(
            thread_id=st.session_state.thread_id,
            run_id=run.id,
            tool_outputs=tool_outputs
        )
        run = loop.run_until_complete(poll_run(client, st.session_state.thread_id, run.id))

    if run.status == 'completed':
        messages = client.beta.threads.messages.list(
            thread_id=st.session_state.thread_id
        )
        
        # Process and display assistant messages
        assistant_messages = [
            message for message in messages 
            if message.run_id == run.id and message.role == "assistant"
        ]
        for message in assistant_messages:
            content = message.content[0].text.value
            st.session_state.messages.append({"role": "assistant", "content": content})
            with st.chat_message("assistant"):
                st.markdown(content)
    else:
        logger.error(f"Run ended with unexpected status: {run.status}")
        st.error(f"An error occurred: Run ended with status {run.status}")

# File upload in sidebar
uploaded_files = st.sidebar.file_uploader("Upload files to vector db", accept_multiple_files=True, type=['pdf', 'txt', 'docx', 'json'])

if st.sidebar.button("Upload Files"):
    if uploaded_files:
        # Upload files to vector store
        file_streams = [file for file in uploaded_files]
        vector_store_id = os.environ.get('OPENAI_VECTORSTORE_ID')
        try:
            file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store_id, files=file_streams
            )
            st.sidebar.success(f"Files uploaded successfully! Status: {file_batch.status}")
            st.sidebar.info(f"File counts: {file_batch.file_counts}")
        except Exception as e:
            st.sidebar.error(f"Error uploading files: {str(e)}")
    else:
        st.sidebar.warning("Please select files to upload.")