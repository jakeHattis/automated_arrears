import pandas as pd 
import requests
import time
from datetime import datetime, timedelta

print("Hi there! I'm going to run through the program now.")
date = datetime.now() - timedelta(days=7)
ytime = date.strftime("%Y-%m-%d")
now = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
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
arrears_formatted = daily_arrears[["Tenant", "Outstanding", 'Full Amount', 'From', 'Property', 'Agent', 'Rent Paid To']]
arrears_formatted['email'] = ''
arrears_formatted['Tenancy Code'] = ''
arrears_formatted['Proper Arrears'] = ''
arrears_formatted['Raised Invoice'] = 0
for i in range(len(arrears_formatted['Tenant'])):
    ten_name = arrears_formatted["Tenant"][i]
    outstanding = arrears_formatted['Outstanding'][i]
    if len(outstanding) < 2:
        arrears_formatted.loc[i, "Outstanding"] = 0
    else:
        outstanding = float(outstanding.split('$', 1)[1].replace(',', '').replace(")",""))
        arrears_formatted.loc[i, 'Outstanding'] = outstanding
    aDate = arrears_formatted['Rent Paid To'][i]
    fDate = arrears_formatted['From'][i]
    prop = arrears_formatted['Property'][i]
    if len(aDate) < 4:
        arrears_formatted.loc[i, 'Proper Arrears'] = 0
        arrears_formatted.loc[i, "Rent Paid To"] = ''
        aDate = ''
    else:
        arrears_formatted.loc[i, 'Proper Arrears'] = (datetime.now() - datetime.strptime(aDate, "%d/%m/%Y")).days
        arrears_formatted.loc[i, 'Rent Paid To'] = datetime.strptime(aDate, "%d/%m/%Y")
        aDate = datetime.strptime(aDate, "%d/%m/%Y")
    if len(fDate) >= 9 and len(str(aDate)) > 8:
        arrears_formatted.loc[i, 'Raised Invoice'] = (datetime.strptime(fDate, "%d/%m/%Y") - datetime.now()).days
        arrears_formatted.loc[i, 'From'] = datetime.strptime(fDate, "%d/%m/%Y")
        fDate = datetime.strptime(fDate, "%d/%m/%Y")
    else:
        arrears_formatted.loc[i, 'Raised Invoice'] = 0
    raised = arrears_formatted['Raised Invoice'][i]
    full_amount = arrears_formatted["Full Amount"][i]
    full_amount = float(full_amount.split('$', 1)[1].replace(',', '').replace(')',''))
    arrears_formatted.loc[i, "Full Amount"] = full_amount
    if raised <= 5 and raised > -3 and len(str(aDate)) > 0:
        M = datetime.now().month - fDate.month + 1
        if M > 1:
            N_Amount = full_amount/M
            outstanding = outstanding - N_Amount
            if outstanding > 0:
                arrears_formatted.loc[i, "Outstanding"] = outstanding
        else:
            pass
    for j in range(len(current_tenants["external_id"])):
        external_id = current_tenants["external_id"][j]
        email = current_tenants['email'][j]
        add = current_tenants['Address'][j]
        if prop != add:
            pass
        else:
            arrears_formatted.loc[i, 'email'] = email
            arrears_formatted.loc[i, 'Tenancy Code'] = external_id
# Exercise running through tenants that were updated and resetting those that are not present in current arrears table.
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
    print("Zeroing out users")
    for i in range(len(multiple_payloads)):
        payload = multiple_payloads[i]
        data = {'users': payload}
        zero_update_responsei = requests.post(url=post_endpoint, auth=(usr,passw), headers= headers, json=data)
        print("Number in payload: " + str(len(payload)))
        print(zero_update_responsei)
else:
    data = {'users': payload}
    auth = {usr, passw}
    headers = {"Content-Type": 'application/json'}
    print("Zeroing out users")
    zero_update_response = requests.post(url=post_endpoint, auth=(usr,passw), headers= headers, json=data)
    print("number in payload: " + str(len(payload)))
    print(zero_update_response)
time.sleep(15)
#resetting payload for updated arrears

