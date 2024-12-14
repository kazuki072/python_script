from flask import Flask
from flask import render_template , redirect ,request,session
from flask_login import UserMixin , LoginManager ,login_user , logout_user , login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import PickleType
from sqlalchemy.types import JSON
from sqlalchemy import inspect
from sqlalchemy.orm import relationship
from flask_migrate import Migrate
import os
from datetime import datetime
from werkzeug.security import generate_password_hash , check_password_hash
import pytz
import matplotlib.pyplot as plt
import io
import base64
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'blog.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)

db=SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def loader_user(user_id):
    return User.query.get(int(user_id))

#単元list
class Subjiect(db.Model):
    id =db.Column(db.Integer,primary_key=True)
    grade = db.Column(db.String(20),)
    subjiect = db.Column(db.String(20))
    topic = db.Column(db.String(50),nullable=False)
    vote = db.Column(db.Integer,default=0)





class Lesson(db.Model):
    id = db.Column(db.Integer , primary_key=True)
    subjiect = db.Column(db.String(50))
    title = db.Column(db.String(120))
    time = db.Column(db.String(20))
    max_number = db.Column(db.Integer)
    students_count=db.Column(db.Integer)
    member = db.Column(db.String(250))
    teacher = db.Column(db.String(20))

class User(UserMixin , db.Model):
    id = db.Column(db.Integer , primary_key=True)
    username = db.Column(db.String(20) , unique=True ,nullable=False)
    passward = db.Column(db.String(12))
    role = db.Column(db.String(10))




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


def Data():
    grade=request.form.get('grade')
    subjiect=request.form.get('subjiect')
    topic=request.form.get('topic')

    query=Subjiect.query
    if grade !='all':
        query = query.filter_by(grade=grade)
    if subjiect !='all':
        query = query.filter_by(subjiect=subjiect)
    if topic:
        query = query.filter(Subjiect.topic.like(f'%{topic}%'))

    results = query.all()

    data={}
    for item in results:
        if item.grade not in data:
            data[item.grade] = {}
        if item.subjiect not in data[item.grade]:
            data[item.grade][item.subjiect]=[]
        data[item.grade][item.subjiect].append({'topic':item.topic,'id':item.id})
    return data


#グラフ関連
def create_gragh(grade,subjiect):
    gragh_data=Subjiect.query
    if grade!='all':
        gragh_data = gragh_data.query.filter_by(grade=grade)
    if subjiect!='all':
        gragh_data = gragh_data.query.filter_by(subjiect=subjiect)
    label=[]
    value=[]
    for sub in gragh_data:
        label.append(sub.topic)
        value.append(sub.vote)
    print(label)
    print(value)
    if label:
        plt.pie(value, startangle=90, counterclock=False,  autopct='%.1f%%', pctdistance=0.8, labels=label)
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()
        img = base64.b64encode(buf.getvalue()).decode("utf-8")
        buf.close()
        return img
    else:
        img=0
        return img 

    





@app.route('/student',methods=['POST','GET'])
@login_required
def student():
    username=session.get('username')
    data=0
    if request.method == 'POST':
        action=request.form.get('action')
        lesson_id = request.form.get('lesson_id')
        lessons=Lesson.query.all()

        #探す関連
        if action=='search':
            return render_template('student.html',lessons=lessons,username=username)
        
        #トレンド関連
        elif action=='trend':            
            grade='all'
            subjiect='all'
            img = create_gragh(grade,subjiect)
            return render_template('student_trend.html',img=img)
        
        #参加している授業関連
        elif action=='attend':
            return render_template('student_attend.html',lessons=lessons)
        
        #ユーザー情報関連
        elif action=='user_imformation':
            return render_template('student_user_imformation.html')
        
        #vote関連
        elif action=='vote':
            data=0
            return render_template('student_vote.html',data=data)
        
        elif action=='look_for':
            data=Data()
            return render_template('student_vote.html',data=data)
        
        elif action=='vote_id':
            data=Data()
            vote_id = request.form.get('vote_id')
            subjiect= Subjiect.query.get(vote_id)
            subjiect.vote += 1
            db.session.commit()
            return render_template('student_vote.html',data=data)
        
        elif action=='lesson':
            lesson_id = request.form.get('lesson_id')
            lesson = Lesson.query.get(lesson_id)
            members = lesson.member.split(',') if lesson.member else []
            if (lesson.students_count < lesson.max_number) and (username not in members):
                lesson.students_count +=1
                members.append(username)
                lesson.member = ','.join(members)
                db.session.commit()
                return redirect('/student')

            elif username in members:
                return redirect('/student')
            else:
                print('満員です')
    else:
        lessons=Lesson.query.all()
        return render_template('student.html',lessons=lessons,username=username)

@app.route("/teacher",methods=['POST','GET'])
@login_required
def teacher():
    username=session.get('username')
    lessons = Lesson.query.all()
    data=0
    if request.method == 'POST':
        action=request.form.get('action')

        if action=='create':
            return render_template('teacher.html',data=data)
        
        elif action=='trend':
            return render_template('teacher_trend.html')
        
        elif action=='user_imformation':
            return render_template('teacher_user_imformation.html')
        
        elif action=='created':
            created=[]
            for i in lessons:
                if i.teacher == username:
                    created.append(i)
            return render_template('teacher_created.html',created=created)
        
        elif action=='lesson':
            lesson_id = request.form.get('lesson_id')
            lesson= Subjiect.query.get(lesson_id)
            return redirect(f'/create_lesson/{lesson.topic}')
        
        elif action=='search':
            data=Data()

            return render_template('teacher.html',data=data)
        else:
            
            return render_template('teacher.html',data=data)

    else:
        return render_template('teacher.html',data=data)



@app.route("/create_lesson/<lesson>",methods=['POST','GET'])
@login_required
def craete_lesson(lesson):
    if request.method=='POST':
        time=request.form.get('time')
        people=request.form.get('people')
        title=request.form.get('title')
        username=session.get('username')
        lesson = Lesson(time=time , title=title ,max_number=people,students_count=0,subjiect=lesson,teacher=username,member='')

        db.session.add(lesson)
        db.session.commit()
        return redirect('/teacher')

    else:    
        return render_template('create_lesson.html',lesson=lesson)
    

@app.route("/topics/add",methods=['POST','GET'])
def topics():
    if request.method=='POST':
        grade=request.form.get('grade')
        subjiect=request.form.get('subjiect')
        topic=request.form.get('topic').split(',') if request.form.get('topic') else []
        if topic:
            for i in topic:
                add=Subjiect(grade=grade,subjiect=subjiect,topic=i)
                db.session.add(add)
                db.session.commit()
        return render_template('topics_add.html')
    else:
        return render_template('topics_add.html')
