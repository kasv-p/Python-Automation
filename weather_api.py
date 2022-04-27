import requests

API_KEY = 'befefbd8b1bd0eea891ab7191df87cbf'
BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'
city = 'chennai'
request_url = f"{BASE_URL}?appid={API_KEY}&q={city}"
response = requests.get(request_url)

if response.status_code == 200:
    data = response.json()
    print('weather -',data['weather'][0]['description'])
    print('temparature -',round(data['main']['temp']-273.15,2),'celcius')
else: print("Fix The Bug")
