import requests

url = 'https://132b-24-203-191-23.ngrok-free.app/pdf_data'
data = {'key1': 'value1', 'key2': 'value2'}
url2 = 'https://132b-24-203-191-23.ngrok-free.app/get_data'


response = requests.get(url2)

# Check the status code of the response
if response.status_code == 200:
    print('get request successful')
    print('Response:', response.text)
else:
    print('POST request failed')
   