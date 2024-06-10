"""
* File: pricing-algorithm\libs\get_item_dynamodb.py
* Project: Omni-lvlp-pricing-algorithm
* Author: Bizcloud Experts
* Date: 2023-12-27
* Confidential and Proprietary
"""
import boto3


def get_item(table_name, id):
    """
    Retrieve an item from the DynamoDB table.

    :param table_name: The name of the DynamoDB table.
    :param id: The id of the item to retrieve.
    :return: The retrieved item.
    """
    # Initialize a DynamoDB resource
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    response = table.get_item(
        Key={"message_id": id}
    )
    return response['Item']


def new_function(table_name, id):
    session = boto3.Session(region_name='us-east-1')
    # Create DynamoDB client
    dynamodb = session.client('dynamodb')
    # Define the primary key of the item to get
    primary_key = {'message_id': id}
    # Define the table name
    #table_name = 'pricing-algo-pricing-algorithm-master-dev-PricingAlgoE2OpenTable-9RYUKBLQ1WS0'
    # Use the DynamoDB client to get an item by primary key
    try:
        response = dynamodb.get_item(TableName=table_name, Key=primary_key)
        item = response.get('Item', None)
        print(item)
        return item
    except:
        print('failed')



#new_function('pricing-algo-pricing-algorithm-master-dev-PricingAlgoE2OpenTable-9RYUKBLQ1WS0', "123456789")
