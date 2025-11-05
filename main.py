import json
import random
import string
import requests
import urllib3
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import asyncio
from httpx import post

app = FastAPI()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === Allow frontend access to safe routes ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict this to your frontend domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === In-memory list of printed tickets ===
printed_tickets = []

# === External API sender ===
def send_events(priority, label, value, resource, sub_resource, env, tower, prblm_type, origin, description):
    trigger_time = str(datetime.now().timestamp()).split('.')[0]

    URL = 'https://acnint50-api.eventops-aiops.com/produce?authid=MAIN'
    KEY = os.getenv("API_KEY")

    headers = {
        'x-api-key': KEY,
        'Content-Type': 'application/json'
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

# === Internal print endpoint (backend-only) ===
@app.post("/print_ticket_internal")
async def print_ticket_internal(ticket_number: str, description: str):
    ticket = {"ticket_number": ticket_number, "description": description}
    printed_tickets.append(ticket)

    print("=== Printing Ticket ===")
    print(f"Ticket Number: {ticket_number}")
    print(f"Description: {description}")
    print("=======================")

    # No "message" field
    return JSONResponse(content=ticket)

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

    # Send event to external API
    result = send_events(priority, label, value, resource, sub_resource, env, tower, prblm_type, origin, description)

    # Trigger internal print (frontend never calls this directly)
    try:
        await asyncio.to_thread(
            post,
            "http://localhost:8000/print_ticket_internal",
            params={
                "ticket_number": shortDescription,
                "description": description,
            },
        )
    except Exception as e:
        print("Error calling internal print:", e)

    return JSONResponse(content=result)

# === Public endpoint: list all printed tickets ===
@app.get("/get_printed_tickets")
async def get_printed_tickets():
    return JSONResponse(content={"tickets": printed_tickets})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
