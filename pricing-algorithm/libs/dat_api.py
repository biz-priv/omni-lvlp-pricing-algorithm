"""
* File: pricing-algorithm\libs\dat_api.py
* Project: Omni-lvlp-pricing-algorithm
* Author: Bizcloud Experts
* Date: 2023-12-27
* Confidential and Proprietary
"""
import requests
import os
import json
from libs.get_creds import get_creds

def dat_rateview(originzip, destzip, equipment):
    #org authentication API call
    #url = 'https://identity.api.nprod.dat.com/access/v1/token/organization'

    try:
        dat_secret = get_creds(os.environ['DAT_SECRET'])
    except:
        print("Failed to get DAT secret")

    url = 'https://identity.api.dat.com/access/v1/token/organization'
    un = 'Cwakefield'
    pw = dat_secret['dat_secret']

    account = 'chad+datapi@livelogisticscorp.com'

    headers = {'Content': 'application/json'}
    data = {"username": account,
        "password": pw}

    try:
        response = requests.post(url, json=data, headers=headers)
    except:
        print("Failed to get DAT ORG auth token")

    output = response.json()
    token = output['accessToken']


    #user auth API call
    #user_url = 'https://identity.api.nprod.dat.com/access/v1/token/user'
    user_url = 'https://identity.api.dat.com/access/v1/token/user'
    user_payload = {"username": f"{un}"}
    user_headers = {
        "Content": "application/json",
        "Authorization": f"Bearer {token}"}

    try:
        response = requests.post(user_url, json=user_payload, headers=user_headers)
    except:
        print("Failed to get DAT user auth token")


    user_output = response.json()
    user_token = user_output['accessToken']



    #rateview API call

    #rateview_url = 'https://analytics.api.nprod.dat.com/linehaulrates/v1/lookups'
    rateview_url = 'https://analytics.api.dat.com/linehaulrates/v1/lookups'
    rateview_headers = {"Content": "application/json",
        "Authorization": f"Bearer {user_token}"}

    payload = [{
            "origin": {
              "postalCode": f"{originzip}"
            },
            "destination": {
              "postalCode": f"{destzip}"
            },
            "rateType": "SPOT",
            "equipment": f"{equipment}",
            "includeMyRate": "false",
            "targetEscalation": {
              "escalationType": "SPECIFIC_AREA_TYPE_AND_SPECIFIC_TIME_FRAME",
              "specificTimeFrame": "7_DAYS",
              "specificAreaType": "MARKET_AREA"
            }
          }]

    try:
        response = requests.post(rateview_url, json=payload, headers=rateview_headers)
    except:
        print("Failed to get rates for 7 day time frame")

    try:
        rateview_output = response.json()
        json_response = rateview_output['rateResponses'][0]['response']
        mileage = json_response['rate']['mileage']
        num_of_reports = json_response['rate']['reports']
        num_of_companies = json_response['rate']['companies']
        esc_time = json_response['escalation']['timeframe']
        org_market = json_response['escalation']['origin']['name']
        dest_market = json_response['escalation']['destination']['name']
        fuel = json_response['rate']['averageFuelSurchargePerTripUsd']
        rv_rate = json_response['rate']['perTrip']['rateUsd'] + fuel


    except:
        rv_rate = 'Not Available'
        mileage = 'Not Available'
        num_of_reports = 'Not Available'
        num_of_companies = 'Not Available'
        esc_time = 'Not Available'
        org_market = 'Not Available'
        dest_market = 'Not Available'

    if (num_of_reports == 'Not Available') or (num_of_reports < 10):
        payload = [{
            "origin": {
              "postalCode": f"{originzip}"
            },
            "destination": {
              "postalCode": f"{destzip}"
            },
            "rateType": "SPOT",
            "equipment": f"{equipment}",
            "includeMyRate": "false",
            "targetEscalation": {
              "escalationType": "SPECIFIC_AREA_TYPE_AND_SPECIFIC_TIME_FRAME",
              "specificTimeFrame": "15_DAYS",
              "specificAreaType": "MARKET_AREA"
            }
          }]

        try:
            response = requests.post(rateview_url, json=payload, headers=rateview_headers)
        except:
            print("Failed to get rates for 15 day time frame")

        try:
            rateview_output = response.json()
            #print(rateview_output)
            json_response = rateview_output['rateResponses'][0]['response']
            mileage = json_response['rate']['mileage']
            num_of_reports = json_response['rate']['reports']
            num_of_companies = json_response['rate']['companies']
            esc_time = json_response['escalation']['timeframe']
            org_market = json_response['escalation']['origin']['name']
            dest_market = json_response['escalation']['destination']['name']
            fuel = json_response['rate']['averageFuelSurchargePerTripUsd']
            rv_rate = json_response['rate']['perTrip']['rateUsd'] + fuel


        except:
            rv_rate = 'Not Available'
            mileage = 'Not Available'
            num_of_reports = 'Not Available'
            num_of_companies = 'Not Available'
            esc_time = 'Not Available'
            org_market = 'Not Available'
            dest_market = 'Not Available'

        if (num_of_reports == 'Not Available') or (num_of_reports < 10):
            payload = [{
                "origin": {
                  "postalCode": f"{originzip}"
                },
                "destination": {
                  "postalCode": f"{destzip}"
                },
                "rateType": "SPOT",
                "equipment": f"{equipment}",
                "includeMyRate": "false",
                "targetEscalation": {
                  "escalationType": "SPECIFIC_AREA_TYPE_AND_SPECIFIC_TIME_FRAME",
                  "specificTimeFrame": "30_DAYS",
                  "specificAreaType": "MARKET_AREA"
                }
              }]

            try:
                response = requests.post(rateview_url, json=payload, headers=rateview_headers)
            except:
                print("Failed to get rate for 30 day time frame")

            try:
                rateview_output = response.json()
                json_response = rateview_output['rateResponses'][0]['response']
                mileage = json_response['rate']['mileage']
                num_of_reports = json_response['rate']['reports']
                num_of_companies = json_response['rate']['companies']
                esc_time = json_response['escalation']['timeframe']
                org_market = json_response['escalation']['origin']['name']
                dest_market = json_response['escalation']['destination']['name']
                fuel = json_response['rate']['averageFuelSurchargePerTripUsd']
                rv_rate = json_response['rate']['perTrip']['rateUsd'] + fuel


            except:
                rv_rate = 'Not Available'
                print('Error getting RateView rates')
                mileage = 'Not Available'
                num_of_reports = 'Not Available'
                num_of_companies = 'Not Available'
                esc_time = 'Not Available'
                org_market = 'Not Available'
                dest_market = 'Not Available'

    return rv_rate, mileage, num_of_reports, num_of_companies, esc_time, org_market, dest_market


