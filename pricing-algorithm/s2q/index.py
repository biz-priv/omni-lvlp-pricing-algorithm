from s2q_suggested_rates import generate_suggested_rate_for_s2q

def lambda_handler(event, context):
    print(event)
    return generate_suggested_rate_for_s2q(event)