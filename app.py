# app.py

import os
import json
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_groq import ChatGroq
from langchain.tools import tool
from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Get service account credentials from environment variable

credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
calendar_id = os.getenv("GOOGLE_CALENDAR_ID")  # The calendar to update (must be shared with the service account)

google_creds = service_account.Credentials.from_service_account_file(
    credentials_path,
    scopes=["https://www.googleapis.com/auth/calendar"]
)

calendar_service = build("calendar", "v3", credentials=google_creds)

# Groq & Tavily config
groq_api_key = os.getenv("GROQ_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

MODEL_NAME = "gpt-4o"
tool_tavily = TavilySearchResults(max_results=2)

# Define a LangChain-compatible tool for booking events
@tool
def book_event(summary: str, start_time: str, duration_minutes: int = 60) -> str:
    """Book a calendar event given a summary, start time (ISO format), and duration."""
    try:
        start = datetime.fromisoformat(start_time)
        end = start + timedelta(minutes=duration_minutes)

        event = {
            'summary': summary,
            'start': {'dateTime': start.isoformat(), 'timeZone': 'Asia/Kolkata'},
            'end': {'dateTime': end.isoformat(), 'timeZone': 'Asia/Kolkata'}
        }
        created_event = calendar_service.events().insert(calendarId=calendar_id, body=event).execute()
        return f"Event '{summary}' booked on {start.strftime('%Y-%m-%d %H:%M')}"
    except Exception as e:
        return f"Failed to book event: {e}"

# Combine all tools
tools = [tool_tavily, book_event]

app = FastAPI(title="LangGraph Calendar Agent")

# Allow Streamlit frontend to access this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for incoming request
class RequestState(BaseModel):
    model_name: str
    messages: List[str]

@app.post("/chat")
def chat_endpoint(request: RequestState):
   

    llm = ChatGroq(groq_api_key=groq_api_key, model_name=MODEL_NAME)

    # Basic system prompt
    system_prompt = "You are a helpful assistant that can schedule meetings in a Google Calendar using the book_event tool."

    agent = create_react_agent(llm, tools=tools, state_modifier=system_prompt)

    state = {"messages": request.messages}

    try:
        result = agent.invoke(state)
        return result
    except Exception as e:
        return {"error": str(e)}

# For local dev
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
