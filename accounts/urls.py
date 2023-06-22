
from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.loginUser, name="login"),
    path("logout/", views.logoutUser, name="logout"),
    path("activate/<uidb64>/<token>/", views.activate, name="activate"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("", views.dashboard, name="dashboard"),
    path("forgotPassword/", views.forgotPassword, name="forgotPassword"),
    path("resetPassword/", views.resetPassword, name="resetPassword"),
    path("resetpassword_validate/<uidb64>/<token>/", views.resetpassword_validate, name="resetpassword_validate"),
] 
