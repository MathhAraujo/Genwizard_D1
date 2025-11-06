import json
import random
import string
import requests
import urllib3
from datetime import datetime
from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import asyncio
from httpx import AsyncClient

app = FastAPI()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === Allow frontend access ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === In-memory list of printed tickets ===
printed_tickets = []


# === External API sender ===
def send_events(priority, label, value, resource, sub_resource, env, tower, prblm_type, origin, description):
    trigger_time = str(datetime.now().timestamp()).split('.')[0]

    URL = "https://acnint50-api.eventops-aiops.com/produce?authid=MAIN"
    KEY = os.getenv("API_KEY")

    headers = {
        "x-api-key": KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "origin": origin,
        "SRC_UNIX_CLOCK": trigger_time,
        "SRC_PRIORITY": priority,
        "SRC_LABEL": label,
        "SRC_DESCRIPTION": description,
        "SRC_PROBLEM_VALUE": value,
        "SRC_RSOURCE": resource,
        "SRC_SUB_RESOURCE": sub_resource,
        "SRC_ENV": env,
        "SRC_TOWER": tower,
        "SRC_PROBLEM_TYPE": prblm_type
    }

    print("Sending event payload:")
    print(payload)

    try:
        data = requests.post(URL, headers=headers, data=json.dumps(payload), verify=False)
        print("Event API response:", data.json())
        return {"status": "success", "external_response": data.json()}
    except Exception as e:
        print("Error sending event:", e)
        return {"status": "error", "details": str(e)}


# === Pydantic model for tickets ===
class Ticket(BaseModel):
    ticket_number: str
    description: str


# === Internal print endpoint (called after API succeeds) ===
@app.post("/print_ticket_internal")
async def print_ticket_internal(ticket: Ticket):
    ticket_data = ticket.dict()
    printed_tickets.append(ticket_data)

    print("=== Printing Ticket ===")
    print(f"Ticket Number: {ticket.ticket_number}")
    print(f"Description: {ticket.description}")
    print("=======================")

    return JSONResponse(content=ticket_data)


# === Public endpoint to create a new ticket ===
@app.post("/create_ticket")
async def create_ticket(
    shortDescription: str = Form(...),
    description: str = Form(...)
):
    priority = "Low"
    label = shortDescription
    value = "Operation"
    resource = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    sub_resource = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    env = "DEV"
    tower = "Matheus Araujo"
    prblm_type = "KO"
    origin = "Recife"

    result = send_events(priority, label, value, resource, sub_resource, env, tower, prblm_type, origin, description)

# === Endpoint to fetch printed tickets ===
@app.get("/get_printed_tickets")
async def get_printed_tickets():
    return JSONResponse(content={"tickets": printed_tickets})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
