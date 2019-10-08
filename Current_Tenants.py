import pandas as pd 
import requests
from datetime import datetime, timedelta

date = datetime.now() - timedelta(days=7)
time = date.strftime("%Y-%m-%d")

query = "type:user days_in_arrears>0 updated>" + time
url = 'https://longview.zendesk.com/api/v2/search.json?query=' + query
usr = 'jake.hattis@longview.com.au'
passw = 'PotatoBondi3160!'
response = requests.get(url, auth = (usr, passw)).json()
users = response["results"]
len(users)

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
arrears_formatted = daily_arrears[["Tenant", "Tenancy Code", "Outstanding", "Days"]]
arrears_formatted['email'] = ''
arrears_formatted['Outstanding'] = arrears_formatted['Outstanding'].astype(str)
arrears_formatted['Days'] = arrears_formatted['Days'].astype(str)
arrears_formatted.dtypes
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
        if external_id_z == external_id:
            addition = {
                'name': name_z,
                'email': email_z,
                'external_id': external_id_z,
                'user_fields': {
                    'days_in_arrears': days,
                    'amount_outstanding': outstanding
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
                'amount_outstanding': 0
            }
        }
        payload.append(addition)

for i in range(len(arrears_formatted['Tenancy Code'])):
    name = arrears_formatted['Tenant'][i]
    email = arrears_formatted['email'][i]
    external_id = arrears_formatted['Tenancy Code'][i]
    outstanding = arrears_formatted['Outstanding'][i]
    days = arrears_formatted['Days'][i]
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
                'amount_outstanding': outstanding
                }
            }
        payload.append(addition)
usr = 'jake.hattis@longview.com.au'
passw = 'PotatoBondi3160!'
post_endpoint = 'https://longview.zendesk.com/api/v2/users/create_or_update_many.json'
data = {'users': payload}
auth = {usr, passw}
headers = {"Content-Type": 'application/json'}
update_response = requests.post(url=post_endpoint, auth=(usr,passw), headers= headers, json=data)
input("Jolly Ho! The program was successful. Press Enter! Status Code: " + str(update_response.status_code))