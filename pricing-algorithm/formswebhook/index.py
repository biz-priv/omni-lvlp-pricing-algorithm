from formstack_webhook_parsing import get_data

def lambda_handler(event, context):
    print(event)
    data = event['data']
    return get_data(data)