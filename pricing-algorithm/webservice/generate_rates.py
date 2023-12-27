import imaplib
import requests
import email
import json
import datetime
import os
from libs.get_creds import get_creds
from libs.greenscreens_api import greenscreens_quote, gs_fixed_prices, get_rules, search_for_priority_rule
from libs.dat_api import dat_rateview
from libs.fuel_api import doe_prices


def generate_rate(data):
    #######################
    ## GET ZIP CODES ######
    #######################
    ## first, try to get zip code from payload
    ## if no zip code, try to get zip code from lat/long
    ## if no zip code or lat/long, try to get zip code from city, state
    try:
        google_api = get_creds(os.environ['GOOGLE_API_SECRET'])
        google_api = google_api['google_api_secret']
    except:
        print("Failed to get Google API Secret")

    # parse equipment type
    equipment = data['equipment_type']

    ## origin zip
    try:
        originzip = data['origin_zip']
    except:
        try:
            origin_lat = data['origin_latitude']
            origin_long = data['origin_longitude']
            loc_response = requests.get(
                f'https://maps.googleapis.com/maps/api/geocode/json?latlng={origin_lat}%2C{origin_long}&key={google_api}')
            loc_output = loc_response.json()
            for i in range(len(loc_output['results'][0]['address_components'])):
                if loc_output['results'][0]['address_components'][i]['types'] == ['postal_code']:
                    originzip = loc_output['results'][0]['address_components'][i]['short_name']
                else:
                    pass
        except:
            origincity = data['origin_city']
            origincity = origincity.replace(' ', '%20')
            originstate = data['origin_state']
            originstate = originstate.replace(' ', '%20')
            origincountry = data['origin_country']
            loc_response = requests.get(
                f'https://maps.googleapis.com/maps/api/geocode/json?address={origincity}%2C%2B{originstate}&key={google_api}')
            loc_output = loc_response.json()
            for i in range(len(loc_output['results'][0]['address_components'])):
                if loc_output['results'][0]['address_components'][i]['types'] == ['postal_code']:
                    originzip = loc_output['results'][0]['address_components'][i]['short_name']
                else:
                    pass

    # destination zip
    try:
        destzip = data['destination_zip']
    except:
        try:
            dest_lat = data['dest_latitude']
            dest_long = data['dest_longitude']
            loc_response = requests.get(
                f'https://maps.googleapis.com/maps/api/geocode/json?latlng={dest_lat}%2C{dest_long}&key={google_api}')
            loc_output = loc_response.json()
            for i in range(len(loc_output['results'][0]['address_components'])):
                if loc_output['results'][0]['address_components'][i]['types'] == ['postal_code']:
                    destzip = loc_output['results'][0]['address_components'][i]['short_name']
                else:
                    pass
        except:
            destcity = data['dest_city']
            destcity = destcity.replace(' ', '%20')
            deststate = data['dest_state']
            deststate = deststate.replace(' ', '%20')
            destcountry = data['dest_country']
            loc_response = requests.get(
                f'https://maps.googleapis.com/maps/api/geocode/json?address={destcity}%2C%2B{deststate}&key={google_api}')
            loc_output = loc_response.json()
            for i in range(len(loc_output['results'][0]['address_components'])):
                if loc_output['results'][0]['address_components'][i]['types'] == ['postal_code']:
                    destzip = loc_output['results'][0]['address_components'][i]['short_name']
                else:
                    pass

    # parse pickup date
    pickupdate = data['pickup_date']

    try:
        customer = data['customer']
        if customer == 'BestBuy':
            customer = 'Best Buy'
        else:
            pass
    except:
        pass

    equipment = equipment.upper()
    if equipment != 'VAN':
        accepted_rate = 'Not a valid equipment type'
        return accepted_rate

    try:
        origincity = data['origin_city']
        originstate = data['origin_state']
        origincountry = data['origin_country']
    except:
        ori_response = requests.get(
            f'https://maps.googleapis.com/maps/api/geocode/json?components=postal_code:{originzip}&key={google_api}')
        ori_output = ori_response.json()

        for i in range(len(ori_output['results'][0]['address_components'])):
            if ori_output['results'][0]['address_components'][i]['types'][0] == 'locality':
                origincity = ori_output['results'][0]['address_components'][i]['short_name']
            if ori_output['results'][0]['address_components'][i]['types'][0] == 'administrative_area_level_1':
                originstate = ori_output['results'][0]['address_components'][i]['short_name']

    try:
        destcity = data['dest_city']
        deststate = data['dest_state']
        destcountry = data['dest_country']
    except:
        des_response = requests.get(
            f'https://maps.googleapis.com/maps/api/geocode/json?components=postal_code:{destzip}&key={google_api}')
        des_output = des_response.json()
        for i in range(len(des_output['results'][0]['address_components'])):
            if des_output['results'][0]['address_components'][i]['types'][0] == 'locality':
                destcity = ori_output['results'][0]['address_components'][i]['short_name']
            if des_output['results'][0]['address_components'][i]['types'][0] == 'administrative_area_level_1':
                deststate = ori_output['results'][0]['address_components'][i]['short_name']

    # calculate GS rate
    priority_rules = search_for_priority_rule(equipment, customer, origincity, originstate, originzip, origincountry, destcity,
                            deststate, destzip, destcountry)

    if priority_rules['final_sell_rate'] is None:
        gs_rate, dist, live_rate = greenscreens_quote(originzip, origincity, originstate, destzip, destcity, deststate,
                                                      pickupdate, equipment)
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
            rules = get_rules(equipment, customer, origincity, originstate, originzip, origincountry, destcity, deststate,
                              destzip,
                              destcountry)
        try:
            fuel_per_mile = doe_prices()
        except:
            fuel_per_mile = 0
        try:
            fuel_cost = fuel_per_mile * dist
        except:
            fuel_cost = 0

        try:
            gs_rate = round(gs_rate)
            live_rate = round(live_rate)
        except:
            gs_rate = 'Not Available'
            live_rate = 'Not Available'
        print(f"Greenscreens rate is: {gs_rate}")

        # calculate DAT rates
        response = dat_rateview(originzip, destzip, equipment)

        datrate, mileage, num_of_reports, num_of_companies, esc_time, org_market, dest_market = dat_rateview(originzip,
                                                                                                             destzip,
                                                                                                             equipment)
        try:
            datrate = round(datrate)
        except:
            datrate = 'Not Available'
        print(f"DAT rate is: {datrate}")

        try:
            dat65 = round(0.65 * datrate + 0.35 * gs_rate)
        except:
            dat65 = 'Not Available'
        try:
            dat35 = round(0.35 * datrate + 0.65 * gs_rate)
        except:
            dat35 = 'Not Available'

        if isinstance(dat65, int) is True and isinstance(dat35, int) is True:
            accepted_rate = min(dat65, dat35)
        elif isinstance(datrate, int) is True:
            accepted_rate = datrate
        elif isinstance(gs_rate, int) is True:
            accepted_rate = gs_rate
        else:
            accepted_rate = 'Error in rate calculation'
        type = 'nonfixed'
        if accepted_rate not in ['Error in rate calculation']:
            if rules['flat'] != 0:
                accepted_rate = round(accepted_rate + rules['flat'])
            if rules['percent'] != 0:
                accepted_rate = round(accepted_rate * rules['percent'])
    else:
        accepted_rate = priority_rules['final_sell_rate']
        fuel_cost = 0
        type = 'fixed'
    # greenscreen_precition_data = greenscreens_quote(originzip, origincity, originstate, destzip, destcity, deststate, pickupdate, equipment)

    generated_rate = {"rate": accepted_rate, "fuel": fuel_cost, "type": type}
    generated_rate = json.dumps(generated_rate)

    # return accepted_rate
    print(generated_rate)
    return generated_rate
