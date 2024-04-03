from cgitb import text
import requests
import json
import traceback
def extract_text_from_json(json_data):
    try:
        # Extract the result from the JSON data
        result = json_data.get('result', [])
        
        # Iterate over each item in the result
        with open('Cloudkaptan.txt', 'a') as file:
            for item in result:
                # Extract the description from the item
                if(type(item)==str):
                    continue
                descriptionContainer = item.get('policyDetails', {})
                # bodyContainer = item.get('componentDescriptionB', {})
                if(type(descriptionContainer)==str):
                    continue
                title = item.get('policyName')
                description = descriptionContainer.get('en', [])
                # body = bodyContainer.get('en',[])
                # # Iterate over each description block
                for block in description:
                    # Extract the text from the description block
                    if(type(block)==str):
                        continue
                    textContainer = block.get('children', [{}])
                    # title = title.get('en',[])[0].get('children', [{}])[0].get('text', '')
                    # file.write(title + ':')
                    # print(title + ';\n')
                    if len(textContainer)>0:
                        file.write('\n'+title+':\n')
                    for text in textContainer:
                        file.write(text.get('text', ''))
                        print(text.get('text', ''))
                    # Write the text to the file
                # for block in body:
                #     # Extract the text from the description block
                #     if(type(block)==str):
                #         continue
                #     textContainer = block.get('children', [{}])
                #     print(title + ';\n')
                #     file.write('.')
                #     for text in textContainer:
                #         file.write(text.get('text', ''))
                #         print(text.get('text', ''))
                # file.write('\n')
    
    except Exception as e:
        stack_trace = traceback.format_exc()
        print(stack_trace)
        print(f"Error: {e}")


def retrieve_json_data(url):
    try:
        # Send a GET request to the URL
        response = requests.get(url)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the response content as JSON
            json_data = response.json()
            return json_data
        else:
            # If the request was not successful, print the error status code
            print(f"Error: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        # If there's an error with the request, print the exception
        print(f"Error: {e}")
        return None

# Example usage:
url = "https://sz09gjoh.api.sanity.io/v2024-03-06/data/query/production?query=*"  # Replace this with the URL of the site you want to retrieve JSON data from
json_data = retrieve_json_data(url)
extract_text_from_json(json_data)
if json_data:
    print('success')
else:
    print("Failed to retrieve JSON data.")

