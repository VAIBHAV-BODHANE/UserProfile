from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.urls import reverse

from userprofile.forms import RegisterForm, UserDetailsForm
from userprofile.models import UserProfile, gender_choices, desi_choices

import csv, os, io, json, base64
from datetime import datetime

# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.client import OAuth2WebServerFlow, FlowExchangeError
from google.oauth2.credentials import Credentials
# from googleapiclient.discovery import build


def register(request):
    if request.method == 'POST':
        print(request.FILES)
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            # email = form.cleaned_data.get('email')
            name = form.cleaned_data.get('name')
            messages.success(request, f"Welcome {name}, your account is created!")
            return redirect('uprofile:login')
    else:
        form = RegisterForm()

    return render(request, 'userprofile/register.html', {'form': form})


@login_required(login_url='uprofile:login')
def home(request):
    search_value = request.GET.get('search')
    print(search_value)
    if not search_value:
        user = UserProfile.objects.all().values_list('id','name', 'designation', 'gender', 'dob', 'doj', 'manager')
    else:
        print('here')
        user = UserProfile.objects.filter(Q(name__icontains=search_value) | Q(email__icontains=search_value) | Q(designation__icontains=search_value) | Q(manager__icontains=search_value)).values_list('id','name', 'designation', 'gender', 'dob', 'doj', 'manager')
        print(user)
    return render(request, 'userprofile/home.html', {'user_list': user, 'gender_choices': dict(gender_choices), 'desig_choices': dict(desi_choices)})


@login_required(login_url='uprofile:login')
def user_details(request, empid):
    emp = UserProfile.objects.filter(id=empid).first()
    print(emp.id)
    if request.method == 'POST':
        print('here')
        form = UserDetailsForm(request.POST, request.FILES, instance=emp)
        print(form.is_valid())
        if form.is_valid():
            form.save()
            return redirect('uprofile:home')
        else:
            print(form.errors)
    else:
        # emp = UserProfile.objects.filter(id=empid).first()
        form = UserDetailsForm(instance=emp)
    
    # service = authenticate_gmail_api(request)

    # results = service.users().messages().list(userId='me', labelIds=['INBOX']).execute()
    # messages = results.get('messages', [])

    # email_data = []

    # if messages:
    #     for message in messages:
    #         msg = service.users().messages().get(userId='me', id=message['id']).execute()
    #         subject = None
    #         for header in msg['payload']['headers']:
    #             if header['name'] == 'Subject':
    #                 subject = header['value']
    #                 break

    #         email_data.append({
    #             'id': message['id'],
    #             'subject': subject
    #         })

    return render(request, 'userprofile/user_details.html', {"form": form, 'instance': emp, 'is_pic': True if emp.pic else False})


@login_required(login_url='uprofile:login')
def delete_profile(request,empid):
    user = UserProfile.objects.filter(id=empid).first()
    user.delete()
    if request.user == user:
        return redirect('uprofile:login')
    return redirect('uprofile:home')


@login_required(login_url='uprofile:login')
def export_profile(request, empid):
    print(empid)
    user = UserProfile.objects.filter(id=empid).values('id', 'name', 'email', 'gender', 'dob', 'doj', 'designation', 'manager', 'last_login', 'is_active').first()
    print(user)
    if not user:
        messages.error(request, "Profile does not exist!")
        return redirect('uprofile:home')
    
    fields = list(user.keys())

    data = []
    data.append(user)
    print(data)

    filename = '_'.join(user['name'].split(' ')) + '_' + ''.join('_'.join(str(datetime.now(tz=settings.LOCAL_TIME_ZONE)).split(' ')).split('.')[0]).replace('-','_').replace(':','_') + '.csv'

    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(filename)

    # with open(filename, 'w') as csvfile:
    writer = csv.DictWriter(response,fieldnames=fields)
    writer.writeheader()
    writer.writerows(data)

    # messages.success(request, "Profile successfully downloaded!")
    return response


@login_required(login_url='uprofile:login')
def export_all_profile(request):
    user = UserProfile.objects.all().values('id', 'name', 'email', 'gender', 'dob', 'doj', 'designation', 'manager', 'last_login', 'is_active')
    if not len(user):
        messages.error(request, "No profile found!")
        return redirect('uprofile:home')
    
    fields = list(user[0].keys())
    print(fields)

    data = []
    for i in user:
        data.append(i)
    print(data)

    filename = 'all_profile_' + ''.join('_'.join(str(datetime.now(tz=settings.LOCAL_TIME_ZONE)).split(' ')).split('.')[0]).replace('-','_').replace(':','_') + '.csv'

    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(filename)

    # with open(filename, 'w') as csvfile:
    writer = csv.DictWriter(response,fieldnames=fields)
    writer.writeheader()
    writer.writerows(data)

    # messages.success(request, "Profile successfully downloaded!")
    return response


