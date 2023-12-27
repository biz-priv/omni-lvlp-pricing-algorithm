import boto3
import json
import datetime
import os
from libs.create_item_dynamodb import create_item

dynamoTable = os.environ['PRICING_ALGO_DB_TABLE']

def blue_yonder_request(data):
    print(data)
    now = datetime.datetime.utcnow()
    now = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    try:
        company_name = data['apiHeader']['companyCode']
        #company_code = data['apiHeader']['contractedCompanyCode']
        customer_code = data['apiHeader']['customerCode'][0]
        #provider_customer_code = data['apiHeader']['providerCustomerCode']
        received_time = data['apiHeader']['timestamp'] #timezone is UTC
        message_id = data['apiHeader']['messageID']
        our_provider_code = data['apiHeader']['providerCode'][0] #will we have multiple values here
        try:
            load_id = data['loadID']
        except:
            load_id = data['loadDetails']['loadID']
        print("Inserting data into database")
        create_item(dynamoTable, message_id, **data, NewQuote="Yes")
    except:
        print('Need to add exception response here, missing required header info') #send a 409 code
        rejection_payload = {
                                "responseStatus": "Rejected",
                                "rejectionDescription": "Malformed Header",
                                "rejectionCode": 8
                            }
        rejection_payload = json.dumps(rejection_payload)
        raise Exception("403: " + rejection_payload)
    acknowdgement_payload = {
                                "apiHeader": {
                                    "providerCode": [our_provider_code],
                                    "messageID": message_id,
                                    "timestamp": now,
                                    "customerCode": [customer_code]
                                },
                                "responseStatus": "Acknowledged"
                            }
    acknowdgement_payload = json.dumps(acknowdgement_payload)
    return acknowdgement_payload
