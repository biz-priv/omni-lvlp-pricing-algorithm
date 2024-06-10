"""
* File: pricing-algorithm\formswebhook\index.py
* Project: Omni-lvlp-pricing-algorithm
* Author: Bizcloud Experts
* Date: 2023-12-27
* Confidential and Proprietary
"""
from formstack_webhook_parsing import get_data

def lambda_handler(event, context):
    print(event)
    data = event['data']
    return get_data(data)