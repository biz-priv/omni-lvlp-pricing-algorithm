import requests
import json
from pyzipcode import ZipCodeDatabase

def zip_code(zipcode):
    #use module to get city/state
    zcdb = ZipCodeDatabase()
    #parse the city name from the response
    city = zcdb[zipcode].city
    state = zcdb[zipcode].state
    return city, state
