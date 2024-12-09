from flask import Flask
from flask import render_template , redirect ,request,session
from flask_login import UserMixin , LoginManager ,login_user , logout_user , login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import PickleType

import os
from datetime import datetime
from werkzeug.security import generate_password_hash , check_password_hash
import pytz
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SECRET_KEY'] = os.urandom(24)
db=SQLAlchemy(app)

#単元list
subjiects_c1_math=['正負の数','文字式の計算','方程式','方程式の利用','比例','比例とグラフ','反比例','平面図形',]

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def loader_user(user_id):
    return User.query.get(int(user_id))

class Lesson(db.Model):
    id = db.Column(db.Integer , primary_key=True)
    subjiect = db.Column(db.String(50))
    title = db.Column(db.String(120))
    time = db.Column(db.String(20))
    max_number = db.Column(db.Integer)
    students_count=db.Column(db.Integer)
    member = db.Column(db.PickleType , default=list)
    teacher = db.Column(db.String(20))

class User(UserMixin , db.Model):
    id = db.Column(db.Integer , primary_key=True)
    username = db.Column(db.String(20) , unique=True ,nullable=False)
    passward = db.Column(db.String(12))
    role = db.Column(db.String(10))



with app.app_context():
    db.create_all()

@app.route("/signup",methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        passward = request.form.get('passward')
        role = request.form.get('role')
        user = User(username=username , passward = generate_password_hash(passward),role=role)

        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    else:
        return render_template('signup.html')    



@app.route("/login",methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        passward = request.form.get('passward')
        sign = request.form.get('signup')
        re = request.form.get('return')
        if sign:
            return redirect('/signup')
        if re:
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.passward , passward):
                session['username'] = username
                login_user(user)
                if user.role=='student':
                    return redirect('/student')
                else:
                    return redirect('/teacher')
            else:
                return render_template('a.html')
        else:
            return render_template('login.html')  
    else:
        return render_template('login.html')  


@app.route("/logout",methods=['GET','POST'])
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route("/")
def home():
    return redirect('/login')

@app.route('/student',methods=['POST','GET'])
@login_required
def student():
    username=session.get('username')
    if request.method == 'POST':
        action=request.form.get('action')
        if action=='search':
            lessons=Lesson.query.all()
            return render_template('student.html',lessons=lessons)
        elif action=='trend':
            return render_template('student_trend.html')
        elif action=='attend':
            return render_template('student_attend.html')
        elif action=='user_imformation':
            return render_template('student_user_imformation.html')
        db.session.commit()
        lesson_id = int(request.form.get('lesson_id'))
        lesson = Lesson.query.get(lesson_id)
        if (lesson.students_count < lesson.max_number) and (username not in lesson.member):
            lesson.students_count +=1
            lesson.member.append(username)
            print(lesson.member)
            db.session.commit()
            return redirect('/student')
        elif username in lesson.member:
            print('もう参加しています')
        else:
            print('満員です')

    else:
        lessons=Lesson.query.all()
        return render_template('student.html',lessons=lessons)

@app.route("/teacher",methods=['POST','GET'])
@login_required
def teacher():
    if request.method == 'POST':
        action=request.form.get('action')
        if action=='create':
            return render_template('teacher.html',subjiects_c1_math = subjiects_c1_math)
        elif action=='trend':
            return render_template('teacher_trend.html')
        elif action=='user_imformation':
            return render_template('teacher_user_imformation.html')
        lesson=request.form.get('lesson')
        print(f'received:{lesson}')
        for i in subjiects_c1_math:
            if lesson==i:
                return redirect(f'/create_lesson/{i}')
    else:
        return render_template('teacher.html',subjiects_c1_math = subjiects_c1_math)

@app.route("/create_lesson/<lesson>",methods=['POST','GET'])
@login_required
def craete_lesson(lesson):
    if request.method=='POST':
        time=request.form.get('time')
        people=request.form.get('people')
        title=request.form.get('title')
        username=session.get('username')
        lesson = Lesson(time=time , title=title ,max_number=people,students_count=0,subjiect=lesson,teacher=username,member=[])

        db.session.add(lesson)
        db.session.commit()
        return redirect('/teacher')

    else:    
        return render_template('create_lesson.html',lesson=lesson)
    