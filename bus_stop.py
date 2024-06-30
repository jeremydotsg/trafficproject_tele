import json

# Assuming you have a JSON file named 'data.json'
with open('datadump.json', 'r') as file:
    data = json.load(file)

# Now 'data' is a Python dictionary that contains the data from the JSON file.
print(data)
