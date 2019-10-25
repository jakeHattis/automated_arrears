import pandas as pd 
import requests
import time
from datetime import datetime, timedelta

print("Hi there! I'm going to run through the program now.")
date = datetime.now() - timedelta(days=7)
ytime = date.strftime("%Y-%m-%d")

query = "type:user days_in_arrears>0 updated>" + ytime
url = 'https://longview.zendesk.com/api/v2/search.json?query=' + query
usr = 'jake.hattis@longview.com.au'
passw = 'PotatoBondi3160!'
response = requests.get(url, auth = (usr, passw)).json()
users = response["results"]

updated_users = pd.DataFrame(columns = ['name', 'email', 'external_id'])
updated_users['name'] = updated_users['name'].astype(str)
updated_users['email'] = updated_users['email'].astype(str)
updated_users['external_id'] = updated_users['external_id'].astype(str)
for i in range(len(users)):
    name = users[i]['name']
    email = users[i]['email']
    external_id = users[i]['external_id']
    updated_users.loc[i, 'name'] = name
    updated_users.loc[i, 'email'] = email
    updated_users.loc[i, 'external_id'] = external_id
#Formatting Daily Arrears
current_tenants = pd.read_csv("currentTenants.csv")
daily_arrears = pd.read_csv("Arrears.csv")
arrears_formatted = daily_arrears[["Tenant", "Tenancy Code", "Outstanding", "Days", 'Property Code', 'Property', 'Tenancy Agent', 'Date']]
arrears_formatted['email'] = ''
arrears_formatted['Days'] = arrears_formatted['Days'].astype(int)
arrears_formatted['Proper Arrears'] = ''
for i in range(len(arrears_formatted["Tenancy Code"])):
    ten_code = arrears_formatted["Tenancy Code"][i]
    days = arrears_formatted["Days"][i]
    outstanding = arrears_formatted["Outstanding"][i]
    aDate = arrears_formatted['Date'][i]
    if len(aDate) < 10:
        arrears_formatted.loc[i, 'Proper Arrears'] = (datetime.now() - datetime.strptime(aDate, "%m-%d-%y")).days
    else:
        arrears_formatted.loc[i, 'Proper Arrears'] = (datetime.now() - datetime.strptime(aDate, "%d-%m-%Y")).days
    for j in range(len(current_tenants["external_id"])):
        external_id = current_tenants["external_id"][j]
        email = current_tenants['email'][j]
        if ten_code != external_id:
            pass
        else:
            arrears_formatted.loc[i, 'email'] = email
#Exercise running through tenants that were updated and resetting those that are not present in current arrears table.
payload = []
for j in range(len(updated_users['external_id'])):
    name_z = updated_users['name'][j]
    email_z = updated_users['email'][j]
    external_id_z = updated_users['external_id'][j]
    addition = {
        'name': name_z,
        'email': email_z,
        'external_id': external_id_z,
        'user_fields': {
            'days_in_arrears': 0,
            'amount_outstanding': 0
            }
    }
    payload.append(addition)
usr = 'jake.hattis@longview.com.au'
passw = 'PotatoBondi3160!'
post_endpoint = 'https://longview.zendesk.com/api/v2/users/create_or_update_many.json'
auth = {usr, passw}
headers = {"Content-Type": 'application/json'}
x = len(payload)
if x > 100:
    multiple_payloads = []
    y = x//100
    w = x%100
    if w > 0:
        for i in range(y):
            payloadi = payload[i*100:(i+1)*100]
            multiple_payloads.append(payloadi)
        payloadFinal = payload[(y*100):(y*100+w)]
        multiple_payloads.append(payloadFinal)
    else:
        for i in range(y):
            payloadi = payload[i*100:(i+1)*100]
            multiple_payloads.append(payloadi)
    for i in range(len(multiple_payloads)):
        payload = multiple_payloads[i]
        data = {'users': payload}
        # zero_update_responsei = requests.post(url=post_endpoint, auth=(usr,passw), headers= headers, json=data)
