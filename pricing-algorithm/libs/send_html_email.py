import boto3
import traceback
import json
from jinja2 import Environment, FileSystemLoader

def send_html_email(html_template_file, from_address, to_address, email_sub, **kwargs):
    try:
        env = Environment(loader=FileSystemLoader('.'))

        template = env.get_template(html_template_file)

        html_content = template.render(**kwargs)


        # Create an SES client
        ses = boto3.client('ses')

        # Send the email
        ses.send_email(
        Source= from_address,
        Destination={
          'ToAddresses': to_address,
        },
        Message={
          'Body': {
            'Html': {
              'Charset': 'UTF-8',
              'Data': html_content,
            }
          },
          'Subject': {
            'Charset': 'UTF-8',
            'Data': email_sub,
          },
        },
        )
    except Exception as e:
        error = str(e)
        stacktrace = json.dumps(traceback.format_exc())
        message = "Exception: " + error + "  Stacktrace: " + stacktrace
        err = {"message": message}
        print(err)
