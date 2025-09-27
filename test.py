import requests 
url = "https://hackathon2025-dev.fpt.edu.vn/api/maps/get_active_map/" 
token = "28b8940a37ed20635f0d72dd1a555520" 
response = requests.get(url,params={"token": token}) 
print(response.status_code)
print(response.json())