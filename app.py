# 1 . Imports
from flask import Flask,request,redirect,url_for,render_template,session
import sqlite3
import random
from flask_mail import Mail
from email.mime.multipart import MIMEMultipart
import smtplib, ssl
from email.mime.text import MIMEText

# 2. All Configurations
app=Flask(__name__)
app.config["DEBUG"] = True
app.config['SECRET_KEY'] = '1234'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
sender_email='aryanarorafreebookswdf@gmail.com'
sender_password='Freebooks123'
mail = Mail(app)


# 3. All Custom Functions
   
def sendemail( subject, recepient_email, message):
    email_message = MIMEMultipart("alternative")
    email_message["Subject"] = subject
    email_message["From"] = sender_email
    email_message["To"] = recepient_email

    part1 = MIMEText(message, "plain")
    email_message.attach(part1)
    
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, sender_password  )
        server.sendmail(
         sender_email, recepient_email, email_message.as_string()
        )


# 4. All Routes

# Adding Books
@app.route('/add_books', methods=['GET', 'POST'])
def add_books(): 
    #checking whether the person is logged in or not      
    if session.get('authenticated') == None or session.get('authenticated') == False :
        return redirect(url_for('login'))
    elif request.method=='POST': 
        bookname = request.form.get('bookname')
        book_detail = request.form.get('book_detail')
        book_image=request.files['coverpage']
        numbers=[0,1,2,3,4,5,6,7,8,9]
        random_number=''
        for ran_num in range(0,4):
            num=random.choice(numbers)
            random_number+=str(num)
        image_path='static/media/'+ random_number + book_image.filename
        # file handling
        f=open(image_path,'wb')
        f.write(book_image.read())
        f.close()
        conn = sqlite3.connect('database/freebooks.db')
        cur=conn.cursor()
        cur.execute('INSERT INTO total_books (bookname,book_detail,book_image,user_id) \
                     VALUES (?,?,?,?);',[bookname,book_detail,image_path,session.get('user_id')])
        conn.commit()
        conn.close()
        return redirect(url_for('all_books'))
    return render_template('add_books.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    message=''
    error_message=''
    if request.method == 'POST':
        first_name = request.form.get('fname')
        last_name = request.form.get('lname')
        email = request.form.get('email')
        contact = request.form.get('contact')
        pincode = request.form.get('pincode')
        city = request.form.get('city')
        state = request.form.get('state')
        password = request.form.get('password')
        confirm_password  = request.form.get('confirm_password')
        conn=sqlite3.connect('database/freebooks.db')
        cur = conn.cursor()
        registered_emails = cur.execute('SELECT email from users where email=?;',[email]).fetchall()
        if len(registered_emails)!=0:
            error_message = 'Email id already exists'
            return render_template('register.html',error_message=error_message)
        elif password == confirm_password:
            # Password Hashing to be done using passlib and sha256
            cur.execute(''' INSERT INTO users(
                fname,lname,email,contact,pincode,city,state,password)
                VALUES (?,?,?,?,?,?,?,?);'''
                ,(first_name,last_name,email,contact,pincode,city,state,password))
            conn.commit()
            conn.close()
            message = 'registration successful'
        else:
            message = 'unsuccessful registration'
    return render_template('register.html',message=message)   

@app.route('/login', methods=['GET', 'POST'])
def login():
    message=''
    error_message=''
    if request.method == 'POST':
        password=request.form.get('password')
        email = request.form.get('email')
        conn=sqlite3.connect('database/freebooks.db')
        cur=conn.cursor()
        records = cur.execute('SELECT password,id,fname FROM users WHERE email=?',[email]).fetchone()
        if records == None:
            error_message = 'No user found with this Email id try again'
        elif password == records[0]:
            session['email']=email
            session['authenticated'] =True
            session['user_id']=records[1]
            session['firstname']=records[2]
            message ='logged in successfully'
        else:
            message = 'Either email id or password is incorrect'
        conn.close()
    return render_template('login.html',message=message,error_message=error_message)

@app.route('/')
@app.route('/all_books', methods=['GET', 'POST'])
def all_books():
    conn=sqlite3.connect('database/freebooks.db')
    cur=conn.cursor()
    cur.execute('SELECT * FROM total_books')
    records=cur.fetchall()
    conn.close()
    return render_template ('all_books.html',records=records)

@app.route('/my_books', methods=['GET', 'POST'])
def my_books():
    conn=sqlite3.connect('database/freebooks.db')
    cur=conn.cursor()
    cur.execute('SELECT * FROM total_books WHERE user_id = ?;',[session.get('user_id','-1')])
    records=cur.fetchall()
    return render_template ('my_books.html',records=records)

@app.route('/request_for_rent/<book_id>')
def request_for_rent(book_id):
    conn=sqlite3.connect('database/freebooks.db')
    cur=conn.cursor()
    # 1 -available 2 -Rented 3 - Requested for rent 
    cur.execute('Update total_books set status="3", rent_user_id =? WHERE  id = ?;',[session.get('user_id'),book_id])
    conn.commit()
    userid=cur.execute('SELECT user_id,bookname from total_books where id=?;',[book_id]).fetchone()
    owner_userid=userid[0]
    bookname=userid[1]
    email_id=cur.execute('SELECT email from users where id=?;',[owner_userid]).fetchone()
    # Email Part
    owner_email_id=email_id[0]
    subject='Your Book has been requested for rent'
    email_mesage_to_owner=str(session.get('user_id'))+ 'has requested your book'\
                          +bookname+'for rent click the link below to approve' + \
                         '127.0.0.1:5000/pending_action'
    sendemail(subject, owner_email_id, email_mesage_to_owner)           
    #send email to the owner of the website with a link to approve 
    # if approved update the status to 2 
    # Once he returns the book again update the status to 1
    conn.close()
    return redirect(url_for('all_books'))

@app.route('/approve_for_rent/<book_id>')
def approve_for_rent(book_id):
    #add login condition
    if session.get('authenticated',False)==False:
        return redirect('/login')
    conn=sqlite3.connect('database/freebooks.db')
    cur=conn.cursor()
    # 1 -available 2 -Rented 3 - Requested for rent 
    cur.execute('Update total_books set status="2" WHERE id = ?;',[book_id])
    #get userid from book_id and get email id from users table
    userid=cur.execute('SELECT user_id,bookname from total_books where id=?;',[book_id]).fetchone()
    owner_userid=userid[0]
    bookname=userid[1]
    email_id=cur.execute('SELECT email from users where id=?;',[owner_userid]).fetchone()
    email_id=email_id[0]
    #send email to the owner about the request
    #todo 
    # store the name of the current logged in user in session
    email_mesage_to_owner= 'has requested your book ' +bookname+\
                            ' for rent click the link below to approve' + \
                            ' 127.0.0.1:5000/pending_action'
    email_message='Your request is pending for approval from the owner.'
    conn.commit()
    conn.close()
    return redirect(url_for('my_books'))

@app.route('/pending_action', methods=['GET', 'POST'])
def pending_action():
    conn=sqlite3.connect('database/freebooks.db')
    cur=conn.cursor()
    records=cur.execute('select * from total_books where user_id=? and status !=1;',[session.get('user_id')]).fetchall()
    '''In html check if status ==2 show unclickable button called rented, if status==3 show a button called approve for rent linking to approve/decline for rent action with book id'''
    conn.close()
    return render_template('pending_actions.html',records=records)


@app.route('/approve_request/<book_id>', methods=['GET', 'POST'])
def approve_request(book_id):
    conn=sqlite3.connect('database/freebooks.db')
    cur=conn.cursor()
    # 1 -available 2 -Rented 3 - Requested for rent 
    cur.execute('Update total_books set status="2" WHERE  id = ?;',[book_id])
    conn.commit()
    userid=cur.execute('SELECT rent_user_id,bookname from total_books where id=?;',[book_id]).fetchone()
    rent_userid=userid[0]
    bookname=userid[1]
    email_id=cur.execute('SELECT email from users where id=?;',[rent_userid]).fetchone()
    rent_person_email_id=email_id[0]
    owner_email_id=session.get('emailid',False)
    subject='Your request to rent a book has been approved'
    # send below email to both owner and rent person
    email_mesage_to_rent_person='request to rent the'+bookname + \
                            ' has been approved. contact details of book owner is ' \
                            +owner_email_id + 'and contact details of person requested for rent is'+\
                            rent_person_email_id + 'Please coordinate b/w yourself'
    sendemail(subject, rent_person_email_id, email_mesage_to_rent_person)
    sendemail(subject, rent_person_email_id, owner_email_id)
    conn.close()
    return redirect(url_for('pending_action'))



@app.route('/decline_request/<book_id>', methods=['GET', 'POST'])
def decline_request(book_id):
    conn=sqlite3.connect('database/freebooks.db')
    cur=conn.cursor()
    # 1 -available 2 -Rented 3 - Requested for rent 
    userid=cur.execute('SELECT rent_user_id,bookname from total_books where id=?;',[book_id]).fetchone()
    rent_userid=userid[0]
    bookname=userid[1]
    email_id=cur.execute('SELECT email from users where id=?;',[rent_userid]).fetchone()
    print(email_id)
    rent_person_email_id=email_id[0]
    subject='Your request to rent a book has been declined'
    # send below email to rent person
    email_mesage_to_rent_person='request to rent the' + bookname + \
        'has been declined. However you can request for other books by clicking here '\
        + '127.0.0.1:5000/all_books'
    sendemail(subject, rent_person_email_id, email_mesage_to_rent_person)
    cur.execute('Update total_books set status="1",rent_user_id=NULL WHERE  id = ?;',[book_id])
    conn.commit()
    conn.close()
    return redirect(url_for('all_books'))

@app.route('/my_rented_books', methods=['GET', 'POST'])
def my_rented_books():
    conn=sqlite3.connect('database/freebooks.db')
    cur=conn.cursor()
    cur.execute('SELECT * FROM total_books WHERE rent_user_id = ? and (status=2 or status=3);',[session.get('user_id','-1')])
    #todo if status ==2 show a button reurn book and link it to actio return rented book, if ststus ==3 show a unclickable button <waiting for approval>
    records=cur.fetchall()
    return render_template ('my_rented_books.html',records=records)

@app.route('/logout')
def logout():
    session.clear()
    return render_template('index.html')



if __name__ == '__main__':
    app.run(debug=True)