def dat_rateview_w_fuel(originzip, destzip, equipment):
    #org authentication API call
    #url = 'https://identity.api.nprod.dat.com/access/v1/token/organization'

    try:
        dat_secret = get_creds(os.environ['DAT_SECRET'])
    except:
        print("Failed to get DAT secret")

    url = 'https://identity.api.dat.com/access/v1/token/organization'
    un = 'Cwakefield'
    pw = dat_secret['dat_secret']

    account = 'chad+datapi@livelogisticscorp.com'

    headers = {'Content': 'application/json'}
    data = {"username": account,
        "password": pw}

    try:
        response = requests.post(url, json=data, headers=headers)
    except:
        print("Failed to get DAT ORG auth token")

    output = response.json()
    token = output['accessToken']


    #user auth API call
    #user_url = 'https://identity.api.nprod.dat.com/access/v1/token/user'
    user_url = 'https://identity.api.dat.com/access/v1/token/user'
    user_payload = {"username": f"{un}"}
    user_headers = {
        "Content": "application/json",
        "Authorization": f"Bearer {token}"}

    try:
        response = requests.post(user_url, json=user_payload, headers=user_headers)
    except:
        print("Failed to get DAT user auth token")


    user_output = response.json()
    user_token = user_output['accessToken']



    #rateview API call

    #rateview_url = 'https://analytics.api.nprod.dat.com/linehaulrates/v1/lookups'
    rateview_url = 'https://analytics.api.dat.com/linehaulrates/v1/lookups'
    rateview_headers = {"Content": "application/json",
        "Authorization": f"Bearer {user_token}"}

    payload = [{
            "origin": {
              "postalCode": f"{originzip}"
            },
            "destination": {
              "postalCode": f"{destzip}"
            },
            "rateType": "SPOT",
            "equipment": f"{equipment}",
            "includeMyRate": "false",
            "targetEscalation": {
              "escalationType": "SPECIFIC_AREA_TYPE_AND_SPECIFIC_TIME_FRAME",
              "specificTimeFrame": "7_DAYS",
              "specificAreaType": "MARKET_AREA"
            }
          }]

    try:
        response = requests.post(rateview_url, json=payload, headers=rateview_headers)
    except:
        print("Failed to get rates for 7 day time frame")

    try:
        rateview_output = response.json()
        json_response = rateview_output['rateResponses'][0]['response']
        mileage = json_response['rate']['mileage']
        num_of_reports = json_response['rate']['reports']
        num_of_companies = json_response['rate']['companies']
        esc_time = json_response['escalation']['timeframe']
        org_market = json_response['escalation']['origin']['name']
        dest_market = json_response['escalation']['destination']['name']
        fuel = json_response['rate']['averageFuelSurchargePerTripUsd']
        rv_rate = json_response['rate']['perTrip']['rateUsd'] + fuel


    except:
        rv_rate = 'Not Available'
        mileage = 'Not Available'
        num_of_reports = 'Not Available'
        num_of_companies = 'Not Available'
        esc_time = 'Not Available'
        org_market = 'Not Available'
        dest_market = 'Not Available'

    if (num_of_reports == 'Not Available') or (num_of_reports < 10):
        payload = [{
            "origin": {
              "postalCode": f"{originzip}"
            },
            "destination": {
              "postalCode": f"{destzip}"
            },
            "rateType": "SPOT",
            "equipment": f"{equipment}",
            "includeMyRate": "false",
            "targetEscalation": {
              "escalationType": "SPECIFIC_AREA_TYPE_AND_SPECIFIC_TIME_FRAME",
              "specificTimeFrame": "15_DAYS",
              "specificAreaType": "MARKET_AREA"
            }
          }]

        try:
            response = requests.post(rateview_url, json=payload, headers=rateview_headers)
        except:
            print("Failed to get rates for 15 day time frame")

        try:
            rateview_output = response.json()
            #print(rateview_output)
            json_response = rateview_output['rateResponses'][0]['response']
            mileage = json_response['rate']['mileage']
            num_of_reports = json_response['rate']['reports']
            num_of_companies = json_response['rate']['companies']
            esc_time = json_response['escalation']['timeframe']
            org_market = json_response['escalation']['origin']['name']
            dest_market = json_response['escalation']['destination']['name']
            fuel = json_response['rate']['averageFuelSurchargePerTripUsd']
            rv_rate = json_response['rate']['perTrip']['rateUsd'] + fuel


        except:
            rv_rate = 'Not Available'
            mileage = 'Not Available'
            num_of_reports = 'Not Available'
            num_of_companies = 'Not Available'
            esc_time = 'Not Available'
            org_market = 'Not Available'
            dest_market = 'Not Available'

        if (num_of_reports == 'Not Available') or (num_of_reports < 10):
            payload = [{
                "origin": {
                  "postalCode": f"{originzip}"
                },
                "destination": {
                  "postalCode": f"{destzip}"
                },
                "rateType": "SPOT",
                "equipment": f"{equipment}",
                "includeMyRate": "false",
                "targetEscalation": {
                  "escalationType": "SPECIFIC_AREA_TYPE_AND_SPECIFIC_TIME_FRAME",
                  "specificTimeFrame": "30_DAYS",
                  "specificAreaType": "MARKET_AREA"
                }
              }]

            try:
                response = requests.post(rateview_url, json=payload, headers=rateview_headers)
            except:
                print("Failed to get rate for 30 day time frame")

            try:
                rateview_output = response.json()
                json_response = rateview_output['rateResponses'][0]['response']
                mileage = json_response['rate']['mileage']
                num_of_reports = json_response['rate']['reports']
                num_of_companies = json_response['rate']['companies']
                esc_time = json_response['escalation']['timeframe']
                org_market = json_response['escalation']['origin']['name']
                dest_market = json_response['escalation']['destination']['name']
                fuel = json_response['rate']['averageFuelSurchargePerTripUsd']
                rv_rate = json_response['rate']['perTrip']['rateUsd'] + fuel


            except:
                rv_rate = 'Not Available'
                print('Error getting RateView rates')
                mileage = 'Not Available'
                num_of_reports = 'Not Available'
                num_of_companies = 'Not Available'
                esc_time = 'Not Available'
                org_market = 'Not Available'
                dest_market = 'Not Available'
                fuel = 'Not Available'

    return rv_rate, mileage, num_of_reports, num_of_companies, esc_time, org_market, dest_market, fuel