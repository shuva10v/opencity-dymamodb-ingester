import json
import boto3

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    print(json.dumps(event))
    table = dynamodb.Table('OpenCity')

    return {
        'statusCode': 200,
        'headers': {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,POST"
        },
        'body': json.dumps('Hello from Lambda!')
    }
