import matplotlib.pyplot as plt
import json
from datetime import datetime

# Assuming you have a JSON file named 'data.json'
with open('datadump.json', 'r') as file:
    data = json.load(file)

# Dictionary to hold all nodes' data grouped by bus stop and service number
grouped_data = {}
interval_data = {}

# Mapping of bus stop codes to names
bus_stop_names = {
    "46101": "Woodlands Checkpoint (Exit)",
    "46211": "Johor Checkpoint (Entry)",
    "46219": "Johor Checkpoint (Exit)",
    "46109": "Woodlands Checkpoint (Entry)"
}

# Iterate over all nodes in the data
for node in data:
    # Parse the 'EstimatedArrival' and 'CreatedTime' into datetime objects
    estimated_arrival_str = node["fields"]["next_bus"]["EstimatedArrival"]
    created_time_str = node["fields"]["createdTime"]
    
    estimated_arrival = datetime.fromisoformat(estimated_arrival_str)
    created_time = datetime.fromisoformat(created_time_str)

    # Calculate the difference in minutes
    difference_in_minutes = (estimated_arrival - created_time).total_seconds() / 60

    # Extract other required fields
    bus_stop_code = node["fields"]["bus_stop"]
    service_no = node["fields"]["service_no"]
    next_bus_load = node["fields"]["next_bus"]["Load"]

    # Replace bus stop code with name using the mapping
    bus_stop = bus_stop_names.get(bus_stop_code, bus_stop_code)

    # Create a dictionary with the required information for this node
    node_data = {
        "CreatedTime": created_time_str,
        "EstimatedArrivalInMinutes": difference_in_minutes,
        "BusStop": bus_stop,
        "ServiceNo": service_no,
        "NextBusLoad": next_bus_load
    }


    # Use (bus_stop, service_no) as key for grouping
    key = (bus_stop, service_no)
    
    # If key is not in dictionary, initialize an empty list
    if key not in grouped_data:
        grouped_data[key] = []
    
    # Append this node's data to the list corresponding to the key
    grouped_data[key].append(node_data)

# Now, we can write each group to a separate JSON file
for key, nodes_data in grouped_data.items():
    bus_stop, service_no = key
    filename = f'data_bus_stop_{bus_stop}_service_{service_no}.json'
    
    with open(filename, 'w') as f:
        json.dump(nodes_data, f, indent=4)
