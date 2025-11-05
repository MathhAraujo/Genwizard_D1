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

app = FastAPI()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    print(payload)

    data = requests.request("POST", str(URL), headers=headers, data=json.dumps(payload), verify=False)
    print(data.json())


@app.post("/print_ticket")
async def print_ticket(request: Request):
    data = await request.json()
    ticket_number = data.get("ticket_number")
    description = data.get("description")

    print(f"Ticket Number: {ticket_number}")
    print(f"Description: {description}")

    return JSONResponse(content={
        "message": "Ticket printed successfully",
        "ticket_number": ticket_number,
        "description": description
    })


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
    return JSONResponse(content=result)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