payload = []
true_arrears = arrears_formatted[(arrears_formatted['Proper Arrears'] >= 3) & (arrears_formatted['Outstanding'] > 100.0)].reset_index()
for i in range(len(true_arrears['Tenancy Code'])):
    name = true_arrears['Tenant'][i]
    email = true_arrears['email'][i]
    external_id = true_arrears['Tenancy Code'][i]
    outstanding = true_arrears['Outstanding'][i]
    days = true_arrears['Proper Arrears'][i]
    prop_add = true_arrears['Property'][i]
    addition = {
        'name': name,
        'email': email,
        'external_id': external_id,
        'user_fields': {
            'days_in_arrears': int(days),
            'amount_outstanding': int(outstanding),
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
    print("Sending updated arrears to Zendesk")
    pa = []
    for i in range(len(multiple_payloads)):
        payload = multiple_payloads[i]
        data = {'users': payload}
        update_responsei = requests.post(url=post_endpoint, auth=(usr,passw), headers= headers, json=data)
        pa.append(update_responsei)
        print("Number in payload: " + str(len(payload)))
        print(update_responsei)
else:
    pa = []
    data = {'users': payload}
    auth = {usr, passw}
    headers = {"Content-Type": 'application/json'}
    update_response = requests.post(url=post_endpoint, auth=(usr,passw), headers= headers, json=data)
    pa.append(update_response)
    print("Sending updated arrears to Zendesk")
    print("Number in payload: " + str(len(payload)))
    print(update_response)
print("Users have been sent to Zendesk. We're just going to give it a sec before shooting out a bunch of emails :)")
time.sleep(30)

#Automated tickets and comments for tenants that are 3-4 days in arrears
for i in range(len(pa)):
    pb = pa[i]
    if pb.status_code != 200:
        print(pb.status_code + " Error was found. Exit out of program.")
        input("Exit Program")
    else:
        continue
query = "type:user days_in_arrears>2 days_in_arrears<5 updated>" + now
threeFourUrl = 'https://longview.zendesk.com/api/v2/search.json?query=' + query
usr = 'jake.hattis@longview.com.au'
passw = 'PotatoBondi3160!'
threeFour = requests.get(threeFourUrl, auth = (usr, passw)).json()
threeFourArrearsPayload = []
for i in range(len(threeFour['results'])):
    request_id = threeFour['results'][i]['id']
    prop_address = threeFour['results'][i]['user_fields']['property_address']
    prop_code = threeFour['results'][i]['user_fields']['property_code']
    n = threeFour['results'][i]['name']
    d = threeFour['results'][i]['user_fields']['days_in_arrears']
    a = threeFour['results'][i]['user_fields']['amount_outstanding']
    ticket_update = {
        'type': 'incident',
        'subject': f"**Arrears Notification** for property: {prop_address}",
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
            'html_body': f'<p>Hello {n}​,</p><p>This is a friendly reminder to advise that your monthly rental payment is now {d} days overdue. Our system shows you are owing ${a}.</p><p>We will continue to send SMS and email updates while you remain in arrears.</p><p>If you have recently processed the payment, please forward through a copy of the payment remittance and disregard this notice.</p><p>Do not hesitate to respond to this email or call us to discuss this matter further.</p><p>Warm regards,</p>',
            'public': True,
            #Setting author as Finance | LongView Real Estate
            'author_id': 387311580292
        }
    }
    threeFourArrearsPayload.append(ticket_update)
threeFourArrearsData = {'tickets': threeFourArrearsPayload}

#Automated tickets created for tenants taht are seven days in arrears. 
query = "type:user days_in_arrears:7 updated>" + now
SevenUrl = 'https://longview.zendesk.com/api/v2/search.json?query=' + query
usr = 'jake.hattis@longview.com.au'
passw = 'PotatoBondi3160!'
sevenRequest = requests.get(SevenUrl, auth = (usr, passw)).json()
sevenPayload = []
for i in range(len(sevenRequest['results'])):
    request_id = sevenRequest['results'][i]['id']
    prop_address = sevenRequest['results'][i]['user_fields']['property_address']
    prop_code = sevenRequest['results'][i]['user_fields']['property_code']
    n = sevenRequest['results'][i]['name']
    d = sevenRequest['results'][i]['user_fields']['days_in_arrears']
    a = sevenRequest['results'][i]['user_fields']['amount_outstanding']
    ticket_update = {
        'type': 'incident',
        'subject': f"**7 Days Arrears Notification** for property: {prop_address}",
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
            'html_body': f'<p>Hello {n}​,</p><p>This email is to advise that your monthly rental payment is now {d} days overdue. Our system shows you are owing ${a}.</p><p>If payment is not sent before 15 days has elapsed, a 14-day Notice To Vacate will be issued.</p><p>If you have recently processed the payment, please forward through a copy of the payment remittance and disregard this notice.</p><p>Kind regards,</p>',
            'public': True,
            'author_id': 387311580292
        }
    }
    sevenPayload.append(ticket_update)
