#IMPORTS

from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename
import math

#END OF IMPORTS

with open("config.json" , "r") as conf:
    params = json.load(conf)["params"]

#SETTING UP SERVER AND MAIL SERVER
local_server = True
app = Flask(__name__)
app.secret_key="superkey"
app.config["UPLOAD_FILES"]=params["upload_location"]
app.config.update(
    MAIL_SERVER= 'smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail_user'],
    MAIL_PASSWORD=params['gmail_password']
)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
db = SQLAlchemy(app)

#END OF SERVER AND MAIL SERVER

mail = Mail(app)

#DB MODEL FOR CONTACTS AND POSTS (SQLITE3)

class Contacts(db.Model):
    sno = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(25),nullable=False)
    email = db.Column(db.String(35),nullable=False)
    phoneno = db.Column(db.String(15),nullable=False)
    msg = db.Column(db.String(100),nullable=False)
    date = db.Column(db.String(15),nullable=True)

class Posts(db.Model):
    sno = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(25),nullable=False)
    slug = db.Column(db.String(35),nullable=False)
    tagline = db.Column(db.String(35),nullable=False) #added here
    content = db.Column(db.String(100),nullable=False)
    date = db.Column(db.String(15),nullable=True)
    img_file = db.Column(db.String(15),nullable=True)

#END OF DB MODEL

#ROUTES
#INDEX ROUTE
@app.route('/')
def index():
    posts = Posts.query.filter_by().all()                               #FILTERING POST
    last = math.ceil(len(posts)/int(params["no_of_posts"]))             #COUNTING LAST PAGE
    page = request.args.get("page")                                     #REQUESTING PAGE
    if(not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params["no_of_posts"]):(page-1)*int(params["no_of_posts"])+int(params["no_of_posts"])]
    
    #NEXT AND PREV PAGE MECHANISM
    
    if (page == 1):
        prev = "#"
        nex = "/?page="+str(page+1)
    elif (page == last):
        prev = "/?page="+str(page-1)
        nex = "#"
    else:
        prev = "/?page="+str(page-1)
        nex = "/?page="+str(page+1)
    return render_template("index.html",params=params,posts=posts,prev=prev,nex=nex)

#DASHBORAD ROUTE
@app.route('/dashboard',methods=['GET','POST'])
def dashboard():
    if ("user" in session and session["user"]==params['u_name']): #CHECKING IF USER IN SESSION OR NOT
        posts = Posts.query.all()
        return render_template("dashboard.html",params=params,posts=posts)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('upassword')
        if(username==params['u_name'] and userpass==params['u_pass']):
            session['user'] = username
            posts = Posts.query.all()
            return render_template("dashboard.html",params=params,posts=posts)
        else:
            return render_template("signin.html",params=params)
    else:
        return render_template("signin.html")

#EDIT AND ADDING POSTS ROUTE
@app.route('/edit/<string:sno>',methods=['GET','POST'])
def editpost(sno):
    if ("user" not in session):
        return render_template("erroredit.html")
    if ("user" in session and session["user"]==params['u_name']):
        if request.method == 'POST':                                                   #IF USER IN SESSION DO ALL IN CONDITON
            etitle = request.form.get('title')
            econtent = request.form.get('content')
            etagline = request.form.get('tagline')
            eslug = request.form.get('slug')
            eimagefile = request.form.get('img_file')
            date = datetime.now()
            if sno == "0":                                                            #IF SERIAL NO IS EQUAL TO 0 EDIT THE POST
                post = Posts(title=etitle,content=econtent,tagline=etagline,slug=eslug,img_file=eimagefile,date=date)
                db.session.add(post)
                db.session.commit()
            else:                                                                     #ELSE ADD THE POST
                post = Posts.query.filter_by(sno=sno).first()
                post.title = etitle
                post.content = econtent
                post.tagline = etagline
                post.slug = eslug
                post.img_file = eimagefile
                post.date = date
                db.session.commit()
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html',params=params,post=post,sno=sno)


#ABOUT ROUTE
@app.route('/about')
def about():
   return render_template("about.html",params=params)

#LOGOUT ROUTE
@app.route('/logout',methods=['GET','POST'])
def logout():
    if("user" not in session):
        return render_template("errorlogout.html")
    session.pop("user")                                                     #POPING USER FROM SESSION
    return redirect("/dashboard")

#DELETE ROUTE
@app.route('/delete/<string:sno>',methods=['GET','POST'])
def delete(sno):
    if("user" in session and session["user"]==params["u_name"]):
        post = Posts.query.filter_by(sno=sno).first()                       #FILTERING POST THAN TAKING ITS FIRST INSTANCE AND REMOVING IT FROM DB THAN AGAIN FETCHING
        db.session.delete(post)
        db.session.commit()
        return redirect('/dashboard')

#SLUG ROUTE
@app.route('/post/<string:post_slug>',methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template("post.html",params=params,post=post)

#IMAGE UPLOADER ROUTE
@app.route('/uploader',methods=['GET','POST'])
def uploader():
    if ("user" in session and session["user"]==params['u_name']):
        if request.method == 'POST':
            f= request.files["filename"]
            f.save(os.path.join(app.config["UPLOAD_FILES"],secure_filename(f.filename)))
            return redirect("/dashboard")

#CONTACT ROUTE
@app.route('/contact',methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        #add entry to db
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("msg")
        phn = request.form.get("phone")

        entry = Contacts(name=name,email=email,phoneno=phn,msg=message,date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New Message From ' + name,sender=email,recipients=[params['gmail_user']],
        body= "Senders Message: " +message +"\n"+ "Senders Phone Number: "+ phn)                                       #USING MAIL IMPORT AND SENDING MAILS
    return render_template("contact.html",params=params)

if __name__ == "__main__":
    app.run(debug=True)