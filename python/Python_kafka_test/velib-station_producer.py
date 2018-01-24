import requests
import json
import time
from kafka import KafkaProducer


API_KEY = "4fb52ebdscd8d1fxbsAbac91x548706293578ccb414ff7"
url = "https://api.jcdecaux.com/vls/v1/stations?apiKey={}".format(API_KEY)
# print(url)

producer = KafkaProducer(bootstrap_servers=['192.168.5.104:9092','192.168.5.98:9092'])

while True:
    print("------------------------------")
    response = requests.get(url)
    stations = response.json()
    for station in stations:
        producer.send("test", json.dumps(station).encode('utf-8'))
        print("{} Produced {} station record".format(time.strftime("%Y-%m-%d %H:%M:%S"), station))
    time.sleep(1)


print("success !!")