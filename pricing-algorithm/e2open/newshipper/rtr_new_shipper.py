"""
* File: pricing-algorithm\e2open\newshipper\rtr_new_shipper.py
* Project: Omni-lvlp-pricing-algorithm
* Author: Bizcloud Experts
* Date: 2023-12-27
* Confidential and Proprietary
"""
import requests
import json
from pytz import timezone
from pyzipcode import ZipCodeDatabase
import os
import calendar
from datetime import datetime, timedelta
from libs.get_creds import get_creds
from libs.get_item_dynamodb import get_item
from libs.update_item_dynamodb import update_item

dynamoTable = os.environ['E2OPEN_NEW_SHIPPER_TABLE']

def parse_new_shipper_data(data):
    now = datetime.utcnow().replace(tzinfo=timezone('UTC'))
    now = now.strftime('%Y-%m-%dT%H:%M:%S%z')
    name = data['company']['name'].upper()
    duns = data['company']['duns'].upper()
    try:
        row = get_item(dynamoTable, duns)
        print(f"Record already exists for {name}, {duns}")
    except:
        update_item(dynamoTable, duns, company_name=name, company_duns=duns,
                    date_added=now)
        print(f"Added record for {name}, {duns}")
