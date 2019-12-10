import json
import boto3
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
            'area': float(item['area'])
        }
        res.append(obj)

    return response(200, json.dumps(res))

def lambda_handler(event, context):
    #    print(json.dumps(event))
    if event['requestContext']['httpMethod'] == 'OPTIONS':
        return response(200, "OK")
    method = event['path']
    if method.endswith("buildings/get"):
        return get_building(json.loads(event['body']))
    else:
        return (400, "Not supported: " + method)



