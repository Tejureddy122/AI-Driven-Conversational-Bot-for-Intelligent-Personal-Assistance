from django.urls import path

from . import views

urlpatterns = [path("index.html", views.index, name="index"),
               path("AdminLogin.html", views.AdminLogin, name="AdminLogin"),	      
               path("AdminLoginAction", views.AdminLoginAction, name="AdminLoginAction"),
	       path("UserLogin.html", views.UserLogin, name="UserLogin"),	      
               path("UserLoginAction", views.UserLoginAction, name="UserLoginAction"),
               path("SignupAction", views.SignupAction, name="SignupAction"),
               path("Signup.html", views.Signup, name="Signup"),
               path("AddQuestion.html", views.AddQuestion, name="AddQuestion"),	      
               path("AddQuestionAction", views.AddQuestionAction, name="AddQuestionAction"),
	       path("ViewUser", views.ViewUser, name="ViewUser"),
	       path("Chatbot.html", views.Chatbot, name="Chatbot"),
	       path("record", views.record, name="record"),
]
