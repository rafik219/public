import json
from kafka import KafkaConsumer

consumer = KafkaConsumer("test", bootstrap_servers=['192.168.5.104:9093','192.168.5.98:9092','192.168.5.43:9092'], group_id='velibGroup')
stations = {}

for msg in consumer:
    station = json.loads(msg.value.decode('utf-8'))
    contract = station.get('contract_name')
    number = station.get('number')
    available_bike_stands = station.get('available_bike_stands')
    address = station.get('address')
    
    if contract not in stations:
        stations[contract] = {}
    
    city_station = stations[contract]
    
    if number not in city_station:
        city_station[number] = available_bike_stands
    
#     print stations
#     print city_station, ' - ', contract
    
    diff = available_bike_stands - city_station[number]
    
    if diff != 0:
        print(u"{}{} {} ({})".format("+" if diff > 0 else '', diff, address, contract).encode('utf-8'))
    
# print("success !!")