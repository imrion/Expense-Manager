from django.urls import path
from . import views

urlpatterns = [
    path('',views.home,name='home'),
    path('login/',views.user_login,name='login'),
    path('logout/',views.user_logout,name='logout'),
    path('register/',views.user_register,name='register'),
    path('password_reset_request/',views.password_reset_request,name='password_reset_request'),
    path('password_reset_confirm/',views.password_reset_confirm,name='password_reset_confirm'),
    path('password_reset_done/',views.password_reset_done,name='password_reset_done'),
    path('password_reset_email/',views.password_reset_email,name='password_reset_email'),
    path('password_reset_complete/',views.password_reset_complete,name='password_reset_complete'),
    path('expense_list/',views.expense_list,name='expense_list'),
    path('expense_create/',views.expense_create,name='expense_create'),
    path('expense_update/',views.expense_update,name='expense_update'),
    path('expense_delete/',views.expense_delete,name='expense_delete'),
]
