from requests_html import HTMLSession

# Create an HTML Session
session = HTMLSession()

# Use the session to get the webpage
url = 'https://example.com'
response = session.get(url)

# Render the JavaScript
response.html.render()

# Extract data using CSS selectors
title = response.html.find('title', first=True).text
print(f'Title: {title}')

# Extract other data as needed
paragraphs = response.html.find('p')
for p in paragraphs:
    print(p.text)