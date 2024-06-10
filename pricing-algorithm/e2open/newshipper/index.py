"""
* File: pricing-algorithm\e2open\newshipper\index.py
* Project: Omni-lvlp-pricing-algorithm
* Author: Bizcloud Experts
* Date: 2023-12-27
* Confidential and Proprietary
"""
from rtr_new_shipper import parse_new_shipper_data

def lambda_handler(event, context):
    print(event)
    return parse_new_shipper_data(event)