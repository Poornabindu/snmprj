from flask import Flask, request, render_template, redirect, url_for,flash,session,send_file
from flask_session import Session
from otp import shinchan
from stoken import entoken,dntoken
from cmail import send_mail
import mysql.connector
from io import BytesIO
import re
import flask_excel as excel
from mimetypes import guess_type
from mysql.connector import (connection)

# mydb=connection.MySQLConnection(user='root',password='admin',host='localhost',db='snmprjdb')/
mydb=mysql.connector.connect(user='root',password='admin',host='localhost',db='snmprjdb')

app = Flask(__name__)
app.config['SESSION_TYPE']='filesystem' # data stored in file format
Session(app)
excel.init_excel(app)
app.secret_key='codegnan@18'

@app.route('/')
def home():
    return render_template('welcome.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        print(request.form)
        email=request.form['email']
        username=request.form['username']
        password=request.form['password']
        gender=request.form['gender']
        cursor=mydb.cursor()
        cursor.execute('select count(*) from users where useremail=%s',[email])
        count_email=cursor.fetchone() #fetchone---(1,) fetchall---[(0,)]


        if count_email[0]==0:
            gotp= genotp() #function call
            userdata={'username':username,'useremail':email,'userpassword':password,
                    'usergender':gender,'stored_otp':gotp}
            print(gotp)
            subject='OTP verification for Simple Notes Management App'
            body=f'Use the given otp for otp verify : {gotp}'
            send_mail(to=email,subject=subject,body=body)
            flash(f'Otp has been send to given email {email}')
            return redirect(url_for('otpverify',udata=entoken(userdata)))
        elif count_email[0]==1:
            flash(f'{email} already existed')

    
    return render_template('register.html')

@app.route('/otpverify/<udata>',methods=['GET','POST'])
def otpverify(udata):
    if request.method=='POST':
        user_otp=request.form['OTP']

        try:
            decrypted_userdata=dntoken(udata)
            #returns userdata={'username':username,'useremail':email,'userpassword':password,'usergender':gender,'stored_otp':gotp}

        except Exception as e:
            print(f'Error is {e}')
            flash('Can not Store your Details please reload te page')
            return redirect(url_for('register'))
        
        else:
            if decrypted_userdata['stored_otp'] == user_otp:
                cursor=mydb.cursor() #mysql cursor --mysql commands
                cursor.execute('insert into users(username,useremail,password,gender) values(%s,%s,%s,%s)',
                               [decrypted_userdata['username'],
                                decrypted_userdata['useremail'],
                                decrypted_userdata['userpassword'],
                                decrypted_userdata['usergender']])
                mydb.commit()
                cursor.close()
                flash('Details registered Successfully')
                return redirect(url_for('login'))
                
            else:
                flash('OTP was Wrong')
                return redirect(url_for('register'))
           
    return render_template('otp.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if not session.get('user'):
        if request.method=='POST':
            uemail=request.form['useremail']
            password=request.form['userpassword']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(useremail) from users where useremail=%s',[uemail])
            count_useremail=cursor.fetchone()
            print(count_useremail)
            if count_useremail[0]==1:
                cursor.execute('select password from users where useremail=%s',[uemail])
                stored_password=cursor.fetchone()

                if stored_password[0]==password:
                    session['user']=uemail
                    return redirect(url_for('dashboard'))
                else:
                    flash('Please Enter Correct Password')
                    return redirect(url_for('login'))

            elif count_useremail[0]==0:
                flash('Email not found please register')
                return redirect(url_for('login'))

        return render_template('login.html')
    else:
        return redirect(url_for('dashboard'))

@app.route('/forgotpassword',methods=['GET','POST'])
def forgotpassword():
    if request.method=='POST':
        useremail=request.form['useremail']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(useremail) from users where useremail=%s',[useremail])
        count_useremail=cursor.fetchone()
        if count_useremail[0]==1:
            subject='Reset link for Password Update'
            body=f"click on the given link : {url_for('newpassword',data=entoken(useremail),_external=True)}"
            send_mail(to=useremail,subject=subject,body=body)
            flash(f'Reset link has been sent to  given email {useremail}')
            return redirect(url_for('forgotpassword'))
        elif count_useremail[0]==0:
            flash('Email not found Please Register')
            return redirect(url_for('login'))
    return render_template('forgot.html')

@app.route('/newpassword/<data>',methods=['GET','POST'])
def newpassword(data):
    if request.method=='POST':
        npassword=request.form['newpassword']
        cpassword=request.form['confirmationpassword']
        try:
            decrypt_email=dntoken(data)
        except Exception as e:
            print(e)
            flash('Could not fetch newpassword update link')
            return redirect(url_for('forgotpassword'))
        else:
            if npassword==cpassword:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update users set password=%s where useremail=%s',[npassword,decrypt_email])
                mydb.commit()
                cursor.close()
                flash('Password updated Successfully')
                return redirect(url_for('login'))
            else:
                flash('password mismatch')

    return render_template('newpassword.html')

@app.route('/dashboard')
def dashboard():
    if session.get('user'):
        print(session)
        return render_template('dashboard.html')
    else:
        flash(f'Please login first')
        return redirect(url_for('login'))
    
@app.route('/addnotes',methods=['GET','POST'])
def addnotes():
    if session.get('user'):
        if request.method=='POST':
            title=request.form['title']
            description=request.form['description']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into notes(title,description,added_by) values(%s,%s,%s)',[title,description,session.get('user')])
            mydb.commit()
            cursor.close()
            flash(f'{title} notes added successfully')
            return redirect(url_for('viewallnotes'))
        return render_template('addnotes.html')
    else:
        flash('Please Login First')
        return redirect(url_for('login'))
    

@app.route('/viewallnotes')
def viewallnotes():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from notes where added_by=%s',[session.get('user')])
        notes_data=cursor.fetchall()
        print(notes_data)
        return render_template('viewallnotes.html',notes_data=notes_data)
    else:
        flash('Please Login First')
        return redirect(url_for('login'))

        
@app.route('/viewnotes/<nid>')
def viewnotes(nid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from notes where nid=%s and added_by=%s',
                    [nid,session.get('user')])
        notesdata=cursor.fetchone()  # (1,'python','ads','2025-09-25','alekhya@gmail.com)
        return render_template('viewnotes.html',notesdata=notesdata)  
    else:
        flash('Please Login First')
        return redirect(url_for('login'))    

@app.route('/deletenotes/<nid>')
def deletenotes(nid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete from notes where nid=%s and added_by=%s',
                    [nid,session.get('user')])
        mydb.commit()
        flash('Notes daleted Successfully')
        return redirect(url_for('viewallnotes'))
    else:
        flash('Please Login First')
        return redirect(url_for('login'))
    
@app.route('/updatenotes/<nid>',methods=['GET','POST'])
def updatenotes(nid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select *from notes where nid=%s and added_by=%s',[nid,session.get('user')])
        notesdata=cursor.fetchone()
        if request.method=='POST':
            title=request.form['title']
            description=request.form['description']
            cursor.execute('update notes set title=%s,description=%s where nid=%s and added_by=%s',[title,description,nid,session.get('user')])
            mydb.commit()
            cursor.close()
            flash(f'notes updated successfylly{title}')
            return redirect(url_for('viewallnotes'))
        
        return render_template('updatenotes.html',notesdata=notesdata)
    else:
        flash('plz login first')
        return redirect(url_for('login'))
@app.route('/fileupload',methods=['GET','POST'])
def fileupload():
    if session.get('user'):
        if request.method=='POST':
            filedata=request.files['file']
            fname=filedata.filename
            fdata=filedata.read()
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into filedata(file_name,file_data,added_by)values(%s,%s,%s)',[fname,fdata,session.get('user')])
            mydb.commit()
            cursor.close()
            flash(f'{fname} Successfully stored')
        return render_template('fileupload.html')
    else:
        flash('plz login first')
        return  redirecct(url_for('login'))

@app.route('/viewallfiles')
def viewallfiles():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from filedata where added_by=%s',[session.get('user')])
        files_data=cursor.fetchall()
        # print(notes_data)
        return render_template('viewallfiles.html',files_data=files_data)
    else:
        flash('Please Login First')
        return redirect(url_for('login'))

@app.route('/view_file/<fid>')
def view_file(fid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select fid,file_name,file_data from filedata where fid=%s and added_by=%s',[fid,session.get('user')])
        fdata=cursor.fetchone()
        data=BytesIO(fdata[2])
        mime_type, _=guess_type(fdata[1])
        print(mime_type)
        return send_file(data,download_name=fdata[1],mimetype=mime_type or 'application/octat-stream' ,as_attachment=False)
    else:
        flash('plz login first')
        return redirect(url_for('login'))

@app.route('/download_file/<fid>')
def download_file(fid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select fid,file_name,file_data from filedata where fid=%s and added_by=%s',[fid,session.get('user')])
        fdata=cursor.fetchone()
        data=BytesIO(fdata[2])
        mime_type, _=guess_type(fdata[1])
        print(mime_type)
        return send_file(data,download_name=fdata[1],mimetype=mime_type or 'application/octat-stream' ,as_attachment=True)
    else:
        flash('plz login first')
        return redirect(url_for('login'))


@app.route('/delete_file/<fid>')
def delete_file(fid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete from filedata where fid=%s and added_by=%s',
                    [fid,session.get('user')])
        mydb.commit()
        flash('File daleted Successfully')
        return redirect(url_for('viewallfiles'))
    else:
        flash('Please Login First')
        return redirect(url_for('login'))

@app.route('/search',methods=['GET','POST'])
def search():
    if session.get('user'):
        if request.method=='POST':
            sdata=request.form['searchdata']
            strg=['a-zA-Z0-9']
            pattern=re.compile(f'^{strg}',re.IGNORECASE)
            print(pattern)
            if pattern.match(sdata):
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select *from notes where nid like %s or title like %s or description like %s or create_at like %s',[sdata+'%',sdata+'%',sdata+'%',sdata+'%'])
                matcheddata=cursor.fetchall()
                if matcheddata:
                    return render_template('dashboard.html',matcheddata=matcheddata)
                else:
                    flash(f'{sdata} not found')
                    return redirect(url_for('dashboard'))
            else:
                flash('invalid search data')
                return redirect(url_for('dashboard'))
    else:
        flash('plz login first')
        return redirecct(url_for('login'))

@app.route('/getexceldata')
def getexceldata():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select *from notes where added_by=%s',[session.get('user')])
        stored_data=cursor.fetchall()
        if stored_data:
            array_data=[list(i) for i in stored_data]
            columns=['NOTES_ID','TITLE','DESCRIPTION','CREATED_AT']
            array_data.insert(0,columns)
            return excel.make_response_from_array(array_data,'xlsx',filename='notesdata')
        else:
            flash('No Data Found')
            return redirecct(url_for('dashboard'))
    else:
        flash('plz login first')
        return redirecct(url_for('login'))

@app.route('/userlogout')
def userlogout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('login'))
    else:
        flash('plz login to logout')
        return redirect(url_for('login'))



app.run(debug=True, use_reloader=True)