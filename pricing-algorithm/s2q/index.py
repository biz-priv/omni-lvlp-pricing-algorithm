"""
* File: pricing-algorithm\s2q\index.py
* Project: Omni-lvlp-pricing-algorithm
* Author: Bizcloud Experts
* Date: 2023-12-27
* Confidential and Proprietary
"""
from s2q_suggested_rates import generate_suggested_rate_for_s2q

def lambda_handler(event, context):
    print(event)
    return generate_suggested_rate_for_s2q(event)