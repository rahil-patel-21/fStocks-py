import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Initialize WebDriver
service = Service(executable_path=ChromeDriverManager().install())
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)

# Open a website
driver.get("")

element = driver.find_element_by_id('__NEXT_DATA__')
element_content = element.get_attribute('innerHTML')

try:
    data_json = json.loads(element_content)
except json.JSONDecodeError as e:
    print("Error decoding JSON:", e)
    data_json = None

# # Get the HTML content
# html_content = driver.page_source

# # Close the browser
# driver.quit()

# # Parse the HTML content with BeautifulSoup
# soup = BeautifulSoup(html_content, 'html.parser')

# # Function to convert BeautifulSoup parse tree to a dictionary
# def soup_to_dict(element):
#     if element.name is None:
#         return element.string
#     return {
#         element.name: {
#             "attributes": element.attrs,
#             "children": [soup_to_dict(child) for child in element.children if child.name or child.string.strip()]
#         }
#     }

# # Convert the BeautifulSoup object to a dictionary
# html_dict = soup_to_dict(soup)

# # Convert the dictionary to a JSON string
# html_json = json.dumps(html_dict, indent=2)

# # Save the JSON string to a file
# output_file = 'output.html.json'
# with open(output_file, 'w') as file:
#     file.write(html_json)
