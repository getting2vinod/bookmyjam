from flask import Flask, request, render_template, redirect, url_for, session
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import datetime


app = Flask(__name__)
app.secret_key = "thisismyveryloooongsecretkey"

# Initialize Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'proud-device-436515-b7-039323121352.json'  # Update this path
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

SHEET_ID = '19Bt8DrXW7l-tAPskOiY9prwWFw7WZ5JHyusnT-54EmM'
RANGE_NAME = 'Sheet1!A2:J'  # Adjust range as needed
ADMIN_RANGE_NAME = 'Sheet2!A1:B' 

@app.route('/')
def index():
    session.clear()
    return render_template('index.html')

def build_list(name_to_filter):
    service = build('sheets', 'v4', credentials=creds)
    result = service.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])
    ndate = datetime.datetime.now() + datetime.timedelta(days=-1) #datetime.strptime(date_string, "%Y-%m-%d")
    
    if session.get("isadmin") == None:
        # Filter by name
        filtered_values = [row for row in values if row and row[1] == name_to_filter and datetime.datetime.strptime(row[3], "%Y-%m-%d") >= ndate]
    else:
        filtered_values = [row for row in values if row and datetime.datetime.strptime(row[3], "%Y-%m-%d") >= ndate]
        
    
    filtered_values.sort(key=lambda x: (datetime.datetime.strptime(x[3], '%Y-%m-%d'),datetime.datetime.strptime(x[4], '%H:%M')))
    return filtered_values


@app.route('/auth', methods=['POST'])
def auth():
    session.clear()
    name_to_filter = request.form['mobile']
    passkey = request.form.get("passkey")
    service = build('sheets', 'v4', credentials=creds)
    if(passkey):       
       result = service.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=ADMIN_RANGE_NAME).execute()
       values = result.get('values', [])
       filtered_values = [row for row in values if row and row[0] == name_to_filter]
       print(filtered_values[0][1])
       if filtered_values and passkey == filtered_values[0][1]:
           session["isadmin"] = True
    session["name_to_filter"] = name_to_filter
    return redirect('/list')

@app.route('/list', methods=['GET'])
def new_and_list():
    filtered_values = build_list(name_to_filter=session['name_to_filter'])    
    return render_template('home.html', filtered_values=filtered_values, mobile=session['name_to_filter'], is_admin=session.get('isadmin'))

@app.route('/delete', methods=['POST'])
def delete():
    row = request.form['delrowid']
    column = "G" #will be fixed for row
    new_value = 'Cancelled'
    mobile = request.form['delrowmobile']

    service = build('sheets', 'v4', credentials=creds)
    range_name = f'Sheet1!{column}{row}'  # Example: "Sheet1!A2"

    body = {
        'values': [[new_value]]
    }

    service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()

    return redirect('/list')

@app.route('/schedule', methods=['POST'])
def schedule():
    Mobile = request.form['Mobile']
    Name = request.form['Name']
    Date = request.form['Date']
    Time = request.form['Time']
    Duration = request.form['Duration']

    service = build('sheets', 'v4', credentials=creds)
    status_val = '=if(INDIRECT(ADDRESS(row(),column()+1))="","Pay Now",if(INDIRECT(ADDRESS(row(),column()+3)),"Confirmed","Approval Pending"))'
    values = [["=Row()", Mobile, Name, Date, Time, Duration,status_val]]  
    
    body = {
        'values': values
    }
    service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=RANGE_NAME,
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()

    return redirect('/list')

@app.route('/confirm', methods=['POST'])
def update_confirm():
    row = request.form['confirmrowid']     
    columnApproval = "J" #will be fixed for row for approval checkbox
   
    service = build('sheets', 'v4', credentials=creds)
       
    #can be improved with one call
    rangeApproval_name = f'Sheet1!{columnApproval}{row}' 
    bodyApproval = {
        'values': [[True]]
    }
    service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=rangeApproval_name,
        valueInputOption='RAW',
        body=bodyApproval
    ).execute()
    return redirect('/list')
    
@app.route('/paymentconfirm', methods=['POST'])
def update_payment():
    row = request.form['payrowid']
    column = "H" #will be fixed for row
    columnApproval = "J" #will be fixed for row for approval checkbox
    new_value = request.form['payref']
    mobile = request.form['payrowmobile']

    service = build('sheets', 'v4', credentials=creds)
    range_name = f'Sheet1!{column}{row}'  # Example: "Sheet1!A2"

    body = {
        'values': [[new_value]]
    }

    service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()

    #can be improved with one call
    rangeApproval_name = f'Sheet1!{columnApproval}{row}' 
    bodyApproval = {
        'values': [[False]]
    }
    service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=rangeApproval_name,
        valueInputOption='RAW',
        body=bodyApproval
    ).execute()

    return redirect('/list')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
