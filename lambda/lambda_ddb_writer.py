import json
import base64
import boto3
from decimal import *

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    table = dynamodb.Table('OpenCity')
    with table.batch_writer() as batch:
        items = dict()
        for record in event['Records']:
            payload = base64.b64decode(record['kinesis']['data'])
            obj = json.loads(payload.decode("utf-8"))
            for field in ['area', 'height', 'height_predict', 'lon', 'lat']:
                obj[field] = Decimal(str(obj[field]))
            items[obj['ubid']] = obj
        for item in items.values():
            # print(obj)
            batch.put_item(
                Item=item
            )
    print("Processed %d, %d distinct items" % (len(event['Records']), len(items)))
    # print("Decoded payload: " + obj)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
