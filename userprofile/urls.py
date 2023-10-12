from django.urls import path
from django.contrib.auth import views as authentication_views

from userprofile import views
from userprofile.forms import CustomAuthentication

app_name = 'uprofile'

urlpatterns = [
    # path('admin/', admin.site.urls),
    # path('user/', include('userprofile.urls'))
    path('register/', views.register, name="register"),
    path('login/', authentication_views.LoginView.as_view(form_class=CustomAuthentication,template_name='userprofile/login.html'), name='login'),
    path('logout/', authentication_views.LogoutView.as_view(template_name='userprofile/logout.html'), name='logout'),
    path('home/', views.home, name = 'home'),
    path('userdetails/<int:empid>', views.user_details, name = 'usrdetails'),
    path('delete_profile/<int:empid>', views.delete_profile, name = 'deleteprofile'),
    path('export_profile/<int:empid>', views.export_profile, name = 'exportprofile'),
    path('export_all_profile/', views.export_all_profile, name = 'exportallprofile'),
    path('add_users/', views.add_users, name = 'addusers'),
    path('sample_csv/', views.sample_csv, name = 'samplecsv'),
]
