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
from libs.get_item_dynamodb import get_item, new_function
from libs.send_html_email import send_html_email

dynamoTable = os.environ['PRICING_ALGO_E2OPEN_TABLE']
dynamoTable2 = os.environ['E2OPEN_NEW_SHIPPER_TABLE']

# NOTE: ALWAYS ONLY LINEHAUL

if os.environ['ENVIRONMENT'] == 'prod':
    from prod_config import *
else:
    from dev_config import *


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


def parse_e2open(data):
    now = datetime.utcnow().replace(tzinfo=timezone('UTC'))
    now_unix = calendar.timegm(now.utctimetuple())
    #try:
    load_id = data['loadID']
    shipper_name = data['shipper']['name']
    shipper_duns = data['shipper']['duns']
    # KENS FOODS: 00-106-3114
    # HB FULLER: 00-615-9776
    # NUTRABOLT: 132052320
    # MATTHEWS INTERNATIONAL: 130-932-564
    ts = datetime.utcnow().replace(tzinfo=timezone('UTC'))
    print(f"Before Dynamo Get: {ts}")
    try:
        row = get_item(dynamoTable2, shipper_duns)
        #row = new_function(dynamoTable2, shipper_duns)
        recognized_shipper = 1
    except:
        recognized_shipper = 0
    ts = datetime.utcnow().replace(tzinfo=timezone('UTC'))
    print(f"After Dynamo Get: {ts}")
    #  if shipper_duns in ["00-106-3114", "132052320","123456789","130-932-564"] or shipper_name.upper() in ["KEN'S FOODS","NUTRABOLT","PSG API TEST COMPANY"]:
    #     recognized_shipper = 1
    # else:
    #     recognized_shipper = 0
    if shipper_name.upper() in ["KERRY INC.", "KERRY INC."]:
        customer = "KERRY INGREDIENTS AND FLAVORS"
    elif shipper_name.upper() == "KEN'S FOODS":
        customer = "KENS FOODS INC."
    elif shipper_name.upper() == "NUTRABOLT":
        customer = "Nutrabolt"
    elif shipper_name.upper() == "SFC GLOBAL SUPPLY CHAIN, INC":
        customer = "SCHWANS"
    elif shipper_name.upper() == "HB FULLER":
        customer = "HB Fuller"
    elif shipper_duns == "130-932-564":
        customer = "Matthews International"
    else:
        customer = ""
    stops = data['stops']
    for stop in range(len(stops)):
        if stops[stop]['stopSequence'] == 0:
            # incoming datetime format is "2021-01-15T15:00:00-05:00"
            pickup_window_start = stops[stop]['planStartDate']
            pickup_window_start = convert_timestring_to_datetime(pickup_window_start)
            pickup_window_end = stops[stop]['planEndDate']
            pickup_window_end = convert_timestring_to_datetime(pickup_window_end)
            pickup_stop_name = stops[stop]['location']['stopLocationName']
            pickup_address = stops[stop]['location']['locationAddress']['address1']
            pickup_city = stops[stop]['location']['locationAddress']['city']
            pickup_state = stops[stop]['location']['locationAddress']['state']
            pickup_country = stops[stop]['location']['locationAddress']['country']
            try:
                pickup_zip = stops[stop]['location']['locationAddress']['postalCode']
            except:
                pickup_zip = get_zip_from_citystate(pickup_city, pickup_state)
        if stops[stop]['stopSequence'] == len(stops) - 1:
            # incoming datetime format is "2021-01-15T15:00:00-05:00"
            delivery_window_start = stops[stop]['planStartDate']
            delivery_window_start = convert_timestring_to_datetime(delivery_window_start)
            delivery_window_end = stops[stop]['planEndDate']
            delivery_window_end = convert_timestring_to_datetime(delivery_window_end)
            delivery_stop_name = stops[stop]['location']['stopLocationName']
            delivery_address = stops[stop]['location']['locationAddress']['address1']
            delivery_city = stops[stop]['location']['locationAddress']['city']
            delivery_state = stops[stop]['location']['locationAddress']['state']
            delivery_country = stops[stop]['location']['locationAddress']['country']
            try:
                delivery_zip = stops[stop]['location']['locationAddress']['postalCode']
            except:
                delivery_zip = get_zip_from_citystate(delivery_city, delivery_state)
    mode = data['transportationMode']  # TL, LTL, R, A, IM, V
    equipment = data['equipment']['type'].upper()  # VAN, REEFER, BULK, FLATBED, CONTAINER, OTHER
    service_level = data['serviceLevel']['description'].upper()
    round_trip = data['roundTrip']
    hazmat = data['hazmat']
    try:
        weight = data['totalWeight']['value']
    except:
        weight = None
    # except:
    #     rejection_payload = {
    #         "error": "Missing Required Info",
    #         "status": "Quote Not Received"
    #     }
    #     rejection_payload = json.dumps(rejection_payload)
    #     raise Exception("403: " + rejection_payload)

    ### TO DO ###
    # implement logic that will allow for auto-quoting
    if mode == 'TL':
        is_tl = 1
    else:
        is_tl = 0
    if equipment in {"VAN", "FLATBED", "REEFER"}:
        is_v_or_f_or_r = 1
    else:
        is_v_or_f_or_r = 0
    if service_level in {"TL STANDARD", "TL:STANDARD", "STANDARD"}:
        is_standard = 1
    else:
        is_standard = 0
    lead_time = pickup_window_start - now
    lead_time = lead_time.total_seconds() / 3600
    if lead_time > 24:
        not_same_day = 1
    else:
        not_same_day = 0
    fourteen_days_lead = pickup_window_start - now
    fourteen_days_lead = fourteen_days_lead.total_seconds() / 86400
    if fourteen_days_lead >= 14:
        fourteen_days = 0
    else:
        fourteen_days = 1
    if hazmat is True:
        dangerous = 0
    else:
        dangerous = 1
    if pickup_window_start <= delivery_window_start:
        stops_in_sequence = 1
    else:
        stops_in_sequence = 0
    if now < pickup_window_start:
        stops_in_future = 1
    elif now < delivery_window_start:
        stops_in_future = 1
    else:
        stops_in_future = 0
    if len(stops) > 2:
        two_stops = 0
    else:
        two_stops = 1

    eligibility = is_tl * is_v_or_f_or_r * is_standard * not_same_day * fourteen_days * dangerous * stops_in_sequence * stops_in_future * two_stops * recognized_shipper

    if eligibility == 0:
        print(
            f"""Ineligible: TL: {is_tl}; Van or Reef or Flat: {is_v_or_f_or_r}; Standard: {is_standard}; Not Same Day: {not_same_day};
                Within 14 Days: {fourteen_days}; Hazmat: {dangerous}; Stops in Order: {stops_in_sequence};
                Stops in Future: {stops_in_future}; Two Stops: {two_stops}; Recognized Shipper: {recognized_shipper}""")
        rejection_payload = {
            "status": "Ineligible for Quoting"
        }
        rejection_payload = json.dumps(rejection_payload)
        print(rejection_payload)
        raise Exception("204: " + rejection_payload)
        # return {'statusCode': 204, 'body': "204: Ineligible for Quoting"}
    else:
        print(
            f"Eligible: TL: {is_tl}; Van or Reef: {is_v_or_f_or_r}; Standard: {is_standard}; Not Same Day: {not_same_day}")
        # look for fixed GS rate
        ts = datetime.utcnow().replace(tzinfo=timezone('UTC'))
        print(f"Before Priority Rule API: {ts}")
        priority_rules = search_for_priority_rule(equipment, customer, pickup_city, pickup_state, pickup_zip, pickup_country,
                                     delivery_city, delivery_state, delivery_zip, delivery_country)
        ts = datetime.utcnow().replace(tzinfo=timezone('UTC'))
        print(f"After Priority Rule API: {ts}")
        if priority_rules['final_sell_rate'] is None:
            gs_network_rate, gs_dist, gs_live_rate, gs_fuel = greenscreens_quote_utc_e2open(pickup_zip, pickup_city,
                                                                                            pickup_state, delivery_zip,
                                                                                            delivery_city,
                                                                                            delivery_state,
                                                                                            pickup_window_start,
                                                                                            equipment)
            ts = datetime.utcnow().replace(tzinfo=timezone('UTC'))
            print(f"After GS Rate API: {ts}")
            dat_rate, dat_mileage, dat_num_of_reports, dat_num_of_companies, dat_esc_time, dat_org_market, dat_dest_market, dat_fuel = dat_rateview_w_fuel(
                pickup_zip, delivery_zip, equipment)
            ts = datetime.utcnow().replace(tzinfo=timezone('UTC'))
            print(f"After DAT Rate API: {ts}")
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
                rules = get_rules(equipment, customer, pickup_city, pickup_state, pickup_zip, pickup_country, delivery_city,
                                  delivery_state, delivery_zip, delivery_country)
                ts = datetime.utcnow().replace(tzinfo=timezone('UTC'))
                print(f"After Combo Rule API: {ts}")
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

        ts = datetime.utcnow().replace(tzinfo=timezone('UTC'))
        print(f"After APIs: {ts}")
        # carrierExpirationDate =  "2021-02-07T12:30:00-05:00"
        expiration = now + timedelta(days=1)
        expiration = expiration.strftime('%Y-%m-%dT%H:%M:%S%z')

        pick_city_state = f"{pickup_city}, {pickup_state}"
        del_city_state = f"{delivery_city}, {delivery_state}"

        # send notification email
        if customer == "KENS FOODS INC.":
            email_sub = f"E2Open Quote for {customer}"
            send_html_email(e2open_notification, from_address, to_ken_address, email_sub, customer_name=customer,
                            equipment=equipment, pick_city_state=pick_city_state, del_city_state=del_city_state,
                            quoted_rate=rate, load_id=load_id)
        elif customer == "Nutrabolt":
            email_sub = f"E2Open Quote for {customer}"
            send_html_email(e2open_notification, from_address, to_nutra_address, email_sub, customer_name=customer,
                            equipment=equipment, pick_city_state=pick_city_state, del_city_state=del_city_state,
                            quoted_rate=rate, load_id=load_id)
        elif customer == "Matthews International":
            email_sub = f"E2Open Quote for {customer}"
            send_html_email(e2open_notification, from_address, to_matt_address, email_sub, customer_name=customer,
                            equipment=equipment, pick_city_state=pick_city_state, del_city_state=del_city_state,
                            quoted_rate=rate, load_id=load_id)

        now = now.strftime('%Y-%m-%dT%H:%M:%S%z')

        returned_payload = {
            "rate": rate,
            "currency": "USD",
            "carrierExpirationDate": expiration
        }
        returned_payload = json.dumps(returned_payload)
        print(returned_payload)
        message_id = f"{now_unix}-{load_id}"
        ts = datetime.utcnow().replace(tzinfo=timezone('UTC'))
        print(f"Before Dynamo Update: {ts}")
        update_item(dynamoTable, message_id, customer=customer, del_city_state=del_city_state,
                    equipment=equipment, load_id=load_id, pick_city_state=pick_city_state, quoted_rate=rate,
                    timestamp=now)
        print(f"After Dynamo Update: {ts}")
        return returned_payload
