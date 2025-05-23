from autogen.agentchat import AssistantAgent, ConversableAgent, UserProxyAgent
import json
import tempfile
from autogen.coding import LocalCommandLineCodeExecutor
# Configuration for the local LM Studio model
config_list = [
    {
        "model": "meta-llama-3.1-8b-instruct",
        "base_url": "http://localhost:1234/v1",
        "api_key": "NULL",
        "price": [0, 0]
    }
]

llm_config = {
    "config_list": config_list,
    "temperature": 0.0,
    "functions": [
        {
            "name": "lookup_flights",
            "description": "Retrieve flights from the database based on origin, destination, and date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "Departure city"},
                    "destination": {"type": "string", "description": "Arrival city"},
                    "date": {"type": "string", "description": "Travel date in YYYY-MM-DD format"}
                },
                "required": ["origin", "destination", "date"]
            }
        }
    ]
}

# Simulated flight database
flight_db = {
    "NYC-LON": [
        {"flight_id": "FL123", "from": "New York", "to": "London", "price": 500, "date": "2025-06-01"},
        {"flight_id": "FL124", "from": "New York", "to": "London", "price": 600, "date": "2025-06-02"}
    ],
    "LON-NYC": [
        {"flight_id": "FL125", "from": "London", "to": "New York", "price": 550, "date": "2025-06-01"}
    ]
}

# Booking Agent to handle flight lookup and booking
booking_agent = ConversableAgent(
    name="BookingAgent",
    system_message="You are a flight booking assistant. Use lookup_flights to retrieve flight data. Do NOT invent flight details. If no flights are found, inform the user. Ask for clarification if needed. Before confirming a booking, request the passenger's name, email, and phone number.",
    llm_config=llm_config,
    human_input_mode="NEVER",
    is_termination_msg=lambda msg: any(phrase in msg["content"].lower() for phrase in ["good bye", "goodbye", "exit"])
)
temp_dir = tempfile.TemporaryDirectory()
executor = LocalCommandLineCodeExecutor(
    timeout=10,  # Timeout for each code execution in seconds.
    work_dir=temp_dir.name,  # Use the temporary directory to store the code files.
)

# User Proxy Agent to simulate user requests
user_proxy = UserProxyAgent(
    name="User",
    #system_message="You are a user requesting a flight booking. Provide clear instructions like 'Book a flight from New York to London on 2025-06-01'.",
    llm_config=False,
    code_execution_config={"executor": executor},
    human_input_mode="ALWAYS",
)

# Function to simulate flight lookup (in a real system, this could call an API)
def lookup_flights(origin, destination, date):
    key = f"{origin[:3].upper()}-{destination[:3].upper()}"
    flights = flight_db.get(key, [])
    return [flight for flight in flights if flight["date"] == date]

# Register the lookup function with the BookingAgent
booking_agent.register_for_execution()(lookup_flights)

# Initiate the conversation
result = user_proxy.initiate_chat(
    booking_agent,
    message="Book a flight from New York to London on 2025-06-01",
    max_consecutive_auto_reply=1
)

# Print the conversation summary
print(json.dumps(result.summary, indent=2))