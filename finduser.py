import boto3
import time
from botocore.exceptions import ClientError

# pp = pprint.PrettyPrinter(indent=4)
import smtplib
import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import base64
import json
#from botocore.exceptions import ClientError

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_secret():

    secret_name = "Global-SES-Central-Authority-Secrets"
    region_name = "us-west-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        if e.response["Error"]["Code"] == "DecryptionFailureException":
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response["Error"]["Code"] == "InternalServiceErrorException":
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response["Error"]["Code"] == "InvalidParameterException":
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response["Error"]["Code"] == "InvalidRequestException":
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response["Error"]["Code"] == "ResourceNotFoundException":
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if "SecretString" in get_secret_value_response:
            secret = get_secret_value_response["SecretString"]
        else:
            decoded_binary_secret = base64.b64decode(
                get_secret_value_response["SecretBinary"]
            )
    return secret

def lambda_handler(event, context):
    doit()

def doit():
    secret = get_secret()
    iam = boto3.client("iam")
    alias = boto3.client("iam").list_account_aliases()["AccountAliases"][0]
    unapproved_userlist = []
    
    SENDER = json.loads(secret)["SENDER"]
    SENDERNAME = alias
    RECIPIENT = json.loads(secret)["RECIPIENT"]
    AWS_REGION = "us-west-2"  # change if sending from another region
    CHARSET = "UTF-8"
    # Replace smtp_username with your Amazon SES SMTP user name.
    USERNAME_SMTP = json.loads(secret)["USERNAME_SMTP"]
    
    # Replace smtp_password with your Amazon SES SMTP password.
    PASSWORD_SMTP = json.loads(secret)["PASSWORD_SMTP"]
    
    # (Optional) the name of a configuration set to use for this message.
    # If you comment out this line, you also need to remove or comment out
    # the "X-SES-CONFIGURATION-SET:" header below.
    CONFIGURATION_SET = "RGPOGrants"
    
    # If you're using Amazon SES in an AWS Region other than US West (Oregon),
    # replace email-smtp.us-west-2.amazonaws.com with the Amazon SES SMTP
    # endpoint in the appropriate region.
    HOST = "email-smtp.us-west-2.amazonaws.com"
    PORT = 587
    SUBJECT = "Local Users Found on AWS Account: " + alias
    
    # for non-HTML emails
    BODY_TEXT = (
        "Amazon SES Test (Python)\r\n" "Email sent using " "AWS SDK for Python (Boto)."
    )
    BODY_HTML = """
        <html>
        <head></head>
        <body>
          <p> The following NON-APPROVED Local Users have been created on this AWS Account.
          <ul>
                """
    def is_user_approved(data):
        status = "Non-Approved"
        #    pp.pprint(data)
        for x in data:
            if x["Key"] == "Approved":
                # print("xxxx found xxxx ", t['Key'])
                status = "Approved"
    
        return status
    
    
    response = iam.list_users()
    # pp.pprint(response)
    
    for user in response["Users"]:
        tags = iam.list_user_tags(UserName=user["UserName"])
    
        result = "Non-Approved"
    
        if tags["Tags"]:
            result = is_user_approved(tags["Tags"])
            # print(result)
    
        if result == "Non-Approved":
            report = "{0} User: {1}\nCreationDate: {2}".format(
                result, user["UserName"], user["CreateDate"]
            )
            unapproved_userlist.append({report})
    
    html_string = ""
    for i in unapproved_userlist:
        temp_list = []
        temp_list = [b for b in i]
        if not temp_list:
            break
        else:
            html_string += "<pre>" + temp_list[0] + "</pre> </ br>"
    
    
    BODY_HTML += html_string
    BODY_HTML += """</u1>
           <br>
           <br>
    <p> NOTE: The Report will only be delivered if NON-APPROVED Local Users are found on this AWS Account. <p>
    <p>                          Please remediate the above issue as soon as possible. <p>
         </p>
            </body>
            </html>
                        """
    
    
    client = boto3.client("ses", region_name="us-west-2")
  
    def send_email():    
    # Create message container - the correct MIME type is multipart/alternative.
        msg = MIMEMultipart("alternative")
        msg["Subject"] = SUBJECT
        msg["From"] = email.utils.formataddr((SENDERNAME, SENDER))
        msg["To"] = RECIPIENT
        # Comment or delete the next line if you are not using a configuration set
        msg.add_header("X-SES-CONFIGURATION-SET", CONFIGURATION_SET)
    
        # Record the MIME types of both parts - text/plain and text/html.
        part1 = MIMEText(BODY_TEXT, "plain")
        part2 = MIMEText(BODY_HTML, "html")
    
        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        msg.attach(part1)
        msg.attach(part2)
    
        # Try to send the message.
        try:
            server = smtplib.SMTP(HOST, PORT)
            server.ehlo()
            server.starttls()
            # stmplib docs recommend calling ehlo() before & after starttls()
            server.ehlo()
            server.login(USERNAME_SMTP, PASSWORD_SMTP)
            server.sendmail(SENDER, RECIPIENT, msg.as_string())
            server.close()
        # Display an error message if something goes wrong.
        except Exception as e:
            print("Error: ", e)
        else:
            print("Email sent!")
            
    if len(unapproved_userlist) != 0:
        send_email()
