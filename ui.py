import streamlit as st
import requests

# Streamlit App Configuration
st.set_page_config(page_title="LangGraph Agent UI", layout="centered")

# Define API endpoint
API_URL = "http://127.0.0.1:8000/chat"

# Using the gpt-40 model
MODEL_NAME = "gpt-4o"

# Streamlit UI Elements
st.title("Google Calendar AI Chatbot")
st.write("Interact with the LangGraph-based agent using this interface.")



# Input box for user messages
user_input = st.text_area("Enter your message(s):", height=150, placeholder="Type your message here...")

# Button to send the query
if st.button("Submit"):
    if user_input.strip():
        try:
            # Send the input to the FastAPI backend
            payload = {  "model_name": MODEL_NAME,"system_prompt": "You are a helpful assistant that helps users manage their Google Calendar.",
                       "messages": [user_input]}
            response = requests.post(API_URL, json=payload)

            # Display the response
            if response.status_code == 200:
                response_data = response.json()
                if "error" in response_data:
                    st.error(response_data["error"])
                else:
                    ai_responses = [
                        message.get("content", "")
                        for message in response_data.get("messages", [])
                        if message.get("type") == "ai"
                    ]

                    if ai_responses:
                        st.subheader("Agent Response:")
                        st.markdown(f"**Final Response:** {ai_responses[-1]}")
                        # for i, response_text in enumerate(ai_responses, 1):
                        #     st.markdown(f"**Response {i}:** {response_text}")
                    else:
                        st.warning("No AI response found in the agent output.")
            else:
                st.error(f"Request failed with status code {response.status_code}.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter a message before clicking 'Send Query'.")