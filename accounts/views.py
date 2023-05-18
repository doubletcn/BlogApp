from django.shortcuts import render
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm



# Create your views here.
class SignUpView(CreateView, UserCreationForm):
    template_name='registration/signup.html'
    form_class=UserCreationForm
    success_url= reverse_lazy("blog:post_list")
