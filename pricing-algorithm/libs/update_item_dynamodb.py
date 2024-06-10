"""
* File: pricing-algorithm\libs\update_item_dynamodb.py
* Project: Omni-lvlp-pricing-algorithm
* Author: Bizcloud Experts
* Date: 2023-12-27
* Confidential and Proprietary
"""
import boto3
import json
from decimal import Decimal

def update_item(table_name, id, **attributes):
    """
    Add an attribute to an existing item in the DynamoDB table.

    :param table_name: The name of the DynamoDB table.
    :param id: The id of the item to update.
    :param attributes: A dictionary of attributes to add to the item.
                      Nested attributes can be specified using dot notation.
    :return: The response from the update_item operation.
    """
    # Initialize a DynamoDB resource
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    expression_attribute_names = {}
    expression_attribute_values = {}
    update_expression_parts = []
    for attr_path, attr_value in attributes.items():
        attr_path_parts = attr_path.split('.')
        attr_name = attr_path_parts[-1]
        for i, attr_path_part in enumerate(attr_path_parts):
            expression_attribute_names[f"#{attr_path_part}"] = attr_path_part
        attr_path_expression = '.'.join(f"#{part}" for part in attr_path_parts)
        update_expression_parts.append(f"{attr_path_expression} = :{attr_name}")
        expression_attribute_values[f":{attr_name}"] = attr_value

    update_expression = "SET " + ', '.join(update_expression_parts)

    # convert the attribute values to accommodate DynamoDB's requirements
    expression_attribute_values = json.loads(json.dumps(expression_attribute_values), parse_float=Decimal)

    response = table.update_item(
        Key={"message_id": id},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values,
        ReturnValues="ALL_NEW"  # returns all attributes of the item, not just the ones updated
    )
    return response
