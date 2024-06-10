"""
* File: pricing-algorithm\blueyonder\blueyonderrequest\index.py
* Project: Omni-lvlp-pricing-algorithm
* Author: Bizcloud Experts
* Date: 2023-12-27
* Confidential and Proprietary
"""
from by_request import blue_yonder_request

def lambda_handler(event, context):
    print(event)
    return blue_yonder_request(event)