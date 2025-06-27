import os
import subprocess
import speech_recognition as sr
import pymysql
import numpy as np
import pandas as pd
from numpy import dot
from numpy.linalg import norm
from sklearn.feature_extraction.text import TfidfVectorizer
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.conf import settings


# Globals (use Django cache in production)
questions, answers, vectorizer, tfidf = [], [], None, None
recognizer = sr.Recognizer()

def ChatbotResponse(request):
    global questions, answers, vectorizer, tfidf

    if request.method == 'POST':
        user_input = request.POST.get('user_input').strip().lower()

        if not user_input:
            return render(request, 'Chatbot.html', {'response': "Please enter a question."})

        # TF-IDF response matching
        test_vec = vectorizer.transform([user_input]).toarray()[0]

        max_score, best_index = 0, -1
        for i, q_vec in enumerate(tfidf):
            score = dot(q_vec, test_vec) / (norm(q_vec) * norm(test_vec))
            if score > max_score:
                max_score = score
                best_index = i

        if best_index != -1 and max_score > 0.5:  # you can adjust threshold here
            response = answers[best_index]
        else:
            response = "Sorry, I don't understand that yet."

        return render(request, 'Chatbot.html', {'response': response})

    return render(request, 'Chatbot.html')

    

def train_model():
    global questions, answers, vectorizer, tfidf
    questions, answers = [], []
    
    con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='AIChatbot', charset='utf8')
    with con.cursor() as cur:
        cur.execute("SELECT * FROM faq")
        rows = cur.fetchall()
        for row in rows:
            q = row[1].strip().lower()
            a = row[2].strip()
            if q:
                questions.append(q)
                answers.append(a)

    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform(questions).toarray()


train_model()


def index(request):
    return render(request, 'index.html')


def Chatbot(request):
    return render(request, 'Chatbot.html')


@csrf_exempt
def record(request):
    if request.method == "POST":
        audio_data = request.FILES.get('data')
        fs = FileSystemStorage()
        record_path = os.path.join(settings.BASE_DIR, 'ChatbotApp/static/record.wav')
        record1_path = os.path.join(settings.BASE_DIR, 'ChatbotApp/static/record1.wav')

        for path in [record_path, record1_path]:
            if os.path.exists(path):
                os.remove(path)

        fs.save('ChatbotApp/static/record.wav', audio_data)

        ffmpeg_path = os.path.join('C:/ffmpeg/bin/ffmpeg.exe')  # Make dynamic or put in settings
        subprocess.run([
            ffmpeg_path, "-y", "-i", record_path, "-ar", "16000", "-ac", "1", record1_path
        ], check=True)

        try:
            with sr.AudioFile(record1_path) as source:
                audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
        except Exception:
            return HttpResponse("Chatbot: Unable to recognize", content_type="text/plain")

        query = text.strip().lower()
        test_vec = vectorizer.transform([query]).toarray()[0]

        max_score, best_index = 0, -1
        for i, q_vec in enumerate(tfidf):
            score = dot(q_vec, test_vec) / (norm(q_vec) * norm(test_vec))
            if score > max_score:
                max_score = score
                best_index = i

        if best_index != -1:
            response = f"Chatbot: {answers[best_index]}"
        else:
            response = "Chatbot: No matching answer found"

        return HttpResponse(response, content_type="text/plain")


def AddQuestion(request):
    return render(request, 'AddQuestion.html')


def Signup(request):
    return render(request, 'Signup.html')


def UserLogin(request):
    return render(request, 'UserLogin.html')


def AdminLogin(request):
    return render(request, 'AdminLogin.html')


def AdminLoginAction(request):
    if request.method == 'POST':
        user = request.POST.get('t1')
        password = request.POST.get('t2')
        if user == 'admin' and password == 'root':
            return render(request, 'AdminScreen.html', {'data': f'Welcome {user}'})
        return render(request, 'AdminLogin.html', {'data': 'Invalid Login'})


def UserLoginAction(request):
    if request.method == 'POST':
        username = request.POST.get('t1')
        password = request.POST.get('t2')
        with pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='AIChatbot') as con:
            with con.cursor() as cur:
                cur.execute("SELECT * FROM register WHERE username=%s AND password=%s", (username, password))
                result = cur.fetchone()
        if result:
            return render(request, 'UserScreen.html', {'data': f'Welcome {username}'})
        return render(request, 'UserLogin.html', {'data': 'Login failed'})


def SignupAction(request):
    if request.method == 'POST':
        username = request.POST.get('t1')
        password = request.POST.get('t2')
        contact = request.POST.get('t3')
        email = request.POST.get('t4')
        address = request.POST.get('t5')[:40]  # Limit to 40 characters
        con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='AIChatbot')
        with con.cursor() as cur:
            cur.execute("SELECT username FROM register WHERE username=%s", (username,))
            if cur.fetchone():
                return render(request, 'Signup.html', {'data': 'Username already exists'})
            cur.execute("INSERT INTO register(username,password,contact,email,address) VALUES(%s, %s, %s, %s, %s)",
                        (username, password, contact, email, address))
            con.commit()
        return render(request, 'Signup.html', {'data': 'Signup successful. You can login now.'})


def AddQuestionAction(request):
    if request.method == 'POST':
        question = request.POST.get('t1').strip().lower()
        answer = request.POST.get('t2').strip()
        con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='AIChatbot')
        with con.cursor() as cur:
            cur.execute("INSERT INTO faq(question, answer) VALUES(%s, %s)", (question, answer))
            con.commit()
        train_model()
        return render(request, 'AddQuestion.html', {'data': 'Question added successfully'})


def ViewUser(request):
    output = '<table border=1 align=center width=100%>'
    output += '<tr><th>Username</th><th>Password</th><th>Contact</th><th>Email</th><th>Address</th></tr>'
    con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root', database='AIChatbot')
    with con.cursor() as cur:
        cur.execute("SELECT * FROM register")
        for row in cur.fetchall():
            output += f'<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[4]}</td></tr>'
    output += '</table>'
    return render(request, 'AdminScreen.html', {'data': output})
