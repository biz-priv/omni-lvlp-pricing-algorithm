"""
* File: pricing-algorithm\e2open\rtr\index.py
* Project: Omni-lvlp-pricing-algorithm
* Author: Bizcloud Experts
* Date: 2023-12-27
* Confidential and Proprietary
"""
from e2open_quoting import parse_e2open

# def lambda_handler(event, context):
#     print(event)
#     return parse_e2open(event)

def lambda_handler(event, context): 
    if "lambda_warmer" in event:
        print("function warm up")
        return {
            'statusCode': 200,
            'body': 'OK',        
        }
    else:
        return parse_e2open(event)