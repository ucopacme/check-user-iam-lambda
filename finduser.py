import boto3
import time
from botocore.exceptions import ClientError
#pp = pprint.PrettyPrinter(indent=4)


def lambda_handler(event, context):
    iam = boto3.client('iam')

iam = boto3.client('iam')
alias = boto3.client('iam').list_account_aliases()['AccountAliases'][0]
unapproved_userlist = []
SENDER =  alias + "<david.rivera@ucop.edu>"
RECIPIENT = "david.rivera@ucop.edu"
AWS_REGION = "us-west-2"   #change if sending from another region
CHARSET = "UTF-8"
SUBJECT = "Local Users Found on AWS Account: "  + alias
 # for non-HTML emails
BODY_TEXT = ("Amazon SES Test (Python)\r\n"
             "Email sent using "
             "AWS SDK for Python (Boto)."
             )
BODY_HTML = """
    <html>
    <head></head>
    <body>
      <p> The following NON-APPROVED Local Users have been created on this AWS Account.
      <ul>
            """

def is_user_approved(data):
    status = 'Non-Approved'
#    pp.pprint(data)
    for x in data:
         if x['Key'] == 'Approved':
                   #print("xxxx found xxxx ", t['Key'])
                   status = 'Approved'

    return status


response = iam.list_users()
#pp.pprint(response)

for user in response['Users']:
    tags = iam.list_user_tags(UserName = user['UserName'])

    result = 'Non-Approved'

    if tags['Tags']:
        result = is_user_approved(tags['Tags'])
        #print(result)

    if result =="Non-Approved":
         report = ("{0} User: {1}\nCreationDate: {2}".format(result, user['UserName'], user['CreateDate']))
         unapproved_userlist.append({report})

html_string = ''
for i in unapproved_userlist:
    temp_list = []
    temp_list = [b for b in i]
    if not temp_list:
        break
    else:
        html_string += "<pre>" + temp_list[0] + "</pre> </ br>"


BODY_HTML += html_string
BODY_HTML +="""</u1>
       <br>
       <br>
<p> NOTE: The Report will only be delivered if NON-APPROVED Local Users are found on this AWS Account. <p>
<p>                          Please remediate the above issue as soon as possible. <p>
     </p>
        </body>
        </html>
                    """


client = boto3.client('ses', region_name="us-west-2")


# importance of 438 - this is the default number of letters in email if no non-approved users are found.
# If the default message change, you must update the length or it will always email even when there is
# nothing to email.

# unpound to verify message length
#print(len(BODY_HTML))

if len(BODY_HTML) != 438:

    # Try to send the email.
    try:
    # Provide the contents of the email.
      #response = client.send_email(
        response = client.send_email(
          Destination={
              'ToAddresses': [RECIPIENT
             ],
          },
          Message={
              'Body': {
                  'Html': {
                      'Charset': CHARSET,
                      'Data': BODY_HTML,


                   },
                   'Text': {
                       'Charset': CHARSET,
                       'Data': BODY_TEXT,

                   },
               },
               'Subject': {
                   'Charset': CHARSET,
                   'Data': SUBJECT,
               },
          },
          Source=SENDER,
        )
# Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        #time.sleep(10)
        print("Email sent! Message ID:"),
        print(response['MessageId'])
