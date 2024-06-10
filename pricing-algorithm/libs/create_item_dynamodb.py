"""
* File: pricing-algorithm\libs\create_item_dynamodb.py
* Project: Omni-lvlp-pricing-algorithm
* Author: Bizcloud Experts
* Date: 2023-12-27
* Confidential and Proprietary
"""
import boto3
import json
from decimal import Decimal


def create_item(table_name, id, **attributes):
  # Initialize a DynamoDB resource
  dynamodb = boto3.resource('dynamodb')

  """
  Add an item to the DynamoDB table.

  :param id: A numeric id to use as the partition key.
  :param attributes: A dictionary of additional attributes for the item.
  :return: The response from the put_item operation.
  """

  table = dynamodb.Table(table_name)
  item = {'message_id': id}
  item.update(attributes)
  item = json.loads(json.dumps(item), parse_float=Decimal)
  response = table.put_item(Item=item)
  return response
