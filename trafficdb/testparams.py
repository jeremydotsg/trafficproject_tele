'''
Created on 23 Jul 2024

@author: Jeremy
'''
import re

def has_params(pattern, chat_text):
    match = re.match(pattern, chat_text)
    if match:
        command, param = match.groups()
        is_process = True
        if param:
            has_param = True
            print("Param: " + param)
        print("Command: " + command)

pattern = r"\/(\w+)\s?([\w\s]*)"

chat_text = "weather"
print("Chat Text: " + chat_text)
has_params(pattern, chat_text)
match = re.findall(pattern, chat_text)
if match:
    print(match)

chat_text = "/weather"
print("Chat Text: " + chat_text)
has_params(pattern, chat_text)
match = re.findall(pattern, chat_text)
if match:
    print(match)

chat_text = "/weather 1"
print("Chat Text: " + chat_text)
has_params(pattern, chat_text)
match = re.findall(pattern, chat_text)
if match:
    print(match)
    
chat_text = "/weather 1 2"
print("Chat Text: " + chat_text)
has_params(pattern, chat_text)
match = re.findall(pattern, chat_text)
if match:
    print(match)

chat_text = "/weather 1 2 3"
print("Chat Text: " + chat_text)
has_params(pattern, chat_text)
match = re.findall(pattern, chat_text)
if match:
    print(match)
    
chat_text = "/weather ku ku ku"
print("Chat Text: " + chat_text)
has_params(pattern, chat_text)
match = re.findall(pattern, chat_text)
if match:
    print(match)
    

param_pattern = "^\d+(?: \d+)*$"
test_text = "12345"
print(test_text)
match = re.findall(param_pattern, test_text)
if match:
    print(match)
test_text = "1"
print(test_text)
match = re.findall(param_pattern, test_text)
if match:
    print(match)
test_text = "1 2"
print(test_text)
match = re.findall(param_pattern, test_text)
if match:
    print(match)
test_text = "1"
print(test_text)
match = re.findall(param_pattern, test_text)
if match:
    print(match)
test_text = "1 a"
print(test_text)
match = re.findall(param_pattern, test_text)
if match:
    print(match)

    