# def authenticate_gmail_api(request):
#     creds = None

#     if 'token' in request.session:
#         creds = Credentials.from_authorized_user_info(request.session['token'])

#     if not creds or not creds.valid:
#         flow = InstalledAppFlow.from_client_config(settings.GMAIL_API_CREDENTIALS, ['https://www.googleapis.com/auth/gmail.send'])
#         creds = flow.run_local_server(port=0)

#     request.session['token'] = creds.to_json()

#     service = build('gmail', 'v1', credentials=creds)
#     return service


@login_required(login_url='uprofile:login')
def add_users(request):
    if request.method == 'POST':
        file = request.FILES['inpt']
        decoded_file = file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        data = []
        keys = {}
        for i,j in enumerate(csv.reader(io_string, delimiter=',', quotechar='|')):
            dt = keys.copy()
            if i == 0:
                for k in j:
                    keys[k] = None
                continue
            for key,value in zip(dt.keys(),j):
                if key == 'email' and (value == '' or value == None):
                    for a,b in keys.items():
                        keys[a] = None
                    break
                dt[key]=value
            if dt['email'] == None:
                continue
            data.append(dt)
        print(data)
        for user in data:
            password = user.pop('password')
            user = UserProfile(**user)
            user.set_password(password)
            user.save()
        messages.success(request, "Users Add Successfully!")
    return render(request, 'userprofile/add_users.html', )


@login_required(login_url='uprofile:login')
def sample_csv(request):
    fields = ['name', 'email', 'designation', 'gender', 'doj', 'dob', 'manager', 'password']
    rows = [['', '', 'IT/S/CS', 'M/F/O', 'yyyy-mm-dd', 'yyyy-mm-dd', '']]
    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename=' + os.path.basename('add_user.csv')
    writer = csv.writer(response)
    writer.writerow(fields)
    writer.writerows(rows)
    return response


flow = OAuth2WebServerFlow(
    client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
    client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
    scope=['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send'],
    redirect_uri='http://127.0.0.1:8000/user/oauth2callback',  # Should match your OAuth credentials
)

def oauth2callback(request):
    print('here')
    if 'code' not in request.GET:
        # The user denied access or something went wrong
        return HttpResponse('Access denied or error occurred.')

    try:
        # Exchange the authorization code for credentials
        credentials = flow.step2_exchange(request.GET['code'])
    except FlowExchangeError:
        return HttpResponse('Failed to exchange authorization code for credentials.')

    # Store the credentials in the Django session (you may want to use a database for production)
    request.session['credentials'] = credentials.to_json()

    # Redirect to a success page or display a message
    return HttpResponseRedirect(reverse('uprofile:list_inbox_emails'))


SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']

def list_inbox_emails(request):
    try:
        # Load stored credentials from the Django session
        credentials_info = request.session.get('credentials')
        credentials_dict = json.loads(credentials_info)
        print(credentials_dict)
        credentials = Credentials.from_authorized_user_info(credentials_dict, scopes=SCOPES)

        # Create a Gmail API service
        service = build('gmail', 'v1', credentials=credentials)

        # Call the Gmail API to list inbox emails
        results = service.users().messages().list(userId='me', labelIds=['INBOX']).execute()
        msg = results.get('messages', [])
        # print(messages)

        email_details = []
        for thread in range(15):
            message_data = service.users().messages().get(userId='me', id=msg[thread]['id']).execute()
            subject = None
            content = None
            date = None

            payload = message_data['payload']
            headers = payload['headers']

            for header in message_data['payload']['headers']:
                if header['name'] == 'Subject':
                    subject = header['value']
                if header['name'] == 'Content-Type':
                    if 'text/plain' in header['value']:
                        payload = message_data['payload']
                        content = payload['body']['data']
                        content = base64.urlsafe_b64decode(content).decode('utf-8')

            if 'parts' in payload.keys() and content == None:
                for part in payload['parts']:
                    if 'text/plain' in part['mimeType']:
                        # If the part contains plain text content
                        try:
                            content = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        except Exception as e:
                            print(e)

            for header in headers:
                if header['name'] == 'Subject':
                    subject = header['value']
                if header['name'] == 'Date':
                    date = header['value'].split(' +')[0]
            print(content)
            email_details.append({
                'subject': subject,
                'content': content[:100] + '...' if content else content ,
                'date': date,
                'id': msg[thread]['id']
            })
            print(subject)
        print(email_details)
        # Process the messages or render them in a template
        return render(request, 'userprofile/email.html', {'data': email_details})

    except HttpError as e:
        # Handle API errors (e.g., invalid credentials)
        messages.error(request, str(e))
        request.session['credentials'] = None
        return redirect('uprofile:home')

    except KeyError as e:
        # Handle the case where credentials are missing or expired
        messages.error(request, 'Credentials are missing or expired. Please re-authenticate.')
        # messages.error(request, str(e))
        request.session['credentials'] = None
        return redirect('uprofile:home')
    

