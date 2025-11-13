import boto3
import uuid
import datetime
import json

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('user_access_logs')

def login_logger(event, context):
    try:
        # Handle both direct invocation and API Gateway
        if isinstance(event.get('body'), str):
            body = json.loads(event.get('body', '{}'))
        else:
            body = event.get('body', event)  # Direct invocation might not have 'body'
        
        username = body.get('username')
        if not username:
            raise ValueError("Username is required in the request body")
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps(f"Invalid request: {str(e)}")
        }
    
    # Get source IP - handle different event structures
    source_ip = 'unknown'
    try:
        # Try API Gateway HTTP API format
        if 'requestContext' in event and 'http' in event['requestContext']:
            source_ip = event['requestContext']['http']['sourceIp']
        # Try API Gateway REST API format
        elif 'requestContext' in event and 'identity' in event['requestContext']:
            source_ip = event['requestContext']['identity']['sourceIp']
        # Try direct invocation or other sources
        elif 'sourceIp' in event:
            source_ip = event['sourceIp']
    except Exception:
        # If all else fails, keep 'unknown'
        pass
    
    item_to_save = {
        'username': username,
        'timestamp': datetime.datetime.utcnow().isoformat() + "Z",
        'event_id': str(uuid.uuid4()),
        'event_type': 'USER_LOGIN_SUCCESS',
        'source_ip': source_ip
    }
    
    try:
        table.put_item(Item=item_to_save)
        return {
            'statusCode': 200,
            'body': json.dumps(f"Successfully logged event for user: {username}")
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error writing to DynamoDB: {str(e)}")
        }