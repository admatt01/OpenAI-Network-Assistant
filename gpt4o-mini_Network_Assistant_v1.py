import os
import logging
import json
import time
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from tools.get_local_time import get_local_time
from tools.librenms_bgp import librenms_bgp
from tools.librenms_arp import librenms_arp
from tools.librenms_get_device_info import librenms_get_device_info
from tools.librenms_syslog import librenms_syslog
from tools.librenms_list_networks import librenms_list_networks
from tools.librenms_port_info import librenms_port_info
from tools.librenms_search_ifalias import librenms_search_ifalias
from tools.show_commands_gpt4o import show_commands_gpt4o
from tools.config_commands import config_commands

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
if "start_chat" not in st.session_state:
    st.session_state.start_chat = False
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "openai_model" not in st.session_state:
    st.session_state.openai_model = "gpt-4o-mini-2024-07-18"
if "messages" not in st.session_state:
    st.session_state.messages = []

# Set up Streamlit page
st.set_page_config(page_title="GPT4o Mini Network Assistant", page_icon=":speech_balloon:")
st.title("Welcome to the GPT4o Mini Network Assistant")

# Sidebar and control buttons
if st.sidebar.button("Start Chat"):
    st.session_state.start_chat = True
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

if st.button("Exit Chat"):
    st.session_state.messages = []
    st.session_state.start_chat = False
    st.session_state.thread_id = None

# Function to poll run status
def poll_run(client, thread_id, run_id, timeout=300):
    start_time = time.time()
    while time.time() - start_time < timeout:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if run.status in ['completed', 'requires_action', 'failed']:
            return run
        time.sleep(1)
    raise TimeoutError("Run polling timed out")

# Main chat logic
if st.session_state.start_chat:
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
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_id,
        )
        run = poll_run(client, st.session_state.thread_id, run.id)

        # Handle different run statuses
        if run.status == 'requires_action':
            tool_outputs = []
            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                try:
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    logger.info(f"Processing tool: {tool_name} with args: {arguments}")

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
                    elif tool_name == "librenms_port_info":
                        port_info_result = librenms_port_info(**arguments)
                        output = json.dumps(port_info_result, indent=2)
                    elif tool_name == "librenms_search_ifalias":
                        if_alias_result = librenms_search_ifalias(**arguments)
                        output = json.dumps(if_alias_result, indent=2)
                    elif tool_name == "show_commands_gpt4o":
                        gpt4o_result =show_commands_gpt4o(**arguments)
                        output = json.dumps(gpt4o_result, indent=2)
                    elif tool_name == "config_commands":
                        config_result = config_commands(**arguments)
                        output = json.dumps(config_result, indent=2)
                    else:
                        raise ValueError(f"Unknown tool: {tool_name}")

                    tool_outputs.append({"tool_call_id": tool_call.id, "output": output})
                except Exception as e:
                    logger.error(f"Error executing tool {tool_name}: {str(e)}")
                    tool_outputs.append({"tool_call_id": tool_call.id, "output": f"Error: {str(e)}"})

            # Submit tool outputs and poll again
            run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=st.session_state.thread_id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
            run = poll_run(client, st.session_state.thread_id, run.id)

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

else:
    st.write("Click 'Start Chat' to begin.")