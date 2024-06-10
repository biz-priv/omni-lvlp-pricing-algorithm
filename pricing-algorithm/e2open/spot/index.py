"""
* File: pricing-algorithm\e2open\spot\index.py
* Project: Omni-lvlp-pricing-algorithm
* Author: Bizcloud Experts
* Date: 2023-12-27
* Confidential and Proprietary
"""
from e2open_spot_market import get_new_spot_loads

def lambda_handler(event, context):
    print(event)