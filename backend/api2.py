#hospital api 
import requests

url = "https://bhuvan-app1.nrsc.gov.in/api/api_proximity/curl_hos_pos_prox.php?theme=hospital&lat=16.27939453125&lon=80.58837890625&buffer=3000&token=xxxxxxxxxxxxxx"
params = {
    "theme": "hospital",  # or "post"
    "lat": "16.27939453125",
    "lon": "80.58837890625",
    "buffer": "3000",
    "token": "303b7fcc8c8916b80f09df7feb65d39802f809c4"
}
headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

response = requests.get(url, params=params, headers=headers)
print(response.json())

