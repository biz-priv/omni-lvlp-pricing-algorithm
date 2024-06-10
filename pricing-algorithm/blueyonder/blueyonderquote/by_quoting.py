"""
* File: pricing-algorithm\blueyonder\blueyonderquote\by_quoting.py
* Project: Omni-lvlp-pricing-algorithm
* Author: Bizcloud Experts
* Date: 2023-12-27
* Confidential and Proprietary
"""
import boto3
import requests
import json
from pathlib import Path
import pytz
from datetime import timedelta
import datetime
import os
from libs.update_item_dynamodb import update_item
from generate_rates import generate_rate
from libs.send_html_email import send_html_email

dynamoTable = os.environ['PRICING_ALGO_DB_TABLE']

if os.environ['ENVIRONMENT'] == 'prod':
    from prod_config import *
else:
    from dev_config import *


def check_for_holiday(start_date, end_date):
    # '%Y-%m-%dT%H:%M:%S%z'
    # start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S%z').date()
    # end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S%z').date()
    start_date = start_date.date()
    end_date = end_date.date()

    delta = end_date - start_date
    holiday_dict = {
      "2023-12-24": 0.50,
      "2023-12-25": 0.50,
      "2023-12-26": 0.50,
      "2023-12-31": 0.25,
      "2024-01-01": 0.25,
      "2024-05-27": 0.25,
      "2024-07-04": 0.25,
      "2024-09-02": 0.25,
      "2024-11-28": 0.25,
      "2024-12-24": 0.50,
      "2024-12-25": 0.50,
      "2024-12-26": 0.50,
      "2024-12-31": 0.25,
      "2025-01-01": 0.25
    }
    holiday_list = list(holiday_dict.keys())
    overlapping_days = dict()

    for i in range(delta.days + 1):
        day = start_date + timedelta(days=i)
        day = day.strftime('%Y-%m-%d')
        if day in holiday_list:
            overlapping_days[day] = holiday_dict[day]

    if len(overlapping_days) > 0:
        max_uplift = max(overlapping_days.values())
    else:
        max_uplift = 0
    return max_uplift


