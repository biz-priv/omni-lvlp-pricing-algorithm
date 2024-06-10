"""
* File: pricing-algorithm\s2q\s2q_suggested_rates.py
* Project: Omni-lvlp-pricing-algorithm
* Author: Bizcloud Experts
* Date: 2023-12-27
* Confidential and Proprietary
"""
import requests
import json
import os
from datetime import datetime
from libs.greenscreens_api import gs_fixed_prices, greenscreens_quote_w_fuel
from libs.dat_api import dat_rateview_w_fuel
from libs.get_creds import get_creds


def get_citystate_from_zip(zip):
    goog_api = 'AIzaSyDod39KtNuE6ufiFSLrpC83hK48jwCka1A'
    loc_response = requests.get(
        f'https://maps.googleapis.com/maps/api/geocode/json?components=postal_code:{zip}&key={goog_api}')
    output = loc_response.json()
    city = ''
    state = ''
    country = ''
    for component in range(len(output['results'][0]['address_components'])):
        if output['results'][0]['address_components'][component]['types'] == ['locality', 'political']:
            city = output['results'][0]['address_components'][component]['long_name']
        if output['results'][0]['address_components'][component]['types'] == ['administrative_area_level_1',
                                                                              'political']:
            state = output['results'][0]['address_components'][component]['short_name']
        if output['results'][0]['address_components'][component]['types'] == ['country', 'political']:
            country = output['results'][0]['address_components'][component]['short_name']
    return city, state, country


def get_zip_from_citystate(city, state):
    goog_api = 'AIzaSyDod39KtNuE6ufiFSLrpC83hK48jwCka1A'
    loc_response = requests.get(
        f'https://maps.googleapis.com/maps/api/geocode/json?address={city},%2B{state}&key={goog_api}')
    output = loc_response.json()
    zip = ''
    add_comps = output['results'][0]['address_components']
    for component in range(len(add_comps)):
        if add_comps[component]['types'] == ['postal_code']:
            zip = add_comps[component]['short_name']
    return zip