else:
    data = {'users': payload}
    auth = {usr, passw}
    headers = {"Content-Type": 'application/json'}
    # zero_update_response = requests.post(url=post_endpoint, auth=(usr,passw), headers= headers, json=data)

print(len(payload))
time.sleep(15)
#resetting payload for updated arrears

payload = []
true_arrears = arrears_formatted[(arrears_formatted['Proper Arrears'] >= 3) & (arrears_formatted['Outstanding'] > 500)].reset_index()
for i in range(len(true_arrears['Tenancy Code'])):
    name = true_arrears['Tenant'][i]
    email = true_arrears['email'][i]
    external_id = true_arrears['Tenancy Code'][i]
    outstanding = true_arrears['Outstanding'][i]
    days = true_arrears['Proper Arrears'][i]
    prop_code = true_arrears['Property Code'][i]
    prop_add = true_arrears['Property'][i]
    addition = {
        'name': name,
        'email': email,
        'external_id': external_id,
        'user_fields': {
            'days_in_arrears': int(days),
            'amount_outstanding': int(outstanding),
            'property_code': prop_code,
            'property_address': prop_add
             }
        }
    payload.append(addition)
#Sending the updated users to Zendesk
x = len(payload)
if x > 100:
    multiple_payloads = []
    y = x//100
    w = x%100
    if w > 0:
        for i in range(y):
            payloadi = payload[i*100:(i+1)*100]
            multiple_payloads.append(payloadi)
        payloadFinal = payload[(y*100):(y*100+w)]
        multiple_payloads.append(payloadFinal)
    else:
        for i in range(y):
            payloadi = payload[i*100:(i+1)*100]
            multiple_payloads.append(payloadi)
    for i in range(len(multiple_payloads)):
        payload = multiple_payloads[i]
        data = {'users': payload}
        # update_responsei = requests.post(url=post_endpoint, auth=(usr,passw), headers= headers, json=data)
else:
    data = {'users': payload}
    auth = {usr, passw}
    headers = {"Content-Type": 'application/json'}
    # update_response = requests.post(url=post_endpoint, auth=(usr,passw), headers= headers, json=data)
print(len(payload))

