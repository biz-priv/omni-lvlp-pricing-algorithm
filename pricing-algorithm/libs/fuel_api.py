import requests
import json
import os
import datetime
from libs.get_creds import get_creds

def doe_prices():
    today = datetime.date.today()

    api_start = today + datetime.timedelta(days=-14)
    api_end = today

    apikey = get_creds(os.environ['FUEL_API_SECRET'])
    apikey = apikey['fuel_api_secret']
    url = f'https://api.eia.gov/v2/petroleum/pri/gnd/data/?api_key={apikey}&frequency=weekly&data[0]=value&facets[product][]=EPD2D&facets[duoarea][]=NUS&start={api_start}&end={api_end}&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=5000'

    response = requests.get(url)
    try:
        output = response.json()
        print(output)
        data = output['response']['data']
        most_recent_price = data[0]['value']
    except:
        most_recent_price = 4.37

    if most_recent_price > 5.44:
        surcharge = 0.54
    elif most_recent_price >= 5.36:
        surcharge = 0.53
    elif most_recent_price >= 5.28:
        surcharge = 0.52
    elif most_recent_price >= 5.20:
        surcharge = 0.51
    elif most_recent_price >= 5.12:
        surcharge = 0.50
    elif most_recent_price >= 5.04:
        surcharge = 0.49
    elif most_recent_price >= 4.96:
        surcharge = 0.48
    elif most_recent_price >= 4.88:
        surcharge = 0.47
    elif most_recent_price >= 4.80:
        surcharge = 0.46
    elif most_recent_price >= 4.72:
        surcharge = 0.45
    elif most_recent_price >= 4.64:
        surcharge = 0.44
    elif most_recent_price >= 4.56:
        surcharge = 0.43
    elif most_recent_price >= 4.48:
        surcharge = 0.42
    elif most_recent_price >= 4.40:
        surcharge = 0.41
    elif most_recent_price >= 4.32:
        surcharge = 0.40
    elif most_recent_price >= 4.24:
        surcharge = 0.39
    elif most_recent_price >= 4.16:
        surcharge = 0.38
    elif most_recent_price >= 4.08:
        surcharge = 0.37
    elif most_recent_price >= 4.00:
        surcharge = 0.36
    elif most_recent_price >= 3.92:
        surcharge = 0.35
    elif most_recent_price >= 3.84:
        surcharge = 0.34
    elif most_recent_price >= 3.76:
        surcharge = 0.33
    elif most_recent_price >= 3.68:
        surcharge = 0.32
    elif most_recent_price >= 3.60:
        surcharge = 0.31
    elif most_recent_price >= 3.52:
        surcharge = 0.30
    elif most_recent_price >= 3.44:
        surcharge = 0.29
    elif most_recent_price >= 3.36:
        surcharge = 0.28
    elif most_recent_price >= 3.28:
        surcharge = 0.27
    elif most_recent_price >= 3.20:
        surcharge = 0.26
    elif most_recent_price >= 3.12:
        surcharge = 0.25
    elif most_recent_price >= 3.04:
        surcharge = 0.24
    elif most_recent_price >= 2.96:
        surcharge = 0.23
    elif most_recent_price >= 2.88:
        surcharge = 0.22
    elif most_recent_price >= 2.80:
        surcharge = 0.21
    elif most_recent_price >= 2.72:
        surcharge = 0.20
    elif most_recent_price >= 2.64:
        surcharge = 0.19
    elif most_recent_price >= 2.56:
        surcharge = 0.18
    elif most_recent_price >= 2.48:
        surcharge = 0.17
    elif most_recent_price >= 2.40:
        surcharge = 0.16
    elif most_recent_price >= 2.32:
        surcharge = 0.15
    elif most_recent_price >= 2.24:
        surcharge = 0.14
    elif most_recent_price >= 2.16:
        surcharge = 0.13
    elif most_recent_price >= 2.08:
        surcharge = 0.12
    elif most_recent_price >= 2.00:
        surcharge = 0.11
    elif most_recent_price >= 1.92:
        surcharge = 0.10
    elif most_recent_price >= 1.84:
        surcharge = 0.09
    elif most_recent_price >= 1.76:
        surcharge = 0.08
    elif most_recent_price >= 1.68:
        surcharge = 0.07
    elif most_recent_price >= 1.60:
        surcharge = 0.06
    elif most_recent_price >= 1.52:
        surcharge = 0.05
    elif most_recent_price >= 1.44:
        surcharge = 0.04
    elif most_recent_price >= 1.36:
        surcharge = 0.03
    elif most_recent_price >= 1.28:
        surcharge = 0.02
    elif most_recent_price >= 1.28:
        surcharge = 0.01
    else:
        surcharge = 0

    print(f"Fuel surcharge: ${surcharge}")
    return surcharge
