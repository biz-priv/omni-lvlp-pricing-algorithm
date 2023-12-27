from rtr_new_shipper import parse_new_shipper_data

def lambda_handler(event, context):
    print(event)
    return parse_new_shipper_data(event)