SevenArrearsData = {'tickets': sevenPayload}
# Tickets that will be created for SS to call the tenant at 5 days in arrears
query = "type:user days_in_arrears:5 updated>" + now
fiveUrl = 'https://longview.zendesk.com/api/v2/search.json?query=' + query
usr = 'jake.hattis@longview.com.au'
passw = 'PotatoBondi3160!'
fiveRequest = requests.get(fiveUrl, auth = (usr, passw)).json()
fivePayload = []
for i in range(len(fiveRequest['results'])):
    request_id = fiveRequest['results'][i]['id']
    prop_address = fiveRequest['results'][i]['user_fields']['property_address']
    prop_code = fiveRequest['results'][i]['user_fields']['property_code']
    n = fiveRequest['results'][i]['name']
    ticket_update = {
        'type': 'task',
        'subject': f"5 day Arrears Call for property: {prop_address}",
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
            'html_body': f'Please call {n}. Our Records show they are 5 days in arrears.',
            'public': False,
        }
    }
    fivePayload.append(ticket_update)
fiveArrearsData = {'tickets': fivePayload}
#creating the over-10 days in arrears list to be sent to each of the pms.
over_10 = true_arrears[true_arrears['Proper Arrears'] >= 10]
PMemailNotification = '<p>Hi Everyone,</p><p>The following tenants are either 10 days or greater in arrears.</p>'
#PMs that will be included in the email
PMs = ['Jenna Hilton', 'Erin Crick', 'Andrew Kilsby', 'Meredith Jays', 'Lucy Black', 'Stephanie Wallace', 'Audrey Chong', 'Cassandra Williams', 'Tania Gunther', 'Lisa Yang', 'Jess hayes', 'Alisha Hinde', 'Danielle Clark', 'Olivia Scott']
#Creating the email that will be sent to the PMs
for i in range(len(PMs)):
    pm = PMs[i]
    PMemailNotification = PMemailNotification + '<h4>' + pm + '</h4>'
    pm_prop = over_10[over_10['Agent'] == pm].reset_index()
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
ten_tickets = []
pm_ids = [383510578571,384465913331,384717503591,386897750352,385533670052,388908486311,387670113511,386911509672,386297556552,384744785051,384711255811,384655325172,384617943391,384541089651,384465913171, 385129973411]
for i in range(len(pm_ids)):
    pm_id = pm_ids[i]
    ticket_update = {
            'type': 'incident',
            'subject': 'Over 10-days Arrears Notification',
            'status': 'solved',
            # Codes for PMs Order is 1.Jenna Hilton, 2.Cath, 3.Erin, 4.Andrew, 5.Meri, 6.Lucy Black, 7.Steph Wallace, 8.Lisa Yang, 9.Olivia Fraser Jones, 10.Cass Williams, 11.Tania Gunther, 12.Jess Hayes, 13.Tess Hudaverdi, 14.Audrey Chong, 15.Megan Taylor 16. Danielle Clark
            'requester_id': pm_id,
            'custom_fields': [
                {'id': 360021904892, 'value': 'tx_only'},
                {'id': 360021971611, 'value': 'team_arrears_notification'},
                {'id': 360022146692, 'value': 'property_manager'},
                {'id': 360022146732, 'value': 'outbound'}
            ],
            'comment': {
                'type': 'Comment',
                'html_body': PMemailNotification,
                'public': True,
            }
        }
    ten_tickets.append(ticket_update)
tenTicketData = {'tickets': ten_tickets}
if (len(threeFourArrearsData['tickets']) == 0) or (len(SevenArrearsData['tickets']) == 0):
    input("Emails are not being sent out. Please exit out of program.")
else:
    single_email_url = 'https://longview.zendesk.com/api/v2/tickets.json'
    bulk_email_url = 'https://longview.zendesk.com/api/v2/tickets/create_many.json'
    three_four_request = requests.post(url=bulk_email_url, auth=(usr,passw), headers=headers, json=threeFourArrearsData)
    seven_request = requests.post(url=bulk_email_url, auth=(usr,passw), headers=headers, json=SevenArrearsData)
    five_request = requests.post(url=bulk_email_url, auth=(usr,passw), headers=headers, json=fiveArrearsData)
    ten_request = requests.post(url=bulk_email_url, auth=(usr,passw), headers=headers, json=tenTicketData)
    input("Program Successful, Press Enter")