def generate_suggested_rate_for_s2q(data):
    # get beginning object data
    try:
        requester = data['apiHeader']['requestingCompanyCode']
        if requester == "BestBuy":
            customer = "Best Buy"
        else:
            customer = "Unknown"
    except:
        customer = "Unknown"
    try:
        requester_domain = data['apiHeader']['requestingCompanyDomain']
    except:
        requester_domain = "Unknown"

    try:
        request_timestamp = data['apiHeader']['timestamp']
    except:
        rejection_payload = {
            "responseStatus": "Rejected",
            "rejectionDescription": "Malformed API Header object",
            "rejectionCode": "1"
        }
        rejection_payload = json.dumps(rejection_payload)
        raise Exception("403: " + rejection_payload)
    # get preliminary load data
    try:
        #cost_type = data['costType']
        service_type = data['serviceType']
        equipment = data['equipmentType']
        commodity = data['commodity']
        team = data['team']
        load_value = data['loadValue']
    except:
        rejection_payload = {
            "responseStatus": "Rejected",
            "rejectionDescription": "Missing Required Load Info",
            "rejectionCode": "2"
        }
        rejection_payload = json.dumps(rejection_payload)
        raise Exception("403: " + rejection_payload)
    # get stop data
    origin_stop_info = {}
    dest_stop_info = {}
    try:
        number_of_stops = len(data['stops'])
        for stop in range(len(data['stops'])):
            if data['stops'][stop]['sequence'] == 1:
                try:
                    origin_stop_info['city'] = data['stops'][stop]['city']
                    origin_stop_info['state'] = data['stops'][stop]['state']
                except:
                    origin_stop_info['city'] = None
                    origin_stop_info['state'] = None
                try:
                    origin_stop_info['country'] = data['stops'][stop]['country']
                except:
                    origin_stop_info['country'] = "US"
                try:
                    origin_stop_info['zip'] = data['stops'][stop]['zipCode']
                except:
                    origin_stop_info['zip'] = None
                if origin_stop_info['city'] is None and origin_stop_info['state'] is None and origin_stop_info[
                    'zip'] is None:
                    rejection_payload = {
                        "responseStatus": "Rejected",
                        "rejectionDescription": "Missing Required Origin Stop Info",
                        "rejectionCode": "4"
                    }
                    rejection_payload = json.dumps(rejection_payload)
                    raise Exception("403: " + rejection_payload)
                elif origin_stop_info['city'] is None and origin_stop_info['state'] is None:
                    city, state, country = get_citystate_from_zip(origin_stop_info['zip'])
                    origin_stop_info['city'] = city
                    origin_stop_info['state'] = state
                    origin_stop_info['country'] = country
                elif origin_stop_info['zip'] is None:
                    origin_stop_info['zip'] = get_zip_from_citystate(origin_stop_info['city'],
                                                                     origin_stop_info['state'])
                else:
                    pass
                origin_stop_info['stop_type'] = data['stops'][stop]['stopType']
                origin_stop_info['early_pick'] = data['stops'][stop]['earliestPick']
                try:
                    origin_stop_info['late_pick'] = data['stops'][stop]['latestPick']
                except:
                    origin_stop_info['late_pick'] = None
            if data['stops'][stop]['sequence'] == number_of_stops:
                try:
                    dest_stop_info['city'] = data['stops'][stop]['city']
                    dest_stop_info['state'] = data['stops'][stop]['state']
                except:
                    dest_stop_info['city'] = None
                    dest_stop_info['state'] = None
                try:
                    dest_stop_info['country'] = data['stops'][stop]['country']
                except:
                    dest_stop_info['country'] = "US"
                try:
                    dest_stop_info['zip'] = data['stops'][stop]['zipCode']
                except:
                    dest_stop_info['zip'] = None
                if dest_stop_info['city'] is None and dest_stop_info['state'] is None and dest_stop_info['zip'] is None:
                    rejection_payload = {
                        "responseStatus": "Rejected",
                        "rejectionDescription": "Missing Required Destination Stop Info",
                        "rejectionCode": "5"
                    }
                    rejection_payload = json.dumps(rejection_payload)
                    raise Exception("403: " + rejection_payload)
                elif dest_stop_info['city'] is None and dest_stop_info['state'] is None:
                    city, state, country = get_citystate_from_zip(dest_stop_info['zip'])
                    dest_stop_info['city'] = city
                    dest_stop_info['state'] = state
                    dest_stop_info['country'] = country
                elif dest_stop_info['zip'] is None:
                    dest_stop_info['zip'] = get_zip_from_citystate(dest_stop_info['city'], dest_stop_info['state'])
                else:
                    pass
                dest_stop_info['stop_type'] = data['stops'][stop]['stopType']
    except:
        rejection_payload = {
            "responseStatus": "Rejected",
            "rejectionDescription": "Missing Required Stop Info",
            "rejectionCode": "3"
        }
        rejection_payload = json.dumps(rejection_payload)
        raise Exception("403: " + rejection_payload)

    # get some optional data
    try:
        max_temp = data['tempMax']
        min_temp = data['tempMin']
    except:
        max_temp = None
        min_temp = None
    try:
        distance = data['distance']
        weight = data['weight']
    except:
        distance = None
        weight = None

    # check for fixed price greenscreens
    fixed_rate = gs_fixed_prices(equipment, customer, origin_stop_info['city'], origin_stop_info['state'],
                                 origin_stop_info['zip'],
                                 origin_stop_info['country'], dest_stop_info['city'], dest_stop_info['state'],
                                 dest_stop_info['zip'],
                                 dest_stop_info['country'])
    target_rate = {}
    if fixed_rate is None:
        gs_network_rate, dist, live_rate, gs_fuel = greenscreens_quote_w_fuel(origin_stop_info['zip'],
                                                                              origin_stop_info['city'],
                                                                              origin_stop_info['state'],
                                                                              dest_stop_info['zip'],
                                                                              dest_stop_info['city'],
                                                                              dest_stop_info['state'],
                                                                              origin_stop_info['early_pick'], equipment)
        rv_rate, mileage, num_of_reports, num_of_companies, esc_time, org_market, dest_market, dat_fuel = dat_rateview_w_fuel(
            origin_stop_info['zip'],
            dest_stop_info['zip'], equipment)
        #if cost_type == "AllIn":
        #    print("check if DAT exists")
        #    if rv_rate != "Not Available":
        #        print("add fuel to DAT")
        try:
            rv_rate_w_fuel = rv_rate + (mileage * dat_fuel)
        except:
            rv_rate_w_fuel = "Not Available"
        #    else:
        #        pass
        #elif cost_type == "Linehaul":
        #    print("check if GS exists")
        #    if gs_network_rate != "Not Avaliable":
        try:
            gs_network_rate_wout_fuel = gs_network_rate - gs_fuel
        except:
            gs_network_rate_wout_fuel = "Not Available"
        #    print("remove fuel from GS")
        #else:
        #    pass

        #ALLIN, INCLUDING FUEL
        if rv_rate_w_fuel == "Not Available" and gs_network_rate == "Not Available":
            target_rate['allin'] = None
        elif rv_rate_w_fuel == "Not Available":
            target_rate['allin'] = (gs_network_rate * 1.11)
        elif gs_network_rate == "Not Available":
            target_rate['allin'] = (rv_rate_w_fuel * 1.11)
        else:
            target_rate['allin'] = (min(rv_rate_w_fuel, gs_network_rate) * 1.11)

        #LINEHAUL, EXCLUDING FUEL
        if rv_rate == "Not Available" and gs_network_rate_wout_fuel == "Not Available":
            target_rate['linehaul'] = None
        elif rv_rate == "Not Available":
            target_rate['linehaul'] = (gs_network_rate_wout_fuel * 1.11)
        elif gs_network_rate_wout_fuel == "Not Available":
            target_rate['linehaul'] = (rv_rate * 1.11)
        else:
            target_rate['linehaul'] = (min(rv_rate, gs_network_rate_wout_fuel) * 1.11)
    else:
        target_rate['allin'] = fixed_rate
        target_rate['linehaul'] = fixed_rate

    returned_payload = {
        "responseStatus": "Returned",
        "rates": [
            {
                "costType": "AllIn",
                "targetRate": round(target_rate['allin']),
                "targetHighRate": round(target_rate['allin'] * 1.04),
                "targetLowRate": round(target_rate['allin'] * 0.96),
            },
            {
                "costType": "Linehaul",
                "targetRate": round(target_rate['linehaul']),
                "targetHighRate": round(target_rate['linehaul'] * 1.04),
                "targetLowRate": round(target_rate['linehaul'] * 0.96),
            }
        ]
    }
    returned_payload = json.dumps(returned_payload)
    print(returned_payload)
    return returned_payload
