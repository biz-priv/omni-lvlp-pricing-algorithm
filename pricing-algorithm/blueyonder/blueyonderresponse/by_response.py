import boto3
import json
import os
import requests
import time
import base64
from libs.get_creds import get_creds
from libs.update_item_dynamodb import update_item

if os.environ['ENVIRONMENT'] == 'prod':
    from prod_config import *
else:
    from dev_config import *

cached_response_secret = None
cached_timestamp = None
dynamoTable = os.environ['PRICING_ALGO_DB_TABLE']

def blue_yonder_auth():
    global cached_response_secret
    global cached_timestamp
    now = int(time.time())

    if not cached_response_secret or not cached_timestamp:
        try:
            get_secrets = get_creds(os.environ['BLUE_YONDER_SECRETS'])
            blue_yonder_secrets = json.loads(get_secrets['blue_yonder_secrets'])
            blue_yonder_secrets['timestamp'] = int(blue_yonder_secrets['timestamp'])
            print("Checking token expiration")
            if now - blue_yonder_secrets['timestamp'] >= 6600:
                #we need to refresh the token every 2 hours
                try:
                    print("Refreshing token")
                    client_id = clientID
                    secret = blue_yonder_secrets['password']
                    url = tokenURL
                    concatenated = f"{client_id}:{secret}"
                    concat_bytes = concatenated.encode("ascii")
                    base64_bytes = base64.b64encode(concat_bytes)
                    b64_string = base64_bytes.decode("ascii")

                    headers = {"Authorization": f"Basic {b64_string}"}

                    print("Getting new token")
                    response = requests.post(url, headers=headers)
                    output = response.json()
                    cached_response_secret = output['access_token']

                    #update timestamp and token parameter
                    print("Putting new token in SSM")
                    ssmclient = boto3.client('ssm')
                    response = ssmclient.put_parameter(
                        Name = os.environ['BLUE_YONDER_SECRETS'],
                        Overwrite = True,
                        Value = json.dumps({
                            "password": blue_yonder_secrets['password'],
                            "timestamp": now,
                            "token": cached_response_secret
                        })
                    )
                    cached_timestamp = now
                    return cached_response_secret
                except Exception as e:
                    return ("Failed to rotate Blue Yonder token:", str(e))
            print("Using non-expired token")
            cached_response_secret = blue_yonder_secrets['token']
            return cached_response_secret
        except Exception as e:
            return ("Failed to get Blue Yonder Secrets:", str(e))
    return cached_response_secret

def blue_yonder_response(data):
    print(data['payload'])

    try:    
        url = responseURL
        #url = 'https://hooks.zapier.com/hooks/catch/15015295/3t9lwvw/'
        payload = data['payload']
        token = blue_yonder_auth()
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.post(url, headers=headers, data=payload)
        update_item(dynamoTable, data['apiHeader']['messageID'], NewQuote="Sent")
    except Exception as e:
        return ("An error occeurred:", str(e))
