import pandas as pd 
import requests
import time
from datetime import datetime, timedelta

date = datetime.now() - timedelta(days=7)
time = date.strftime("%Y-%m-%d")

query = "type:user days_in_arrears>0 updated>" + time
url = 'https://longview.zendesk.com/api/v2/search.json?query=' + query
usr = 'jake.hattis@longview.com.au'
passw = 'PotatoBondi3160!'
response = requests.get(url, auth = (usr, passw)).json()
users = response["results"]

updated_users = pd.DataFrame(columns = ['name', 'email', 'external_id'])
updated_users['name'] = updated_users['name'].astype(str)
updated_users['email'] = updated_users['email'].astype(str)
updated_users['external_id'] = updated_users['external_id'].astype(str)
updated_users.dtypes
for i in range(len(users)):
    name = users[i]['name']
    email = users[i]['email']
    external_id = users[i]['external_id']
    updated_users.loc[i, 'name'] = name
    updated_users.loc[i, 'email'] = email
    updated_users.loc[i, 'external_id'] = external_id


current_tenants = pd.read_csv("currentTenants.csv")
daily_arrears = pd.read_csv("Arrears.csv")
arrears_formatted = daily_arrears[["Tenant", "Tenancy Code", "Outstanding", "Days", 'Property Code', 'Property', 'Tenancy Agent']]
arrears_formatted['email'] = ''
arrears_formatted['Outstanding'] = arrears_formatted['Outstanding'].astype(str)
arrears_formatted['Days'] = arrears_formatted['Days'].astype(str)

for i in range(len(arrears_formatted["Tenancy Code"])):
    ten_code = arrears_formatted["Tenancy Code"][i]
    days = arrears_formatted["Days"][i]
    outstanding = arrears_formatted["Outstanding"][i]
    for j in range(len(current_tenants["external_id"])):
        external_id = current_tenants["external_id"][j]
        email = current_tenants['email'][j]
        if ten_code != external_id:
            pass
        else:
            arrears_formatted.loc[i, 'email'] = email
#Exercise running through tenants that were updated and resetting those that are not present in current arrears table, while changing those that are still present.
payload = []
for j in range(len(updated_users['external_id'])):
    name_z = updated_users['name'][j]
    email_z = updated_users['email'][j]
    external_id_z = updated_users['external_id'][j]
    external_id = ''
    for i in range(len(arrears_formatted['Tenancy Code'])):
        name = arrears_formatted['Tenant'][i]
        email = arrears_formatted['email'][i]
        external_id = arrears_formatted['Tenancy Code'][i]
        outstanding = arrears_formatted['Outstanding'][i]
        days = arrears_formatted['Days'][i]
        prop_code = arrears_formatted['Property Code'][i]
        prop_add = arrears_formatted['Property'][i]
        if external_id_z == external_id:
            addition = {
                'name': name_z,
                'email': email_z,
                'external_id': external_id_z,
                'user_fields': {
                    'days_in_arrears': days,
                    'amount_outstanding': outstanding,
                    'property_code': prop_code,
                    'property_address': prop_add
                }
            }
            payload.append(addition)
            break
        else:
            pass
    if external_id == external_id_z:
        pass
    else:
        addition = {
            'name': name_z,
            'email': email_z,
            'external_id': external_id_z,
            'user_fields': {
                'days_in_arrears': 0,
                'amount_outstanding': 0,
                'property_code': prop_code,
                'property_address': prop_add
            }
        }
        payload.append(addition)
#running through users again to add in new tenants that are in arrears -- packaging them in the payload array.
for i in range(len(arrears_formatted['Tenancy Code'])):
    name = arrears_formatted['Tenant'][i]
    email = arrears_formatted['email'][i]
    external_id = arrears_formatted['Tenancy Code'][i]
    outstanding = arrears_formatted['Outstanding'][i]
    days = arrears_formatted['Days'][i]
    prop_code = arrears_formatted['Property Code'][i]
    prop_add = arrears_formatted['Property'][i]
    already_added = ''
    for j in range(len(payload)):
        already_added = payload[j]['external_id']
        if already_added != external_id:
            pass
        else:
            break
    if already_added == external_id:
        continue
    else:
        addition = {
            'name': name,
            'email': email,
            'external_id': external_id,
            'user_fields': {
                'days_in_arrears': days,
                'amount_outstanding': outstanding,
                'property_code': prop_code,
                'property_address': prop_add
                }
            }
        payload.append(addition)
#Sending the updated users to Zendesk
usr = 'jake.hattis@longview.com.au'
passw = 'PotatoBondi3160!'
post_endpoint = 'https://longview.zendesk.com/api/v2/users/create_or_update_many.json'
data = {'users': payload}
auth = {usr, passw}
headers = {"Content-Type": 'application/json'}
update_response = requests.post(url=post_endpoint, auth=(usr,passw), headers= headers, json=data)

# Automated tickets and comments for tenants that are 3-4 days in arrears
print("Users have been sent to Zendesk. We're just going to give it a sec before shooting out a bunch of emails :)")
time.sleep(20)
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
            'author_id': 383909195851,
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
            'author_id': 383909195851,
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

    over_10 = arrears_formatted[arrears_formatted['Days'] >= 10]
    PMemailNotification = '<p>Hi Everyone,</p><p>The following tenants are either 10 days or greater in arrears.</p>'
    #PMs that will be included in the email
    PMs = ['Mal Younes', 'Erin Crick', 'Andrew Kilsby', 'Meredith Jays']
    #Creating the email that will be sent to the PMs
    for i in range(len(PMs)):
        pm = PMs[i]
        PMemailNotification = PMemailNotification + '<h2>' + pm + '</h2>'
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
    #Need to add PUT requests for each payloads
    ticket_update = {
            'type': 'incident',
            'subject': 'Over 10-days Arrears Notification',
            'status': 'solved',
            # Codes for PMs Order is Mal, Cath, Erin, Andrew, Meri
            'email_cc_ids': [383510578571,384465913331,384717503591,386897750352, 385533670052],
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
            }
        }
    tenTicketData = {'tickets': ticket_update}
    single_email_url = 'https://longview.zendesk.com/api/v2/tickets.json'
    bulk_email_url = 'https://longview.zendesk.com/api/v2//api/v2/tickets/create_many.json'
    three_four_request = requests.post(url=bulk_email_url, auth=(usr,passw), headers=headers, json=threeFourArrearsData)
    seven_request = requests.post(url=bulk_email_url, auth=(usr,passw), headers=headers, json=SevenArrearsData)
    ten_request = requests.post(url=single_email_url, auth=(usr,passw), headers=headers, json=tenTicketData)