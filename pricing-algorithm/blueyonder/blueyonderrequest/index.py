from by_request import blue_yonder_request

def lambda_handler(event, context):
    print(event)
    return blue_yonder_request(event)