time.sleep(30)
# Automated tickets and comments for tenants that are 3-4 days in arrears
print("Users have been sent to Zendesk. We're just going to give it a sec before shooting out a bunch of emails :)")
if update_response.status_code == 200:
    query = "type:user days_in_arrears>2 days_in_arrears<5"
    threeFourUrl = 'https://longview.zendesk.com/api/v2/search.json?query=' + query
    usr = 'jake.hattis@longview.com.au'
    passw = 'PotatoBondi3160!'
    threeFour = requests.get(threeFourUrl, auth = (usr, passw)).json()
    threeFourArrearsPayload = []
    for i in range(len(threeFour['results'])):
        request_id = threeFour['results'][i]['id']
        prop_address = threeFour['results'][i]['user_fields']['property_address']
        prop_code = threeFour['results'][i]['user_fields']['property_code']
        ticket_update = {
            'type': 'incident',
            'subject': "**Arrears Notification** for property: " + str(prop_address),
            'status': 'solved',
            'requester_id': request_id,
            'custom_fields': [
                {'id': 360021904892, 'value': 'tx_only'},
                {'id': 360021971591, 'value': prop_code},
                {'id': 360021971611, 'value': 'arrears_-_3-4_days'},
                {'id': 360022146692, 'value': 'tenant'},
                {'id': 360022146732, 'value': 'outbound'}
            ],
            'comment': {
                'type': 'Comment',
                'html_body': '<p>Hello {{ticket.requester.name}}​,</p><p>This is a friendly reminder to advise that your monthly rental payment is now {{ticket.requester.custom_fields.days_in_arrears}} days overdue. Our system shows you are owing ${{ticket.requester.custom_fields.amount_outstanding}}.</p><p>We will continue to send SMS and email updates while you remain in arrears.</p><p>Please ensure this is paid at your earliest possible convenience, to prevent any further legal action being instigated.</p><p>If you have recently processed the payment, please forward through a copy of the payment remittance and disregard this notice.</p><p>Do not hesitate to respond to this email or call us to discuss this matter further.</p><p>Warm regards,</p>',
                'public': True,
                'author_id': 383909195851
            }
        }
        threeFourArrearsPayload.append(ticket_update)
    threeFourArrearsData = {'tickets': threeFourArrearsPayload}
    #Automated tickets created for tenants taht are seven days in arrears. 
    query = "type:user days_in_arrears:7"
    SevenUrl = 'https://longview.zendesk.com/api/v2/search.json?query=' + query
    usr = 'jake.hattis@longview.com.au'
    passw = 'PotatoBondi3160!'
    sevenRequest = requests.get(SevenUrl, auth = (usr, passw)).json()
    sevenPayload = []
    for i in range(len(sevenRequest['results'])):
        request_id = sevenRequest['results'][i]['id']
        prop_address = sevenRequest['results'][i]['user_fields']['property_address']
        prop_code = sevenRequest['results'][i]['user_fields']['property_code']
        ticket_update = {
            'type': 'incident',
            'subject': "**7 Days Arrears Notification** for property: " + str(prop_address),
            'status': 'solved',
            'requester_id': request_id,
            'custom_fields': [
                {'id': 360021904892, 'value': 'tx_only'},
                {'id': 360021971591, 'value': prop_code},
                {'id': 360021971611, 'value': 'arrears_-_7_days'},
                {'id': 360022146692, 'value': 'tenant'},
                {'id': 360022146732, 'value': 'outbound'}
            ],
            'comment': {
                'type': 'Comment',
                'html_body': '<p>Hello {{ticket.requester.name}}​,</p><p>This email is to advise that your monthly rental payment is now {{ticket.requester.custom_fields.days_in_arrears}} days overdue. Our system shows you are owing ${{ticket.requester.custom_fields.amount_outstanding}}.</p><p>If payment is not sent before 15 days has elapsed, a 14-day Notice To Vacate will be issued.</p><p>If you have recently processed the payment, please forward through a copy of the payment remittance and disregard this notice.</p><p>Kind regards,</p>',
                'public': True,
                'author_id': 383909195851
            }
        }
        sevenPayload.append(ticket_update)
    SevenArrearsData = {'tickets': sevenPayload}
    # Tickets that will be created for SS to call the tenant at 5 days in arrears
    query = "type:user days_in_arrears:5"
    fiveUrl = 'https://longview.zendesk.com/api/v2/search.json?query=' + query
    usr = 'jake.hattis@longview.com.au'
    passw = 'PotatoBondi3160!'
    fiveRequest = requests.get(fiveUrl, auth = (usr, passw)).json()
    fivePayload = []
    for i in range(len(fiveRequest['results'])):
        request_id = fiveRequest['results'][i]['id']
        prop_address = fiveRequest['results'][i]['user_fields']['property_address']
        prop_code = fiveRequest['results'][i]['user_fields']['property_code']
        ticket_update = {
            'type': 'task',
            'subject': "5 day Arrears Call for property: " + str(prop_address),
            'status': 'new',
            'requester_id': request_id,
            'custom_fields': [
                {'id': 360021904892, 'value': 'tx_only'},
                {'id': 360021971591, 'value': prop_code},
                {'id': 360021971611, 'value': 'arrears_call_--_5_days'},
                {'id': 360022146692, 'value': 'tenant'},
                {'id': 360022146732, 'value': 'outbound'}
            ],
            'comment': {
                'type': 'Comment',
                'html_body': 'Please call {{ticket.requester.name}}. Our Records show they are 5 days in arrears.',
                'public': False,
            }
        }
        fivePayload.append(ticket_update)
    fiveArrearsData = {'tickets': fivePayload}

    over_10 = true_arrears[true_arrears['Days'] >= 10]
    PMemailNotification = '<p>Hi Everyone,</p><p>The following tenants are either 10 days or greater in arrears.</p>'
    #PMs that will be included in the email
    PMs = ['Jenna Hilton', 'Erin Crick', 'Andrew Kilsby', 'Meredith Jays', 'Lucy Black', 'Stephanie Wallace', 'Audrey Chong', 'Cassandra Williams', 'Tania Gunther', 'Lisa Yang', 'Olivia Fraser-Jones', 'Jess hayes', 'Tess Hudaverdi']
    #Creating the email that will be sent to the PMs
    for i in range(len(PMs)):
        pm = PMs[i]
        PMemailNotification = PMemailNotification + '<h4>' + pm + '</h4>'
        pm_prop = over_10[over_10['Tenancy Agent'] == pm].reset_index()
        if len(pm_prop['Property']) == 0:
            PMemailNotification = PMemailNotification + '<p>none :)</p>'
        for j in range(len(pm_prop['Property'])):
            over10_prop =pm_prop['Property'][j]
            if j == 0:
                PMemailNotification = PMemailNotification + '<p>' + over10_prop + '</p>'
            else:
                over10_propbefore = pm_prop['Property'][j-1]
                if over10_propbefore == over10_prop:
                    continue
                else:
                    PMemailNotification = PMemailNotification + '<p>' + over10_prop + '</p>'
            
        PMemailNotification = PMemailNotification + '<p></p>'
    ticket_update = [{
            'type': 'incident',
            'subject': 'Over 10-days Arrears Notification',
            'status': 'solved',
            # Codes for PMs Order is Jenna Hilton, Cath, Erin, Andrew, Meri, Lucy Black, Steph Wallace, Lisa Yang, Olivia Fraser Jones, Cass Williams, Tania Gunther, Jess Hayes, Tess Hudaverdi, Audrey Chong, Megan Taylor
            'email_cc_ids': [383510578571,384465913331,384717503591,386897750352, 385533670052, 388908486311, 387670113511, 386911509672, 386297556552, 384744785051, 384711255811, 384655325172, 384617943391, 384541089651, 384465913171],
            'custom_fields': [
                {'id': 360021904892, 'value': 'tx_only'},
                {'id': 360021971611, 'value': 'team_arrears_notification'},
                {'id': 360022146692, 'value': 'property_manager'},
                {'id': 360022146732, 'value': 'outbound'}
            ],
            'comment': {
                'type': 'Comment',
                'html_body': PMemailNotification,
                # Author Id is set to Shaun
                'author_id': 383909195851,
                'public': True,
            }},
            {
            'type': 'task',
            'subject': "Please send SMS Arrears Notifications, Receipting is Completed",
            'status': 'new',
            'custom_fields': [
                {'id': 360021904892, 'value': 'tx_only'},
                {'id': 360021971611, 'value': 'arrears_sms_notification'},
                {'id': 360022146692, 'value': 'tenant'},
                {'id': 360022146732, 'value': 'outbound'}
            ],
            'comment': {
                'type': 'Comment',
                'html_body': 'Chloe finished the receipting. You can go ahead and send out the SMS arrears notifications. You are awesome!',
                'public': False,
            }
        }]
    tenTicketData = {'ticket': ticket_update}


    # single_email_url = 'https://longview.zendesk.com/api/v2/tickets.json'
    # bulk_email_url = 'https://longview.zendesk.com/api/v2/tickets/create_many.json'
    # three_four_request = requests.post(url=bulk_email_url, auth=(usr,passw), headers=headers, json=threeFourArrearsData)
    # seven_request = requests.post(url=bulk_email_url, auth=(usr,passw), headers=headers, json=SevenArrearsData)
    # five_request = requests.post(url=bulk_email_url, auth=(usr,passw), headers=headers, json=fiveArrearsData)
    # ten_request = requests.post(url=single_email_url, auth=(usr,passw), headers=headers, json=tenTicketData)
    # input("Program Successful, Press Enter")