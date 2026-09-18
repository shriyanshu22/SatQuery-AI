import requests

url2 = 'http://127.0.0.1:8000/api/v1/health'
url3 = 'http://127.0.0.1:8000/api/v1/upload'
url4 = 'http://127.0.0.1:8000/api/v1/query'

headers = {
    'Origin': 'http://localhost:5173',
    'Access-Control-Request-Method': 'POST',
    'Access-Control-Request-Headers': 'content-type'
}

print('1. OPTIONS /api/v1/upload')
res_opt3 = requests.options(url3, headers=headers)
print(f'Status: {res_opt3.status_code}, CORS: {res_opt3.headers.get("Access-Control-Allow-Origin")}')

print('2. OPTIONS /api/v1/query')
res_opt4 = requests.options(url4, headers=headers)
print(f'Status: {res_opt4.status_code}, CORS: {res_opt4.headers.get("Access-Control-Allow-Origin")}')
