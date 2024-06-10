"""
* File: pricing-algorithm\libs\greenscreens_api.py
* Project: Omni-lvlp-pricing-algorithm
* Author: Bizcloud Experts
* Date: 2023-12-27
* Confidential and Proprietary
"""
import requests
import os
from libs.zip_api import zip_code
from datetime import datetime
from pypostalcode import PostalCodeDatabase
from libs.get_creds import get_creds


def gs_fixed_prices(equipment, customer, origin_city, origin_state, origin_zip, origin_ct, dest_city, dest_state,
                    dest_zip, dest_ct):
    # call get_creds lib
    # authenticate gs api
    try:
        client_secret = get_creds(os.environ['GREENSCREENS_SECRET'])
    except:
        print("Failed to get Greenscreens secret")
    url = 'https://api.greenscreens.ai/v1/auth/token'
    greenscreen_headers = {'accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
    greenscreen_data = {'grant_type': 'client_credentials', 'client_id': 'livelogistics',
                        'client_secret': client_secret['greenscreens_secret']}
    try:
        response = requests.post(url, headers=greenscreen_headers, data=greenscreen_data)
    except:
        print("Failed to get greenscreens auth token")
    greenscreen_auth_data = response.json()

    time = datetime.now()
    current_time = time.strftime('%Y-%m-%dT%H:%M:%SZ')

    url = "https://api.greenscreens.ai/v1/pricing/tpl-pricing"
    payload = {"pickupDateTime": f"{current_time}",
               "transportType": f"{equipment}",
               "customerName": f"{customer}",
               "region": "CITY",
               "stops":
                   [
                       {"order": 0,
                        "address": {
                            "city": f"{origin_city}",
                            "state": f"{origin_state}",
                            "zip": f"{origin_zip}",
                            "country": f"{origin_ct}"}},
                       {"order": 1,
                        "address": {
                            "city": f"{dest_city}",
                            "state": f"{dest_state}",
                            "zip": f"{dest_zip}",
                            "country": f"{dest_ct}"}}
                   ],
               "currency": "USD"}
    headers = {
        'content-type': "application/json",
        'authorization': f"Bearer {greenscreen_auth_data['access_token']}"}

    response = requests.request("POST", url, headers=headers, json=payload)
    greenscreen_prediction_data = response.json()
    if greenscreen_prediction_data['priorityRule'] is None:
        return None
    else:
        target_rate = greenscreen_prediction_data['priorityRule']['rule']['effects']['setSellCost']['amount']
        return target_rate


def search_for_priority_rule(equipment, customer, origin_city, origin_state, origin_zip, origin_ct, dest_city, dest_state,
                             dest_zip, dest_ct):
    # call get_creds lib
    # authenticate gs api
    try:
        client_secret = {
            "greenscreens_secret": "e5ef7084-c9db-4104-9c14-c9125084f970"
        }
    except:
        print("Failed to get Greenscreens secret")
    url = 'https://api.greenscreens.ai/v1/auth/token'
    greenscreen_headers = {'accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
    greenscreen_data = {'grant_type': 'client_credentials', 'client_id': 'livelogistics',
                        'client_secret': client_secret['greenscreens_secret']}
    try:
        response = requests.post(url, headers=greenscreen_headers, data=greenscreen_data)
    except:
        print("Failed to get greenscreens auth token")
    greenscreen_auth_data = response.json()

    time = datetime.now()
    current_time = time.strftime('%Y-%m-%dT%H:%M:%SZ')

    url = "https://api.greenscreens.ai/v1/pricing/tpl-pricing"
    payload = {"pickupDateTime": f"{current_time}",
               "transportType": f"{equipment}",
               "customerName": f"{customer}",
               "region": "CITY",
               "stops":
                   [
                       {"order": 0,
                        "address": {
                            "city": f"{origin_city}",
                            "state": f"{origin_state}",
                            "zip": f"{origin_zip}",
                            "country": f"{origin_ct}"}},
                       {"order": 1,
                        "address": {
                            "city": f"{dest_city}",
                            "state": f"{dest_state}",
                            "zip": f"{dest_zip}",
                            "country": f"{dest_ct}"}}
                   ],
               "currency": "USD"}
    headers = {
        'content-type': "application/json",
        'authorization': f"Bearer {greenscreen_auth_data['access_token']}"}

    response = requests.request("POST", url, headers=headers, json=payload)
    greenscreen_prediction_data = response.json()
    #print(greenscreen_prediction_data)
    #return
    target_rate = dict()
    if greenscreen_prediction_data['priorityRule'] is not None:
        target_sell_rate = greenscreen_prediction_data['priorityRule']['rule']['effects']['setSellCost']
        if target_sell_rate is not None:
            target_sell_rate = greenscreen_prediction_data['priorityRule']['rule']['effects']['setSellCost']['amount']
            target_rate['final_sell_rate'] = target_sell_rate
        else:
            target_rate['final_sell_rate'] = None
        markup_perc = greenscreen_prediction_data['priorityRule']['rule']['effects']['percentageAdjustment']
        if markup_perc is not None:
            markup_perc = greenscreen_prediction_data['priorityRule']['rule']['effects']['percentageAdjustment']['percentage']
            target_rate['markup_perc'] = 1 + (markup_perc / 100)
        else:
            target_rate['markup_perc'] = None
        markup_flat = greenscreen_prediction_data['priorityRule']['rule']['effects']['flatAdjustment']
        if markup_flat is not None:
            markup_flat = greenscreen_prediction_data['priorityRule']['rule']['effects']['flatAdjustment']['amount']
            target_rate['markup_flat'] = markup_flat
        else:
            target_rate['markup_flat'] = None
    else:
        target_rate['final_sell_rate'] = None
        target_rate['markup_perc'] = None
        target_rate['markup_flat'] = None
    print(target_rate)
    return target_rate


def greenscreens_quote(originzip, origincity, originstate, destzip, destcity, deststate, pickupdate, equipment):
    # call get_creds lib
    # authenticate gs api
    try:
        client_secret = get_creds(os.environ['GREENSCREENS_SECRET'])
    except:
        print("Failed to get Greenscreens secret")

    url = 'https://api.greenscreens.ai/v1/auth/token'
    greenscreen_headers = {'accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
    greenscreen_data = {'grant_type': 'client_credentials', 'client_id': 'livelogistics',
                        'client_secret': client_secret['greenscreens_secret']}
    try:
        response = requests.post(url, headers=greenscreen_headers, data=greenscreen_data)
    except:
        print("Failed to get greenscreens auth token")

    greenscreen_auth_data = response.json()
    ### TODO ####
    #############
    ## NEED TO REINVESTIGATE TIMESTAMPS ##
    #############
    # format the pickup date

    pickupstr = str(pickupdate)
    if len(pickupstr) < 15:
        pickupstr = pickupstr + ' 15:00:00'
        pickup_object = datetime.strptime(pickupstr, '%m/%d/%Y %H:%M:%S')
        pickstr = str(pickup_object)
        pickd = pickstr.split(" ")[0]
        pickt = pickstr.split(" ")[1]
        pickdt = pickd + "T" + pickt + "Z"
        print(pickdt)
    else:
        # pickupstr = datetime.strptime(pickupstr, '%Y-%m-%dT%H:%M:%SZ')
        pickdt = pickupstr  # .strftime('%Y-%m-%dT%H:%M:%SZ')
        print(pickdt)

    oziplenth = len(originzip)
    dziplenth = len(destzip)

    # check if the zip is canadian
    # if (oziplenth > 5) and (dziplenth > 5):
    #    pcdb = PostalCodeDatabase()
    #    try:
    #        org_location = pcdb[originzip]
    #        org_city = org_location.city
    #        org_province = org_location.province

    #        dest_location = pcdb[destzip]
    #        dest_city = dest_location.city
    #        dest_province = dest_location.province

    # get gs rates for canadian zip
    #        second_url = "https://api.greenscreens.ai/v3/prediction/network-rates"
    #        payload = {"pickupDateTime":f"{pickdt}",
    #                                "transportType":f"{equipment}",
    #                                "stops":
    #                                    [
    #                                        {"order":0,
    #                                        "city":f"{org_city}",
    #                                        "state":f"{org_province}",
    #                                        "zip":f"{originzip}"},
    #                                        {"order":1,
    #                                        "city":f"{dest_city}",
    #                                        "state":f"{dest_province}",
    #                                        "zip":f"{destzip}"}
    #                                    ],
    #                                    "currency":"USD"}
    #        headers = {
    #                    'content-type': "application/json",
    #                    'authorization': f"Bearer {greenscreen_auth_data['access_token']}"
    #                    }

    #        try:
    #            response = requests.request("POST", second_url, headers=headers, json=payload)
    #        except:
    #            print("Failed to get Canadian Greenscreens rates")

    #        greenscreen_precition_data = response.json()

    # get live network rates
    #        third_url = "https://api.greenscreens.ai/v3/prediction/rates"
    #        try:
    #            response = requests.request("POST", third_url, headers=headers, json=payload)
    #        except:
    #            print("Failed to get Canadian live network rates")

    #        gs_live_data = response.json()

    #    except:
    #        greenscreen_precition_data = 'Not Available'
    #        gs_live_data = 'Not Available'
    # else is when the zip code is us
    # else:
    # format the us zip codes
    # ozip = int(originzip)
    # origin = zip_code(ozip)
    # dzip = int(destzip)
    # destination = zip_code(dzip)

    # get gs rates
    second_url = "https://api.greenscreens.ai/v3/prediction/network-rates"
    payload = {"pickupDateTime": f"{pickdt}",
               "transportType": f"{equipment}",
               "stops":
                   [
                       {"order": 0,
                        "city": f"{origincity}",
                        "state": f"{originstate}",
                        "zip": f"{originzip}"},
                       {"order": 1,
                        "city": f"{destcity}",
                        "state": f"{deststate}",
                        "zip": f"{destzip}"}
                   ],
               "currency": "USD"}
    headers = {
        'content-type': "application/json",
        'authorization': f"Bearer {greenscreen_auth_data['access_token']}"
    }

    try:
        response = requests.request("POST", second_url, headers=headers, json=payload)
    except:
        print("Failed to get Greenscreens rates")

    greenscreen_precition_data = response.json()

    # get live network rates
    third_url = "https://api.greenscreens.ai/v3/prediction/rates"
    try:
        response = requests.request("POST", third_url, headers=headers, json=payload)
    except:
        print("Failed to get Greenscreens rates")
    gs_live_data = response.json()

    # print(greenscreen_precition_data)
    # return gs_live_data

    # set distance and rate variables
    try:
        dist = greenscreen_precition_data["distance"]
        rate = greenscreen_precition_data["targetBuyRate"] * greenscreen_precition_data["distance"]
        live_rate = gs_live_data["targetBuyRate"] * greenscreen_precition_data["distance"]
    except:
        dist = 'Not Available'
        rate = 'Not Available'
        live_rate = 'Not Available'
    print(rate, dist, live_rate)
    return rate, dist, live_rate


def greenscreens_quote_w_fuel(originzip, origincity, originstate, destzip, destcity, deststate, pickupdate, equipment):
    # call get_creds lib
    # authenticate gs api
    try:
        client_secret = get_creds(os.environ['GREENSCREENS_SECRET'])
    except:
        print("Failed to get Greenscreens secret")

    url = 'https://api.greenscreens.ai/v1/auth/token'
    greenscreen_headers = {'accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
    greenscreen_data = {'grant_type': 'client_credentials', 'client_id': 'livelogistics',
                        'client_secret': client_secret['greenscreens_secret']}
    try:
        response = requests.post(url, headers=greenscreen_headers, data=greenscreen_data)
    except:
        print("Failed to get greenscreens auth token")

    greenscreen_auth_data = response.json()
    ### TODO ####
    #############
    ## NEED TO REINVESTIGATE TIMESTAMPS ##
    #############
    # format the pickup date

    pickupstr = str(pickupdate)
    if len(pickupstr) < 15:
        pickupstr = pickupstr + ' 15:00:00'
        pickup_object = datetime.strptime(pickupstr, '%m/%d/%Y %H:%M:%S')
        pickstr = str(pickup_object)
        pickd = pickstr.split(" ")[0]
        pickt = pickstr.split(" ")[1]
        pickdt = pickd + "T" + pickt + "Z"
        print(pickdt)
    else:
        # pickupstr = datetime.strptime(pickupstr, '%Y-%m-%dT%H:%M:%SZ')
        pickdt = pickupstr  # .strftime('%Y-%m-%dT%H:%M:%SZ')
        print(pickdt)

    oziplenth = len(originzip)
    dziplenth = len(destzip)

    # get gs rates
    second_url = "https://api.greenscreens.ai/v3/prediction/network-rates"
    payload = {"pickupDateTime": f"{pickdt}",
               "transportType": f"{equipment}",
               "stops":
                   [
                       {"order": 0,
                        "city": f"{origincity}",
                        "state": f"{originstate}",
                        "zip": f"{originzip}"},
                       {"order": 1,
                        "city": f"{destcity}",
                        "state": f"{deststate}",
                        "zip": f"{destzip}"}
                   ],
               "currency": "USD"}
    headers = {
        'content-type': "application/json",
        'authorization': f"Bearer {greenscreen_auth_data['access_token']}"
    }

    try:
        response = requests.request("POST", second_url, headers=headers, json=payload)
    except:
        print("Failed to get Greenscreens rates")

    greenscreen_precition_data = response.json()

    # get live network rates
    third_url = "https://api.greenscreens.ai/v3/prediction/rates"
    try:
        response = requests.request("POST", third_url, headers=headers, json=payload)
    except:
        print("Failed to get Greenscreens rates")
    gs_live_data = response.json()

    # print(greenscreen_precition_data)
    # return gs_live_data

    # set distance and rate variables
    try:
        dist = greenscreen_precition_data["distance"]
        rate = greenscreen_precition_data["targetBuyRate"] * greenscreen_precition_data["distance"]
        fuel = greenscreen_precition_data["fuelRate"] * greenscreen_precition_data["distance"]
        live_rate = gs_live_data["targetBuyRate"] * greenscreen_precition_data["distance"]
    except:
        dist = 'Not Available'
        rate = 'Not Available'
        fuel = 'Not Available'
        live_rate = 'Not Available'
    print(rate, dist, live_rate, fuel)
    return rate, dist, live_rate, fuel


def greenscreens_quote_utc_e2open(originzip, origincity, originstate, destzip, destcity, deststate, pickupdate,
                                  equipment):
    # call get_creds lib
    # authenticate gs api
    try:
        client_secret = get_creds(os.environ['GREENSCREENS_SECRET'])
    except:
        print("Failed to get Greenscreens secret")

    url = 'https://api.greenscreens.ai/v1/auth/token'
    greenscreen_headers = {'accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
    greenscreen_data = {'grant_type': 'client_credentials', 'client_id': 'livelogistics',
                        'client_secret': client_secret['greenscreens_secret']}
    try:
        response = requests.post(url, headers=greenscreen_headers, data=greenscreen_data)
    except:
        print("Failed to get greenscreens auth token")

    greenscreen_auth_data = response.json()

    # format the pickup date (NOTE: TIMESTAMP IN UTC)
    pickdt = pickupdate.strftime("%Y-%m-%dT%H:%M:%SZ")

    # get gs rates
    second_url = "https://api.greenscreens.ai/v3/prediction/network-rates"
    payload = {"pickupDateTime": f"{pickdt}",
               "transportType": f"{equipment}",
               "stops":
                   [
                       {"order": 0,
                        "city": f"{origincity}",
                        "state": f"{originstate}",
                        "zip": f"{originzip}"},
                       {"order": 1,
                        "city": f"{destcity}",
                        "state": f"{deststate}",
                        "zip": f"{destzip}"}
                   ],
               "currency": "USD"}
    headers = {
        'content-type': "application/json",
        'authorization': f"Bearer {greenscreen_auth_data['access_token']}"
    }

    try:
        response = requests.request("POST", second_url, headers=headers, json=payload)
    except:
        print("Failed to get Greenscreens rates")

    greenscreen_precition_data = response.json()

    # get live network rates
    third_url = "https://api.greenscreens.ai/v3/prediction/rates"
    try:
        response = requests.request("POST", third_url, headers=headers, json=payload)
    except:
        print("Failed to get Greenscreens rates")
    gs_live_data = response.json()

    # print(greenscreen_precition_data)
    # return gs_live_data

    # set distance and rate variables
    try:
        dist = greenscreen_precition_data["distance"]
        rate = greenscreen_precition_data["targetBuyRate"] * greenscreen_precition_data["distance"]
        fuel = greenscreen_precition_data["fuelRate"] * greenscreen_precition_data["distance"]
        live_rate = gs_live_data["targetBuyRate"] * greenscreen_precition_data["distance"]
    except:
        dist = 'Not Available'
        rate = 'Not Available'
        fuel = 'Not Available'
        live_rate = 'Not Available'
    print(rate, dist, live_rate, fuel)
    return rate, dist, live_rate, fuel


def get_rules(equipment, customer, origin_city, origin_state, origin_zip, origin_ct, dest_city, dest_state, dest_zip,
              dest_ct):
    try:
        client_secret = get_creds(os.environ['GREENSCREENS_SECRET'])
    except:
        print("Failed to get Greenscreens secret")

    url = 'https://api.greenscreens.ai/v1/auth/token'
    greenscreen_headers = {'accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
    greenscreen_data = {'grant_type': 'client_credentials', 'client_id': 'livelogistics',
                        'client_secret': client_secret['greenscreens_secret']}
    try:
        response = requests.post(url, headers=greenscreen_headers, data=greenscreen_data)
    except:
        print("Failed to get greenscreens auth token")

    greenscreen_auth_data = response.json()

    time = datetime.now()
    current_time = time.strftime('%Y-%m-%dT%H:%M:%SZ')

    url = "https://api.greenscreens.ai/v1/pricing/tpl-pricing"
    payload = {"pickupDateTime": f"{current_time}",
               "transportType": f"{equipment}",
               "customerName": f"{customer}",
               "region": "CITY",
               "stops":
                   [
                       {"order": 0,
                        "address": {
                            "city": f"{origin_city}",
                            "state": f"{origin_state}",
                            "zip": f"{origin_zip}",
                            "country": f"{origin_ct}"}},
                       {"order": 1,
                        "address": {
                            "city": f"{dest_city}",
                            "state": f"{dest_state}",
                            "zip": f"{dest_zip}",
                            "country": f"{dest_ct}"}}
                   ],
               "currency": "USD"}
    headers = {
        'content-type': "application/json",
        'authorization': f"Bearer {greenscreen_auth_data['access_token']}"}

    response = requests.request("POST", url, headers=headers, json=payload)

    greenscreen_prediction_data = response.json()
    #print(greenscreen_prediction_data)
    combo_adj = dict()
    combo_adj['flat'] = 0
    combo_adj['perc'] = 0

    # combination rules:
    if greenscreen_prediction_data['combinationRules'] is not None:
        for rule in range(len(greenscreen_prediction_data['combinationRules']['rules'])):
            # print(greenscreen_prediction_data['combinationRules']['rules'][rule]['effects'])
            if greenscreen_prediction_data['combinationRules']['rules'][rule]['effects']['percentageAdjustment'] is not None:
                combo_adj['perc'] = combo_adj['perc'] + \
                                    greenscreen_prediction_data['combinationRules']['rules'][rule]['effects'][
                                        'percentageAdjustment']['percentage']
            if greenscreen_prediction_data['combinationRules']['rules'][rule]['effects']['flatAdjustment'] is not None:
                combo_adj['flat'] = combo_adj['flat'] + \
                                    greenscreen_prediction_data['combinationRules']['rules'][rule]['effects'][
                                        'flatAdjustment']['amount']
    # print('Combination Rules:')
    # print(combo_adj)

    combo_perc = 1 + (combo_adj['perc'] / 100)

    rules = {
        "flat": combo_adj['flat'],
        "percent": combo_perc
    }
    print(rules)
    return rules


#get_rules("VAN", "KERRY INGREDIENTS AND FLAVORS", "CHICAGO", "IL", "60657", "US", "SOLON", "OH", "44139", "US")
