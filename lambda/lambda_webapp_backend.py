import json
import boto3
import time
from openlocationcode import encode, decode
from math import sin, cos, sqrt, atan2, radians
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')

def response(code, body, content_type='application/json'):
    print(body)
    return {
        'statusCode': code,
        'headers': {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,POST",
            "Content-type": content_type
        },
        'body': body
    }

def get_building(req):
    table = boto3.resource('dynamodb').Table('OpenCity')
    lat, lon, code = req['lat'], req['lon'], req['code']
    grid = code.split("+")[0] + "+"
    print("Requested buildings for %s" % code)
    items = table.query(
        KeyConditionExpression=Key('grid').eq(grid)
    )
    res = []
    for item in items['Items']:
        obj = {
            'county': item['county'],
            'fp': item['fp'],
            'ubid': item['ubid'],
            'state': item['state'],
            'height': float(item['height']),
            'area': float(item['area']),
            'grid': grid,
            'updated': float(item['updated']) if 'updated' in item else None
        }
        res.append(obj)

    return response(200, json.dumps(res))

def distance(lat1, lon1, lat2, lon2):
    # approximate radius of earth in km
    R = 6373.0

    lat1, lon1, lat2, lon2 = radians(lat1), radians(lon1), radians(lat2), radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c

def get_objects_nearby(req):
    table = boto3.resource('dynamodb').Table('OpenCity')
    lat, lon = float(req['lat']), float(req['lon'])
    res = []
    for length in [12, 11, 10, 8]:
        pc = encode(lat, lon, length)
        grid = "OSM:" + pc
        items = table.query(
            KeyConditionExpression=Key('grid').eq(grid),
            ProjectionExpression='lat, lon, tags,ubid'
        )
        nearby = []
        for item in items['Items']:
            if 'tags' in item and 'lat' in item and 'lon' in item:
                tags = item['tags']
                if 'name' in tags or 'amenity' in tags:
                    dist = distance(lat, lon, item['lat'], item['lon'])
                    tags['distance'] = dist
                    tags['lat'] = float(item['lat'])
                    tags['lon'] = float(item['lon'])
                    tags['ubid'] = item['ubid']
                    nearby.append(tags)
        if len(res) > 0:
            break
    nearby = sorted(nearby, key=lambda x: x['distance'])

    return response(200, json.dumps(nearby))

def add_tag(req, idenitiy):
    opencity = boto3.resource('dynamodb').Table('OpenCity')
    tags = boto3.resource('dynamodb').Table('UserTags')
    grid, ubid, key, value = req['grid'], req['ubid'], req['key'], req['value']
    if len(key) < 1 or len(value) < 1:
        return response(403, "empty key or value")

    timestamp = int(time.time() *1000000)
    tags.put_item(
        Item={
            'ubid': ubid,
            'timestamp': timestamp,
            'key': key,
            'value': value,
            'ip': idenitiy['sourceIp'],
            'ua': idenitiy['userAgent']
        }
    )
    opencity.update_item(
        Key={'ubid': ubid, 'grid': grid},
        UpdateExpression='SET updated = :ts',
        ExpressionAttributeValues={':ts': timestamp}
    )

    return response(200, json.dumps({"status": "OK"}))

def get_tags(req):
    tags = boto3.resource('dynamodb').Table('UserTags')
    ubid = req['ubid']
    print("Requested tags for %s" % ubid)
    items = tags.query(
        KeyConditionExpression=Key('ubid').eq(ubid)
    )
    res = []
    for item in items['Items']:
        item['timestamp'] = float(item['timestamp'])
        res.append(item)

    return response(200, json.dumps(res))

def lambda_handler(event, context):
    #    print(json.dumps(event))
    if event['requestContext']['httpMethod'] == 'OPTIONS':
        return response(200, "OK")
    method = event['path']
    if method.endswith("buildings/get"):
        return get_building(json.loads(event['body']))
    if method.endswith("objects/get"):
        return get_objects_nearby(json.loads(event['body']))
    if method.endswith("tags/add"):
        return add_tag(json.loads(event['body']), event['requestContext']['identity'])
    if method.endswith("tags/get"):
        return get_tags(json.loads(event['body']))
    else:
        return (400, "Not supported: " + method)



