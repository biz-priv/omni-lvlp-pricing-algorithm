import boto3

# Global cache variable
parameter_cache = {}

def get_creds(param_names):
  global parameter_cache

  # Ensure that param_names is a list
  if not isinstance(param_names, list):
    param_names = [param_names]

  # Check if all requested parameters are in the cache
  if all(name in parameter_cache for name in param_names):
    return parameter_cache

  # Create an SSM client
  ssmclient = boto3.client('ssm')
  response = ssmclient.get_parameters(
    Names=param_names,
    WithDecryption=True
  )

  # Iterate through the list of parameters and add the parameter values to the cache
  for param in response['Parameters']:
    param_name = param['Name']
    param_value = param['Value']
    var_name = param_name.split('/')[-1].replace('-', '_')
    parameter_cache[var_name] = param_value

  return parameter_cache
