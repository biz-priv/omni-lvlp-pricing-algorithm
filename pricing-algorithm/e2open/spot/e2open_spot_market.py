"""
* File: pricing-algorithm\e2open\spot\e2open_spot_market.py
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
from libs.greenscreens_api import gs_fixed_prices, greenscreens_quote_utc_e2open, get_rules, search_for_priority_rule
from libs.dat_api import dat_rateview_w_fuel
from libs.get_creds import get_creds
from libs.update_item_dynamodb import update_item
from libs.get_item_dynamodb import get_item
from libs.send_html_email import send_html_email


dynamoTable = os.environ['E2OPEN_SPOT_TABLE']
# dynamoTable2 = os.environ['E2OPEN_NEW_SHIPPER_TABLE']

# NOTE: ALWAYS ONLY LINEHAUL

# if os.environ['ENVIRONMENT'] == 'prod':
#     from prod_config import *
# else:
#     from dev_config import *


def convert_timestring_to_datetime(timestamp):
    # incoming datetime format is "2021-01-15T15:00:00-05:00"
    new_time = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S%z')
    new_time_utc = new_time.astimezone(timezone('UTC'))
    return new_time_utc


def geocode_w_latlng(lat, long):
    goog_api = 'AIzaSyDod39KtNuE6ufiFSLrpC83hK48jwCka1A'
    loc_response = requests.get(
        f'https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{long}&key={goog_api}')
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


def get_citystate_from_zip(zip):
    goog_api = 'AIzaSyDod39KtNuE6ufiFSLrpC83hK48jwCka1A'
    loc_response = requests.get(
        f'https://maps.googleapis.com/maps/api/geocode/json?components=postal_code:{zip}&key={goog_api}')
    output = loc_response.json()
    city = ''
    state = ''
    country = ''
    if output['status'] == "ZERO_RESULTS":
        zcdb = ZipCodeDatabase()
        r = zcdb[zip]
        # print(r.city)
        lat = r.latitude
        long = r.longitude
        city, state, country = geocode_w_latlng(lat, long)
    else:
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

    if zip == '':
        zcdb = ZipCodeDatabase()
        zip_data = zcdb.find_zip(city=f"{city}")
        for entry in range(len(zip_data)):
            if zip_data[entry].state == state:
                zip = zip_data[entry].zip
    return zip


def send_spot_rate_to_e2open(load_id, payload):
    url = f"https://orange-sandbox-tms-api.e2open.com/tmsapi/v2/spotmarket/load/{load_id}/offer/"
    username = 'SpotTestLVLP'
    password = 'r-GAsCsVQgh5sM0'
    response = requests.post(url, auth=(username, password), json=payload)
    return response.status_code


def get_new_spot_loads():
    now = datetime.utcnow().replace(tzinfo=timezone('UTC'))
    now_unix = calendar.timegm(now.utctimetuple())
    url = 'https://orange-sandbox-tms-api.e2open.com/tmsapi/v2/spotmarket/'
    username = 'SpotTestLVLP'
    password = 'r-GAsCsVQgh5sM0'
    # shipper_name = 'PSG API TEST COMPANY'
    # duns = '123456789'

    response = requests.get(url, auth=(username, password))

    loads = response.json()['loads']

    for load in range(len(loads)):
        ####################
        ## GET BASIC INFO
        ####################
        load_id = loads[load]['id']
        shipper_name = loads[load]['shipper_name'].upper()
        num_of_stops = loads[load]['number_stops']

        ####################
        ## GET BASIC INFO
        ####################
        # determine customer name
        if shipper_name in ["KEN'S FOODS"]:
            customer = 'KENS FOODS INC.'
        elif shipper_name in ['NUTRABOLT']:
            customer = 'Nutrabolt'
        else:
            customer = ''

        ####################
        ## GET STOP INFO
        ####################
        stops = loads[load]['stops']
        for stop in range(len(stops)):
            if stops[stop]['sequence_number'] == 0:
                # incoming datetime format is "2021-01-15T15:00:00-05:00"
                pickup_window_start = stops[stop]['plan_date_start']
                pickup_window_start = convert_timestring_to_datetime(pickup_window_start)
                pickup_window_end = stops[stop]['plan_date_end']
                pickup_window_end = convert_timestring_to_datetime(pickup_window_end)
                pickup_stop_name = stops[stop]['location']['name']
                pickup_address = stops[stop]['location']['address1']
                pickup_city = stops[stop]['location']['city']
                pickup_state = stops[stop]['location']['state']
                pickup_country = stops[stop]['location']['country']
                try:
                    pickup_zip = stops[stop]['location']['postalCode']
                except:
                    pickup_zip = get_zip_from_citystate(pickup_city, pickup_state)
                    if stops[stop]['drop_trailer'] is False:
                        live_pick = 1
                    else:
                        live_pick = 0
            if stops[stop]['sequence_number'] == len(stops) - 1:
                # incoming datetime format is "2021-01-15T15:00:00-05:00"
                delivery_window_start = stops[stop]['plan_date_start']
                delivery_window_start = convert_timestring_to_datetime(delivery_window_start)
                delivery_window_end = stops[stop]['plan_date_end']
                delivery_window_end = convert_timestring_to_datetime(delivery_window_end)
                delivery_stop_name = stops[stop]['location']['name']
                delivery_address = stops[stop]['location']['address1']
                delivery_city = stops[stop]['location']['city']
                delivery_state = stops[stop]['location']['state']
                delivery_country = stops[stop]['location']['country']
                try:
                    delivery_zip = stops[stop]['location']['postalCode']
                except:
                    delivery_zip = get_zip_from_citystate(delivery_city, delivery_state)
                if stops[stop]['drop_trailer'] is False:
                    live_del = 1
                else:
                    live_del = 0

        ####################
        ## GET OTHER INFO
        ####################
        equipment = loads[load]['equipment'][0]['type'].upper()  # VAN, REEFER, BULK, FLATBED, CONTAINER, OTHER
        hazmat = loads[load]['hazmat']
        low_offer = loads[load]['low_offer']

        ####################
        ## DETERMINE QUALIFYING INFO
        ####################
        if num_of_stops <= 2:
            under_max_stops = 1
        else:
            under_max_stops = 0
        if equipment in ["VAN", "FLATBED", "REEFER"]:
            is_v_or_f_or_r = 1
        else:
            is_v_or_f_or_r = 0
        lead_time = pickup_window_start - now
        lead_time = lead_time.total_seconds() / 3600
        if lead_time > 24:
            not_same_day = 1
        else:
            not_same_day = 0
        fourteen_days_lead = pickup_window_start - now
        fourteen_days_lead = fourteen_days_lead.total_seconds() / 86400
        if fourteen_days_lead >= 14:
            under_fourteen_days_lead = 0
        else:
            under_fourteen_days_lead = 1
        if hazmat is True:
            not_dangerous = 0
        else:
            not_dangerous = 1
        if pickup_window_start <= delivery_window_start:
            stops_in_sequence = 1
        else:
            stops_in_sequence = 0
        if live_pick * live_del > 0:
            live = 1
        else:
            live = 0

        eligibility = under_max_stops * is_v_or_f_or_r * not_same_day * under_fourteen_days_lead * not_dangerous * stops_in_sequence * live

        if eligibility == 0:
            print(
                f"""Ineligible: 2 Stops: {under_max_stops}; Equipment: {is_v_or_f_or_r}; Not Same Day: {not_same_day};
                    Within 14 Days: {under_fourteen_days_lead}; Not Dangerous: {not_dangerous}; Stops in Sequence: {stops_in_sequence};
                    Live pick/del: {live}"""
            )
        else:
            print(
                f"""Eligible: 2 Stops: {under_max_stops}; Equipment: {is_v_or_f_or_r}; Not Same Day: {not_same_day};
                    Within 14 Days: {under_fourteen_days_lead}; Not Dangerous: {not_dangerous}; Stops in Sequence: {stops_in_sequence};
                    Live pick/del: {live}"""
            )
            ####################
            ## GENERATE RATE
            ####################
            # look for priority rules
            priority_rules = search_for_priority_rule(equipment, customer, pickup_city, pickup_state, pickup_zip,
                                                      pickup_country,
                                                      delivery_city, delivery_state, delivery_zip, delivery_country)
            if priority_rules['final_sell_rate'] is None:
                gs_network_rate, gs_dist, gs_live_rate, gs_fuel = greenscreens_quote_utc_e2open(pickup_zip, pickup_city,
                                                                                                pickup_state,
                                                                                                delivery_zip,
                                                                                                delivery_city,
                                                                                                delivery_state,
                                                                                                pickup_window_start,
                                                                                                equipment)
                dat_rate, dat_mileage, dat_num_of_reports, dat_num_of_companies, dat_esc_time, dat_org_market, dat_dest_market, dat_fuel = dat_rateview_w_fuel(
                    pickup_zip, delivery_zip, equipment)
                gs_allin = gs_network_rate
                print(f"Greenscreens All-In: {gs_allin}")
                dat_allin = dat_rate - dat_fuel
                print(f"DAT All-In: {dat_allin}")
                rules = dict()
                rules = {
                    "percent": 0,
                    "flat": 0
                }
                if priority_rules['markup_perc'] is not None:
                    rules['percent'] = priority_rules['markup_perc']
                elif priority_rules['markup_flat'] is not None:
                    rules['flat'] = priority_rules['markup_flat']
                else:
                    rules = get_rules(equipment, customer, pickup_city, pickup_state, pickup_zip, pickup_country,
                                      delivery_city,
                                      delivery_state, delivery_zip, delivery_country)
                try:
                    dat65 = round(0.65 * dat_allin + 0.35 * gs_allin)
                except:
                    dat65 = 'Not Available'
                try:
                    dat35 = round(0.35 * dat_allin + 0.65 * gs_allin)
                except:
                    dat35 = 'Not Available'
                if isinstance(dat65, int) is True and isinstance(dat35, int) is True:
                    rate = min(dat65, dat35)
                    if min(dat65, dat35) == dat65:
                        print(f"Blend Chosen: 65% DAT, 35% GS Network")
                    else:
                        print(f"Blend Chosen: 35% DAT, 65% GS Network")
                elif isinstance(dat_allin, int) is True:
                    rate = dat_allin
                    print(f"No Blend Available. Choosing DAT Rate")
                elif isinstance(gs_allin, int) is True:
                    rate = gs_allin
                    print(f"No Blend Available. Choosing GS Network Rate")
                else:
                    rate = 'Error in rate calculation'

                # add margins
                if rules['flat'] != 0:
                    rate = round(rate + rules['flat'])
                if rules['percent'] != 0:
                    rate = round(rate * rules['percent'])


            else:
                print('need to use fixed GS rate')
                rate = priority_rules['final_sell_rate']

            # carrierExpirationDate =  "2021-02-07T12:30:00-05:00"
            expiration = now + timedelta(days=1)
            expiration = expiration.strftime('%Y-%m-%dT%H:%M:%S%z')

            pick_city_state = f"{pickup_city}, {pickup_state}"
            del_city_state = f"{delivery_city}, {delivery_state}"

            now = now.strftime('%Y-%m-%dT%H:%M:%S%z')

            payload = dict()
            payload['currency'] = 'USD'
            payload['offer_amount'] = rate
            payload['expiration_date'] = now
            payload['comment'] = "SpotMarket rate provided by Omni Logistics, dba LiVe Logistics"
            payload['use_contract_rate'] = "false"

            status_code = send_spot_rate_to_e2open(load_id, payload)
            if 200 <= status_code < 300:
                print(f"Successful Spot Market Bid for {load_id}")
                print(f"From: {pick_city_state}")
                print(f"To: {del_city_state}")
                print(f"Allin Rate: {rate}")
            return


