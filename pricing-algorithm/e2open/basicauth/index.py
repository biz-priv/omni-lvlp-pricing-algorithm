"""
* File: pricing-algorithm\e2open\basicauth\index.py
* Project: Omni-lvlp-pricing-algorithm
* Author: Bizcloud Experts
* Date: 2023-12-27
* Confidential and Proprietary
"""
import base64
import os
import json
from libs.get_creds import get_creds

def lambda_handler(event, context):
    try:
        if "lambda_warmer" in event:
            print("function warm up")
            return {
                'statusCode': 200,
                'body': 'OK',        
            }
        # Get expected username and password from parameter store
        get_secrets = get_creds(os.environ['E2OPEN_SECRETS'])
        e2_open_secrets = json.loads(get_secrets['e2open_secrets'])
        expected_username = e2_open_secrets['username']
        expected_password = e2_open_secrets['password']

        auth_token = event['authorizationToken'].split(' ')[1]
        username, password = base64.b64decode(auth_token).decode('utf-8').split(':')

        if username.strip() == expected_username.strip() and password.strip() == expected_password.strip():
            return generate_policy('user', 'Allow', event['methodArn'])
        else:
            print("Exception 1")
            raise Exception('Unauthorized')
    except Exception as e:
        print(e)
        raise Exception ('Unauthorized')

def generate_policy(principal_id, effect, resource):
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{
                "Action": "execute-api:Invoke",
                "Effect": effect,
                "Resource": resource
            }]
        }
    }