# noinspection PyDictCreation
def blue_yonder(data):
    print(data)
    now = datetime.datetime.utcnow()
    expiration = now + datetime.timedelta(hours=24)
    now = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    expiration = expiration.strftime('%Y-%m-%dT%H:%M:%SZ')

    try:
        company_name = data['apiHeader']['companyCode']
        # company_code = data['apiHeader']['contractedCompanyCode']
        customer_code = data['apiHeader']['customerCode'][0]
        provider_customer_code = data['apiHeader']['providerCustomerCode']
        received_time = data['apiHeader']['timestamp']  # timezone is UTC
        message_id = data['apiHeader']['messageID']
        our_provider_code = data['apiHeader']['providerCode'][0]  # will we have multiple values here
        try:
            load_id = data['loadID']
        except:
            load_id = data['loadDetails']['loadID']
    except:
        print('Need to add exception response here, missing required header info')  # send a 409 code
        rejection_payload = {
            "responseStatus": "Rejected",
            "rejectionDescription": "Malformed Header",
            "rejectionCode": "8"
        }
        rejection_payload = json.dumps(rejection_payload)
        raise Exception("403: " + rejection_payload)
    if customer_code not in ['BYCustomer', 'BestBuy']:
        rejection_payload = {
            "apiHeader": {
                "customerCode": [
                    customer_code
                ],
                "providerCode": [
                    our_provider_code
                ],
                "messageID": message_id,
                "timestamp": now,
                "targetContext": "TMS",
            },
            "responseStatus": "Rejected"
        }
        rejection_payload['rejectionDescription'] = "Unknown customer code."
        rejection_payload['rejectionCode'] = "7"
        rejection_payload = json.dumps(rejection_payload)
        raise Exception("403: " + rejection_payload)
    # define rejection payload, to be used and updated if the request is rejected
    rejection_payload = {
        "apiHeader": {
            "customerCode": [
                customer_code
            ],
            "providerCode": [
                our_provider_code
            ],
            "messageID": message_id,
            "companyCode": company_name,
            "timestamp": now,
            "targetContext": "TMS",
            "providerCustomerCode": provider_customer_code
        },
        "responseStatus": "Rejected",
        "loadID": load_id
    }

    try:
        equipment = data['equipmentDetails'][0]['equipmentType']  # will we have multiple values here
        if equipment == 'DryVan':
            equipment = 'VAN'
        elif equipment == 'Reefer':
            equipment = 'REEFER'
        elif equipment == 'Flatbed':
            equipment = 'FLATBED'
        else:
            # Want to let them know it is not a valid equipment type
            equipment = equipment + 1
    except:
        print('Need to add exception response here, missing required equipment')
        rejection_payload['rejectionDescription'] = "Missing equipment."
        rejection_payload['rejectionCode'] = "2"
        rejection_payload = json.dumps(rejection_payload)

        ## TODO: enter all required table data
        update_item(dynamoTable, message_id, payload=rejection_payload, customer=customer_code,
                    received_time=received_time, load_id=load_id, quote_status='Rejected', rejected_reason=2,
                    NewQuote="No")
        raise Exception("409: " + rejection_payload)  # need to return rejection payload and 409 code
    try:
        order_value = data['loadTotals']['orderValue']
    except:
        print('Need to add exception response here, missing required order value')
        rejection_payload['rejectionDescription'] = "Missing Order Value."
        rejection_payload['rejectionCode'] = "6"
        rejection_payload = json.dumps(rejection_payload)
        ## TODO: enter all required table data
        update_item(dynamoTable, message_id, payload=rejection_payload, customer=customer_code,
                    received_time=received_time, load_id=load_id, quote_status='Rejected', rejected_reason=6,
                    NewQuote="No")
        raise Exception("409: " + rejection_payload)
    try:
        pallets = data['loadTotals']['pallets']
    except:
        print('Need to add exception response here, missing required pallets')
        rejection_payload['rejectionDescription'] = "Missing pallets."
        rejection_payload['rejectionCode'] = "3"
        rejection_payload = json.dumps(rejection_payload)
        ## TODO: enter all required table data
        update_item(dynamoTable, message_id, payload=rejection_payload, customer=customer_code,
                    received_time=received_time, load_id=load_id, quote_status='Rejected', rejected_reason=3,
                    NewQuote="No")
        raise Exception("409: " + rejection_payload)
    try:
        pieces = data['loadTotals']['pieces']
    except:
        pieces = 0
    try:
        weight = data['loadTotals']['weight']
    except:
        print('Need to add exception response here, missing required weight')
        rejection_payload['rejectionDescription'] = "Missing weight."
        rejection_payload['rejectionCode'] = "4"
        rejection_payload = json.dumps(rejection_payload)
        ## TODO: enter all required table data
        update_item(dynamoTable, message_id, payload=rejection_payload, customer=customer_code,
                    received_time=received_time, load_id=load_id, quote_status='Rejected', rejected_reason=4,
                    NewQuote="No")
        raise Exception("409: " + rejection_payload)
    try:
        teams_required = data['teamDriver']
    except:
        teams_required = False

    # define stop_info dict
    stop_info = {}
    valid_states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL', 'GA', 'ID', 'IL', 'IN', 'IA', 'KS',
                    'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY',
                    'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV',
                    'WI', 'WY']
    try:
        for i in range(len(data['stops'])):
            stop_type = data['stops'][i]['activityType']
            address_info = data['stops'][i]['address']
            early_arrival_utc = data['stops'][i]['earliestArrivalUtc']
            late_arrival_utc = data['stops'][i]['latestArrivalUtc']
            live_handling = data['stops'][i]['liveHandling']
            location_id = data['stops'][i]['locationID']
            location_name = data['stops'][i]['locationName']
            stop_sequence = data['stops'][i]['stopSequence']
            city = data['stops'][i]['address']['city']
            state = data['stops'][i]['address']['state']
            stop_info[stop_sequence] = {"stop_type": stop_type,
                                        "address": address_info,
                                        "early_arrival": early_arrival_utc,
                                        "late_arrival": late_arrival_utc,
                                        "live_handling": live_handling,
                                        "location_id": location_id,
                                        "location_name": location_name}
    except:
        print('Need to add exception response here, missing required stop info')
        rejection_payload['rejectionDescription'] = "Missing stop information."
        rejection_payload['rejectionCode'] = "5"
        rejection_payload = json.dumps(rejection_payload)
        ## TODO: enter all required table data
        update_item(dynamoTable, message_id, payload=rejection_payload, customer=customer_code,
                    received_time=received_time, load_id=load_id, quote_status='Rejected', rejected_reason=5,
                    NewQuote="No")
        raise Exception("409: " + rejection_payload)

    number_of_stops = len(stop_info)

    if number_of_stops > 2:
        print('Need to add exception here, too many stops')
        now = datetime.datetime.utcnow()
        now = now.strftime('%Y-%m-%dT%H:%M:%SZ')
        rejection_payload['rejectionDescription'] = "Multi-stop loads are not rated."
        rejection_payload['rejectionCode'] = "1"
        rejection_payload = json.dumps(rejection_payload)
        ## TODO: enter all required table data
        update_item(dynamoTable, message_id, payload=rejection_payload, customer=customer_code,
                    received_time=received_time, load_id=load_id, quote_status='Rejected', rejected_reason=1,
                    NewQuote="No")
        raise Exception("409: " + rejection_payload)
    else:
        # try to get Zip Code info
        try:
            if stop_info[1]['address']['countryCode'] == 'USA':
                if stop_info[1]['address']['state'] in valid_states:
                    pass
                else:
                    rejection_payload[
                        'rejectionDescription'] = "Loads outside of the contiguous US and Canada are not rated."
                    rejection_payload['rejectionCode'] = "10"
                    rejection_payload = json.dumps(rejection_payload)
                    update_item(dynamoTable, message_id, payload=rejection_payload, customer=customer_code,
                                received_time=received_time, load_id=load_id, quote_status='Rejected',
                                rejected_reason=10, NewQuote="No")
                    raise Exception("409: " + rejection_payload)
            elif stop_info[1]['address']['countryCode'] != 'CA':
                rejection_payload[
                    'rejectionDescription'] = "Loads outside of the contiguous US and Canada are not rated."
                rejection_payload['rejectionCode'] = "10"
                rejection_payload = json.dumps(rejection_payload)
                update_item(dynamoTable, message_id, payload=rejection_payload, customer=customer_code,
                            received_time=received_time, load_id=load_id, quote_status='Rejected', rejected_reason=10,
                            NewQuote="No")
                raise Exception("409: " + rejection_payload)
            else:
                pass
            if stop_info[2]['address']['countryCode'] == 'USA':
                if stop_info[2]['address']['state'] in valid_states:
                    pass
                else:
                    rejection_payload[
                        'rejectionDescription'] = "Loads outside of the contiguous US and Canada are not rated."
                    rejection_payload['rejectionCode'] = "10"
                    rejection_payload = json.dumps(rejection_payload)
                    update_item(dynamoTable, message_id, payload=rejection_payload, customer=customer_code,
                                received_time=received_time, load_id=load_id, quote_status='Rejected',
                                rejected_reason=10, NewQuote="No")
                    raise Exception("409: " + rejection_payload)
            elif stop_info[2]['address']['countryCode'] != 'CA':
                rejection_payload[
                    'rejectionDescription'] = "Loads outside of the contiguous US and Canada are not rated."
                rejection_payload['rejectionCode'] = "10"
                rejection_payload = json.dumps(rejection_payload)
                update_item(dynamoTable, message_id, payload=rejection_payload, customer=customer_code,
                            received_time=received_time, load_id=load_id, quote_status='Rejected', rejected_reason=10,
                            NewQuote="No")
                raise Exception("409: " + rejection_payload)
            else:
                pass
        except:
            try:
                if stop_info[1]['address']['state'] in valid_states or stop_info[1]['address']['countryCode'] == 'CA':
                    pass
                elif stop_info[2]['address']['state'] in valid_states or stop_info[3]['address']['countryCode'] == 'CA':
                    pass
                else:
                    rejection_payload['rejectionDescription'] = "Missing stop information."
                    rejection_payload['rejectionCode'] = "5"
                    rejection_payload = json.dumps(rejection_payload)
                    update_item(dynamoTable, message_id, payload=rejection_payload, customer=customer_code,
                                received_time=received_time, load_id=load_id, quote_status='Rejected',
                                rejected_reason=5, NewQuote="No")
                    raise Exception("409: " + rejection_payload)
            except:
                rejection_payload['rejectionDescription'] = "Missing stop information."
                rejection_payload['rejectionCode'] = "5"
                rejection_payload = json.dumps(rejection_payload)
                update_item(dynamoTable, message_id, payload=rejection_payload, customer=customer_code,
                            received_time=received_time, load_id=load_id, quote_status='Rejected', rejected_reason=5,
                            NewQuote="No")
                raise Exception("409: " + rejection_payload)
        origin_city = stop_info[1]['address']['city']
        origin_state = stop_info[1]['address']['state']
        origin_country = stop_info[1]['address']['countryCode']
        if origin_country == 'USA':
            origin_country = 'US'
        elif origin_country == 'CA':
            pass
        else:
            pass
        try:
            origin_zip = stop_info[1]['address']['postalCode']
            if len(origin_zip) == 9:
                origin_zip = origin_zip[:5]
            elif len(origin_zip) == 10:
                origin_zip = origin_zip[:5]
            else:
                pass
        except:
            google_key = 'AIzaSyDod39KtNuE6ufiFSLrpC83hK48jwCka1A'
            lat = stop_info[1]['address']['geographicalCoordinates']['latitude']
            long = stop_info[1]['address']['geographicalCoordinates']['longitude']
            loc_response = requests.get(
                f'https://maps.googleapis.com/maps/api/geocode/json?latlng={lat}%2C{long}&key={google_key}')
            loc_output = loc_response.json()
            for i in range(len(loc_output['results'][0]['address_components'])):
                if loc_output['results'][0]['address_components'][i]['types'] == ['postal_code']:
                    origin_zip = loc_output['results'][0]['address_components'][i]['short_name']
                else:
                    pass
        destination_city = stop_info[2]['address']['city']
        destination_state = stop_info[2]['address']['state']
        destination_country = stop_info[2]['address']['countryCode']
        if destination_country == 'USA':
            destination_country = 'US'
        else:
            pass
        try:
            destination_zip = stop_info[2]['address']['postalCode']
            if len(destination_zip) == 9:
                destination_zip = destination_zip[:5]
            elif len(destination_zip) == 10:
                destination_zip = destination_zip[:5]
            else:
                pass
        except:
            # google_key = 'AIzaSyDod39KtNuE6ufiFSLrpC83hK48jwCka1A'
            google_key = 'AIzaSyAU9buHNDnquWqbkvblYE7H6EFazFflRDo'
            lat = stop_info[2]['address']['geographicalCoordinates']['latitude']
            long = stop_info[2]['address']['geographicalCoordinates']['longitude']
            loc_response = requests.get(
                f'https://maps.googleapis.com/maps/api/geocode/json?latlng={lat}%2C{long}&key={google_key}')
            loc_output = loc_response.json()
            for i in range(len(loc_output['results'][0]['address_components'])):
                if loc_output['results'][0]['address_components'][i]['types'] == ['postal_code']:
                    origin_zip = loc_output['results'][0]['address_components'][i]['short_name']
                else:
                    pass

        # format pickup date
        pickup_date = stop_info[1]['late_arrival']
        if str(type(pickup_date)) == "<class 'str'>":
            pickup_date = datetime.datetime.strptime(pickup_date, '%Y-%m-%dT%H:%M:%SZ')
        else:
            print(type(pickup_date))
        pickup_date = pickup_date.replace(tzinfo=pytz.UTC)
        pickup_date = pickup_date.strftime('%Y-%m-%dT%H:%M:%SZ')

        if customer_code in ['BYCustomer', 'BestBuy']:
            bill_to = 'Best Buy DPD'
        else:
            bill_to = ''

        payload = {}
        payload['equipment_type'] = equipment
        payload['origin_zip'] = origin_zip
        payload['destination_zip'] = destination_zip
        payload['pickup_date'] = pickup_date
        payload['customer'] = bill_to
        try:
            payload['origin_lat'] = stop_info[1]['address']['geographicalCoordinates']['latitude']
            payload['origin_long'] = stop_info[1]['address']['geographicalCoordinates']['longitude']
        except:
            pass
        try:
            payload['origin_city'] = origin_city
            payload['origin_state'] = origin_state
            payload['origin_country'] = origin_country
        except:
            pass
        try:
            payload['dest_latitude'] = stop_info[2]['address']['geographicalCoordinates']['latitude']
            payload['dest_longitude'] = stop_info[2]['address']['geographicalCoordinates']['longitude']
        except:
            pass
        try:
            payload['dest_city'] = destination_city
            payload['dest_state'] = destination_state
            payload['dest_country'] = destination_country
        except:
            pass

        # get rate type and use generate rate function
        try:
            requested_cost_type = data['loadDetails']['requestedCostType']
        except:
            requested_cost_type = 'LineHaul'
        rate_output = generate_rate(payload)
        rate_output = json.loads(rate_output)
        if rate_output['rate'] == 'Error in rate calculation':
            rejection_payload['rejectionDescription'] = "LiVe had an error generating rates."
            rejection_payload['rejectionCode'] = "11"
            rejection_payload = json.dumps(rejection_payload)
            update_item(dynamoTable, message_id, payload=rejection_payload, customer=customer_code,
                        received_time=received_time, load_id=load_id, quote_status='Rejected', rejected_reason=11,
                        NewQuote="No")
        else:
            pass
        if requested_cost_type == "AllIn":
            linehaul_rate = rate_output['rate']
            fuel = rate_output['fuel']
            rate = linehaul_rate + fuel
        elif requested_cost_type == "LineHaul":
            rate = rate_output['rate']
        else:
            rejection_payload['rejectionDescription'] = "Only All In and LineHaul accepted for requestedCostType."
            rejection_payload['rejectionCode'] = "9"
            rejection_payload = json.dumps(rejection_payload)
            update_item(dynamoTable, message_id, payload=rejection_payload, customer=customer_code,
                        received_time=received_time, load_id=load_id, quote_status='Rejected', rejected_reason=9,
                        NewQuote="No")
            raise Exception("409: " + rejection_payload)

        pickup_window_start = datetime.datetime.strptime(stop_info[1]['late_arrival'], '%Y-%m-%dT%H:%M:%SZ')
        delivery_window_start = datetime.datetime.strptime(stop_info[2]['late_arrival'], '%Y-%m-%dT%H:%M:%SZ')
        max_uplift = check_for_holiday(pickup_window_start, delivery_window_start)
        rate = rate * (1 + max_uplift)

        # if origin_zip in ['91739', '92335', '92336', '92377'] and destination_zip in ['93618','93666'] and customer_code in {'BestBuy'}:  # fixed rate fontana cali to dinuba cali (so cal)
        #     rate = 1075
        # elif origin_zip in ['91710', '91730', '91761', '91762', '91764'] and destination_zip in ['93618','93666'] and customer_code in {'BestBuy'}:  # fixed rate ontario cali to dinuba cali (so cal)
        #     rate = 1075
        # elif origin_zip in ['90248', '91789', '91789', '92647', '90808', '92407', '92806', '90620', '90810', '92337','95035'] and destination_zip in ['93618', '93666'] and customer_code in {'BestBuy'}:  # additional cali to dinuba cali (so cal)
        #     rate = 1075
        # elif origin_zip in ['95035', '95054', '95131', '95133', '95134'] and destination_zip in ['93618','93666'] and customer_code in {'BestBuy'}:  # fixed rate milpitas cali to dinuba cali (nor cal)
        #     rate = 1000
        # else:
        #     rate = round(1.11 * rate)

        #if rate_output['type'] == 'fixed':
        #    rate = rate * 1.0
        #else:
        #    rate = round(1.09 * rate)

        # accepted payload
        accepted_payload = {
            "apiHeader": {
                "companyCode": company_name,
                "customerCode": [
                    customer_code
                ],
                "providerCustomerCode": provider_customer_code,
                "providerCode": [
                    our_provider_code
                ],
                "messageID": message_id,
                "timestamp": now
            },
            "loadID": load_id,
            "responseStatus": "Accepted",
            "quotes": [
                {
                    "providerCode": our_provider_code,
                    "quoteID": message_id,
                    "quoteExpiration": expiration,
                    "cost": {
                        "totalCost": rate,
                        "currency": "USD",
                        "costDetails": [
                            {
                                "chargeAmount": rate,
                                "detailType": requested_cost_type,
                                "currency": "USD"
                            }
                        ]
                    },
                    "costType": requested_cost_type,
                    "serviceType": "TL"
                }
            ]
        }

        accepted_payload = json.dumps(accepted_payload)
        ## TODO: enter all required table data
        update_item(dynamoTable, message_id, payload=accepted_payload, customer=customer_code,
                    received_time=received_time, load_id=load_id, equipment_type=equipment, over_value=order_value,
                    pallets=pallets, pieces=pieces, weight=weight, team=teams_required, pcikup_zip=origin_zip,
                    delivery_zip=destination_zip, suggested_rate=rate, quote_status='Accepted', NewQuote="No")
        email_sub = f'New Blue Yonder Quote for {company_name} BOL {load_id}'
        origin_city_state = origin_city + ", " + origin_state
        dest_city_state = destination_city + ", " + destination_state
        send_html_email(BYnotification, from_address, to_address, email_sub, customer_name=company_name,
                        quote_type=requested_cost_type, rate=round(rate, 2), origin_city_state=origin_city_state,
                        dest_city_state=dest_city_state, pickup_date=pickup_date, order_value=round(order_value, 2))
        # print(accepted_payload)

        return accepted_payload
