"""
* File: pricing-algorithm\webservice\index.py
* Project: Omni-lvlp-pricing-algorithm
* Author: Bizcloud Experts
* Date: 2023-12-27
* Confidential and Proprietary
"""
from generate_rates import generate_rate
#from generate_ratesv2 import generate_ratev2

def lambda_handler(event, context):
    print(event)
    return generate_rate(event)