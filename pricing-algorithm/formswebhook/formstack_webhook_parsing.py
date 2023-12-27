import imaplib
import email
import json
import os
import requests
from libs.get_creds import get_creds
from libs.greenscreens_api import greenscreens_quote
from libs.dat_api import dat_rateview
from libs.send_html_email import send_html_email

if os.environ['ENVIRONMENT'] == 'prod':
    from prod_config import *
else:
    from dev_config import *
#import from my dynamic sendgrid template
#from live_formstack.send_email import *
#from live_formstack.send_flatbed_email import *


def get_data(data):
    #parse all of the needed data from webhook/json
    try:
        data['omni_account'] = data['omni_account'].replace("'", "")
    except:
        pass
    try:
        data['your_name']['first'] = data['your_name']['first'].replace("'", "")
    except:
        pass
    try:
        data['your_name']['last'] = data['your_name']['last'].replace("'", "")
    except:
        pass
    try:
        data['your_email_address'] = data['your_email_address'].replace("'", "")
    except:
        pass
    try:
        data['bol_'] = data['bol_'].replace("'", "")
    except:
        pass
    try:
        data['product_name__description'] = data['product_name__description'].replace("'", "")
    except:
        pass
    try:
        data['open_deck__flatbed_mode_choice'] = data['open_deck__flatbed_mode_choice'].replace("'", "")
    except:
        pass
    try:
        data['total_shipment_weight'] = data['total_shipment_weight'].replace("'", "")
    except:
        pass
    try:
        data['tarp_size'] = data['tarp_size'].replace("'", "")
    except:
        pass
    try:
        data['product_dimensions'] = data['product_dimensions'].replace("'", "")
    except:
        pass

    data = str(data)
    data = data.replace('\"', "'")
    data = data.replace("None", "''")
    data = data.replace("'", '\"')
    data = json.loads(data)
    if data.get('FormID') != '4998248':
        raise Exception("Validation Error: Formstack webhook not from Brokerage Quote request form")
    else:
        request_num = data['UniqueID']
        first_name = data['your_name']['first']
        last_name = data['your_name']['last']
        try:
            station = data['omni_account']
        except:
            station = 'NA'
        email = data['your_email_address']
        try:
            bol = data['bol_']
        except:
            bol = 'NA'
        mode = data['mode']
        equipment = mode.upper()
        originzip = data['origin_zip_code']['zip']
        pickupdate = data['pickup_date']
        destzip = data['delivery_zip_code']['zip']
        originzip = originzip.strip()
        destzip = destzip.strip()

        ## GET origincity, originstate, destcity, deststate using google api
        try:
            google_api = get_creds(os.environ['GOOGLE_API_SECRET'])
        except:
            print("Failed to get Google API Secret")

        ori_response = requests.get(f'https://maps.googleapis.com/maps/api/geocode/json?components=postal_code:{originzip}&key={google_api}')
        ori_output = ori_response.json()
        for i in range(len(ori_output['results'][0]['address_components'])):
            if ori_output['results'][0]['address_components'][i]['types'][0] == 'locality':
                origincity = ori_output['results'][0]['address_components'][i]['short_name']
            if ori_output['results'][0]['address_components'][i]['types'][0] == 'administrative_area_level_1':
                originstate = ori_output['results'][0]['address_components'][i]['short_name']

        des_response = requests.get(f'https://maps.googleapis.com/maps/api/geocode/json?components=postal_code:{originzip}&key={google_api}')
        des_output = des_response.json()
        for i in range(len(des_output['results'][0]['address_components'])):
            if des_output['results'][0]['address_components'][i]['types'][0] == 'locality':
                destcity = des_output['results'][0]['address_components'][i]['short_name']
            if des_output['results'][0]['address_components'][i]['types'][0] == 'administrative_area_level_1':
                deststate = des_output['results'][0]['address_components'][i]['short_name']

        #make equipment digestable from the sources
        if equipment == 'OPEN DECK / FLATBED':
            equipment = 'FLATBED'
        elif equipment == 'DRY VAN':
            equipment = 'VAN'
        elif equipment == 'REEFER':
            equipment = 'REEFER'
        else:
            equipment = 'NA'


        #van or reefer flow
        if equipment == 'VAN' or equipment =='REEFER':
            #calculate GS rate
            gs_rate, dist, live_rate = greenscreens_quote(originzip, origincity, originstate, destzip, destcity, deststate, pickupdate, equipment)
            try:
                gs_rate = round(gs_rate)
                live_rate = round(live_rate)
            except:
                gs_rate = 'Not Available'
                live_rate = 'Not Available'
            print(f"Greenscreens rate is: {gs_rate}")



            #calculate DAT rateview rate
            datrate, mileage, num_of_reports, num_of_companies, esc_time, org_market, dest_market = dat_rateview(originzip, destzip, equipment)
            try:
                datrate = round(datrate)
            except:
                datrate = 'Not Available'
            print(f"DAT rate is: {datrate}")

            try:
                dat65 = round(0.65*datrate + 0.35*gs_rate)
            except:
                dat65 = 'Not Available'
            try:
                datgs = round(0.5*datrate + 0.5*gs_rate)
            except:
                datgs = 'Not Available'
            try:
                dat35 = round(0.35*datrate + 0.65*gs_rate)
            except:
                dat35 = 'Not Available'

            #set sendgrid subject variables
            subjects = f"{equipment} Quote Request #{request_num} from [{station}]"

            #send the email using the sendgrid dynamic template
            #SendDynamic(gs_rate, live_rate, origin_score, dest_score, subjects, datrate, mileage, num_of_reports, num_of_companies, esc_time, org_market, dest_market, dat65, datgs, dat35)
            send_html_email(email_template_file, from_address, to_address, email_sub, gs_rate=gs_rate, live_rate=live_rate, subjects=subjects, datrate=datrate, mileage=mileage, num_of_reports=num_of_reports, num_of_companies=num_of_companies, esc_time=esc_time, org_market=org_market, dest_market=dest_market, dat65=dat65, datgs=datgs, dat35=dat35)
        #flatbed flow
        elif equipment == 'FLATBED':
            #calculate GS rate
            gs_rate, dist, live_rate = greenscreens_quote(originzip, destzip, pickupdate, equipment)
            try:
                gs_rate = round(gs_rate)
                live_rate = round(live_rate)
            except:
                gs_rate = 'Not Available'
                live_rate = 'Not Available'
            print(f"Greenscreens rate is: {gs_rate}")

            #calculate DAT rateview rate
            datrate, mileage, num_of_reports, num_of_companies, esc_time, org_market, dest_market = dat_rateview(originzip, destzip, equipment)
            try:
                datrate = round(datrate)
            except:
                datrate = 'Not Available'
            print(f"DAT rate is: {datrate}")

            #set sendgrid subject variables
            subjects = f"{equipment} Quote Request #{request_num} from [{station}]"

            #send email using dynamic template
            #SendDynamicFlatbed(gs_rate, live_rate, subjects, datrate, mileage, num_of_reports, num_of_companies, esc_time, org_market, dest_market)
            send_html_email(email_template_flatbed_file, from_address, to_address, email_sub, gs_rate=gs_rate, live_rate=live_rate, subjects=subjects, datrate=datrate, mileage=mileage, num_of_reports=num_of_reports, num_of_companies=num_of_companies, esc_time=esc_time, org_market=org_market, dest_market=dest_market, dat65=dat65, datgs=datgs, dat35=dat35)
        else:
            print('Not acceptable equipment type')

        return "Formstack rate email successfully sent"
