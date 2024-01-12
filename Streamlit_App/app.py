import InvokeAgent as agenthelper
import streamlit as st
import uuid
import json
import pandas as pd
from PIL import Image, ImageOps, ImageDraw

# Streamlit page configuration
st.set_page_config(page_title="Assistente Pointer", page_icon=":robot_face:", layout="wide")

sessionid = str(uuid.uuid4())

# Function to crop image into a circle
def crop_to_circle(image):
    mask = Image.new('L', image.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0) + image.size, fill=255)
    result = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    result.putalpha(mask)
    return result
    
def format_response(response_body):
    try:
        # Try to load the response as JSON
        data = json.loads(response_body)
        # If it's a list, convert it to a DataFrame for better visualization
        if isinstance(data, list):
            return pd.DataFrame(data)
        else:
            return response_body
    except json.JSONDecodeError:
        # If response is not JSON, return as is
        return response_body
    
# Function to check if the string is a link to an image
def is_image_link(text):
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']
    return any(text.lower().endswith(ext) for ext in image_extensions)

# Function to render images in the answer
def render_images(answer):
    lines = answer.split('\n')
    for i, line in enumerate(lines):
        if is_image_link(line):
            st.image(line, caption=f"Image {i+1}", use_column_width=True)


# Title
st.title("Assistente Pointer")

# Session State Management
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = sessionid
    st.session_state['history'] = []

while True:
    # Display a text box for input
    prompt = st.text_input("Em que posso ajudar?", max_chars=2000)
    prompt = prompt.strip()

    # Display a primary button for submission
    submit_button = st.button("Enviar", type="primary")

    if not submit_button or not prompt:
        break  # Break the loop if the user didn't submit a question

    # Function to reset session
    def reset_session():
        st.session_state['session_id'] = sessionid
        st.session_state['history'] = []

    # Handling user input and responses
    if submit_button and prompt:
        event = {
            "sessionId": sessionid,
            "question": prompt
        }
        response = agenthelper.lambda_handler(event, None)

        # Parse the JSON string
        response_data = json.loads(response['body'])

        # Check if 'response' key is present in response_data
        if 'response' in response_data:
            # Extract the response and trace data
            all_data = format_response(response_data['response'])
            the_response = response_data['trace_data']

            # Append the current question and answer to the conversation history
            st.session_state['history'].append({"question": prompt, "answer": the_response})

            # Use trace_data and formatted_response as needed
            st.sidebar.text_area("Tracing", value=all_data, height=300)
            st.session_state['trace_data'] = the_response
        else:
            # Handle the case when 'response' key is not present
            st.sidebar.text("Error: 'response' key not found in the API response.")

# Display conversation history
st.write("## Output")

for chat in reversed(st.session_state['history']):
    # Creating columns for Question
    col1_q, col2_q = st.columns([2, 10])
    with col1_q:
        human_image = Image.open('images/human_face.jpg')
        circular_human_image = crop_to_circle(human_image)
        st.image(circular_human_image, width=125)
    with col2_q:
        st.text_area("Q:", value=chat["question"], height=50, key=str(chat) + "q", disabled=True)

    # Creating columns for Answer
    col1_a, col2_a = st.columns([2, 10])
    if isinstance(chat["answer"], pd.DataFrame):
        with col1_a:
            robot_image = Image.open('images/robot_face.jpg')
            circular_robot_image = crop_to_circle(robot_image)
            st.image(circular_robot_image, width=100)
        with col2_a:
            st.dataframe(chat["answer"])
    else:
        with col1_a:
            robot_image = Image.open('images/robot_face.jpg')
            circular_robot_image = crop_to_circle(robot_image)
            st.image(circular_robot_image, width=150)
        with col2_a:
            st.text_area("A:", value=chat["answer"], height=100, key=str(chat) + "a")
            render_images(chat["answer"])