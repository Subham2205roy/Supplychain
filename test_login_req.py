import requests

url = "https://supplychain-plum.vercel.app/api/login"
payload = {"email": "testuser99@test.com", "password": "Test1234!"}
response = requests.post(url, json=payload)

print(f"Status: {response.status_code}")
print("Headers:")
for k, v in response.headers.items():
    print(f"{k}: {v}")
    
print(f"Cookies: {response.cookies.get_dict()}")