@login_required(login_url='uprofile:login')
def email_tab(request):
    credentials_info = request.session.get('credentials')
    print(credentials_info)
    if not credentials_info:
        authorize_url = flow.step1_get_authorize_url()
        return redirect(authorize_url)
    else:
        return redirect('uprofile:list_inbox_emails')
    

@login_required(login_url='uprofile:login')
def open_email(request, id):
    print(id)
    credentials_info = request.session.get('credentials')
    credentials_dict = json.loads(credentials_info)
    # print(credentials_dict)
    credentials = Credentials.from_authorized_user_info(credentials_dict, scopes=SCOPES)

    # Create a Gmail API service
    service = build('gmail', 'v1', credentials=credentials)
    message_data = service.users().messages().get(userId='me', id=id).execute()
    subject = None
    content = None
    date = None
    e_from = None

    payload = message_data['payload']
    headers = payload['headers']

    for header in message_data['payload']['headers']:
        if header['name'] == 'Subject':
            subject = header['value']
        if header['name'] == 'Content-Type':
            if 'text/plain' in header['value']:
                payload = message_data['payload']
                content = payload['body']['data']
                content = base64.urlsafe_b64decode(content).decode('utf-8')

    if 'parts' in payload.keys() and content == None:
        for part in payload['parts']:
            if 'text/plain' in part['mimeType']:
                # If the part contains plain text content
                try:
                    content = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                except Exception as e:
                    print(e)

    for header in headers:
        if header['name'] == 'Subject':
            subject = header['value']
        if header['name'] == 'Date':
            date = header['value'].split(' +')[0]
        if header['name'] == 'From':
            e_from = header['value']

    print(payload)
    email_data = {
        'subject': subject,
        'content': content ,
        'date': date,
        'id': id,
        'from': e_from
    }
    return render(request, 'userprofile/open_email.html', {'email_data': email_data})


def create_reply_message(service, original_message, subject, to, message_body):
    reply_message = {
        'raw': base64.urlsafe_b64encode(
            f"Subject: {subject}\nTo: {to}\nIn-Reply-To: {original_message['id']}\nReferences: {original_message['threadId']}\n\n{message_body}"
            .encode("utf-8")
        ).decode("utf-8")
    }
    return service.users().messages().send(userId='me', body=reply_message).execute()

# SEND_SCOPES = ['https://www.googleapis.com/auth/gmail.send']
@login_required(login_url='uprofile:login')
def reply_to_email(request, id):
    if request.method == 'POST':
        body = request.POST.get('body')
        print(body)
        credentials_info = request.session.get('credentials')
        credentials_dict = json.loads(credentials_info)
        credentials = Credentials.from_authorized_user_info(credentials_dict, scopes=SCOPES)

        # Create a Gmail API service
        service = build('gmail', 'v1', credentials=credentials)
        # Retrieve the original email you want to reply to
        original_message_id = id
        original_message = service.users().messages().get(userId='me', id=original_message_id).execute()

        print(original_message['payload']['headers'])

        # Compose and send the reply
        subject = None
        e_from = None
        for i in original_message['payload']['headers']:
            # print(i['name'])
            if i['name'] == 'Subject':
                subject = i['value']
            if i['name'] == 'From':
                e_from = i['value']
        subject = 'Re: ' + subject
        to = e_from
        message_body = body

        response = create_reply_message(service, original_message, subject, to, message_body)

        # Handle response or error as needed
        if response:
            messages.success(request, 'Sent!')
            return redirect('uprofile:emailtab')
        else:
            messages.success(request, 'Error!')
            return redirect('uprofile:emailtab')