import json
import base64
import boto3
from decimal import *
from openlocationcode import encode, decode
from math import sin, cos, sqrt, atan2, radians

def distance(lat1, lon1, lat2, lon2):
    # approximate radius of earth in km
    R = 6373.0

    lat1, lon1, lat2, lon2 = radians(lat1), radians(lon1), radians(lat2), radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    table = dynamodb.Table('OpenCity')
    with table.batch_writer() as batch:
        items = dict()
        for record in event['Records']:
            payload = base64.b64decode(record['kinesis']['data'])
            #print(payload)
            obj = json.loads(payload.decode("utf-8"))
            obj['ubid'] = str(obj['hash'])
            for length in [8, 10, 11, 12]:
                grid = encode(obj['lat'], obj['lon'], length)
                obj['grid'] = "OSM:" + grid
                ca = decode(grid)
                lat, lon = ca.latitudeCenter, ca.longitudeCenter
                obj['distance'] = distance(lat, lon, obj['lat'], obj['lon'])
                o = json.loads(json.dumps(obj))
                for field in ['distance', 'lon', 'lat']:
                    o[field] = Decimal(str(o[field]))
                items[o['grid'] + o['hash']] = o
        for item in items.values():
            #print(item)
            batch.put_item(
                Item=item
            )
    print("Processed %d, %d distinct items" % (len(event['Records']), len(items)))
    # print("Decoded payload: " + obj)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
