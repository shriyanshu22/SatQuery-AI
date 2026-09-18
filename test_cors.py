import requests

url1 = 'http://127.0.0.1:8000/health'
url2 = 'http://127.0.0.1:8000/api/v1/health'

headers = {'Origin': 'http://localhost:5173'}

print('1. GET /health')
res1 = requests.get(url1, headers=headers)
print(f'Status: {res1.status_code}, CORS: {res1.headers.get("Access-Control-Allow-Origin")}')

print('2. OPTIONS /health')
res_opt1 = requests.options(url1, headers=headers)
print(f'Status: {res_opt1.status_code}, CORS: {res_opt1.headers.get("Access-Control-Allow-Origin")}')

print('3. OPTIONS /api/v1/health')
res_opt2 = requests.options(url2, headers=headers)
print(f'Status: {res_opt2.status_code}, CORS: {res_opt2.headers.get("Access-Control-Allow-Origin")}')

print('4. GET /api/v1/health')
res2 = requests.get(url2, headers=headers)
print(f'Status: {res2.status_code}, CORS: {res2.headers.get("Access-Control-Allow-Origin")}')
