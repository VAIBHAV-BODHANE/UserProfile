from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Q
from django.http import Http404

from userprofile.forms import RegisterForm, UserDetailsForm
from userprofile.models import UserProfile, gender_choices, desi_choices

import csv, os, io
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


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


def authenticate_gmail_api(request):
    creds = None

    if 'token' in request.session:
        creds = Credentials.from_authorized_user_info(request.session['token'])

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_config(settings.GMAIL_API_CREDENTIALS, ['https://www.googleapis.com/auth/gmail.send'])
        creds = flow.run_local_server(port=0)

    request.session['token'] = creds.to_json()

    service = build('gmail', 'v1', credentials=creds)
    return service


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