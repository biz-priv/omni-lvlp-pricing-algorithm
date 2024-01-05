import cfnresponse
def handler(event, context):
    response_data = {}
    try:
        webacldetails = event['ResourceProperties']['WebACL'].split("|")
        response_data['Name'] = webacldetails[0]
        cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)
    except Exception as e:
        response_data['Data'] = str(e)
        cfnresponse.send(event, context, cfnresponse.FAILED, response_data)