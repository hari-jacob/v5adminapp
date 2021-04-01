import os
import io
from flask import Flask, render_template, url_for, request, redirect
import pymysql
from google.cloud import storage
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import date
import xlrd

db_user = "baarath"
db_password = "baarath"
db_name = "certdets"
db_connection_name = "tasko-task:asia-south1:mydbinsta"
host='35.244.62.185'

app = Flask(__name__)


@app.route('/')
def main():
    return render_template('adminlogin.html')

@app.route('/home')
def home():
    return render_template('adminpage.html')

@app.route('/addbamboozles')
def addbamboozles():
    return render_template('addbamboozles.html')


@app.route('/adminlogin', methods = ["POST","GET"])
def login():
    global email
    email =  request.form.get("email")
    password =  request.form.get("password")
    if email.find("admin") != -1:
        pwd=login_table(email)
        if pwd==password:
            return render_template('adminpage.html')
        else:
            return render_template('adminlogin.html')
    else:
        return render_template('adminlogin.html')

def login_table(email):
    sqlcheck="select password from personal where email = %s;"
    val=(email)
    cnx = pymysql.connect(user=db_user, password=db_password, host=host, db=db_name)
    try:
        with cnx.cursor() as cursor:
            cursor.execute(sqlcheck,val)
            pwd =cursor.fetchone() 
            cnx.commit()
        cursor.close()
    except:
        pwd="fail"
    return pwd[0]

@app.route('/filesupload', methods = ["POST","GET"])
def filesupload():
    if request.method == "POST":
      file = request.files["file"]
      csp = request.form["csp"]
      filetype = request.form["filetype"]
      qcfname = request.form["qcfname"]
      
      if filetype == "Quiz":
          path = '/usr/src/app/quiz/'
          file.save(os.path.join(path, file.filename))   
          database = pymysql.connect(user=db_user, password=db_password, host=host, db=db_name)
          cursor = database.cursor()
          # Open the workbook and define the worksheet
          bookpath=path + file.filename
          book = xlrd.open_workbook(bookpath)
          sheet = book.sheet_by_name("source")
          # Create the INSERT INTO sql query
          query = "INSERT INTO {}quiz (quizname,question,option1,option2,option3,option4,correct) VALUES (%s, %s, %s, %s, %s, %s, %s)".format(csp)
          # Create a For loop to iterate through each row in the XLS file, starting at row 2 to skip the headers
          for r in range(1, sheet.nrows):
              question= sheet.cell(r,0).value
              option1= sheet.cell(r,1).value
              option2= sheet.cell(r,2).value
              option3= sheet.cell(r,3).value
              option4= sheet.cell(r,4).value
              correct= sheet.cell(r,5).value
              values = (qcfname,question, option1, option2, option3, option4, correct)
              # Execute sql Query
              cursor.execute(query, values)
              database.commit()
          # Close the cursor
          cursor.close()
          database.close()
          return render_template("adminpage.html")
      elif filetype == "Flash Cards":
          path = '/usr/src/app/cards/'
          file.save(os.path.join(path, file.filename))   
          database = pymysql.connect(user=db_user, password=db_password, host=host, db=db_name)
          cursor = database.cursor()
          # Open the workbook and define the worksheet
          bookpath=path+file.filename
          book = xlrd.open_workbook(bookpath)
          sheet = book.sheet_by_name("source")
          # Create the INSERT INTO sql query
          query = "INSERT INTO {}cards (question, answer) VALUES (%s, %s)".format(csp)
          # Create a For loop to iterate through each row in the XLS file, starting at row 2 to skip the headers
          # Close the cursor
          for r in range(1, sheet.nrows):
              question= sheet.cell(r,0).value
              answer= sheet.cell(r,1).value
              values = (question, answer)
              # Execute sql Query
              cursor.execute(query, values)
              database.commit()
          cursor.close()
          database.close()
          return render_template("adminpage.html")
      else: 
          #filetype == "Course Content"
          path = '/usr/src/app/pdfs/'
          file.save(os.path.join(path, file.filename))
          database = pymysql.connect(user=db_user, password=db_password, host=host, db=db_name)
          cursor = database.cursor()
          query = "INSERT INTO content (csp, contentname, filelink) VALUES (%s, %s,%s)"
          values = (csp, qcfname, file.filename)
          cursor.execute(query, values)
          database.commit()
          cursor.close()
          database.close()

          destination_blob_name="content/"+file.filename
          bucket_name = "certdetsimage"
          source_file_name= path + file.filename
          storage_client = storage.Client()
          bucket = storage_client.bucket(bucket_name)
          blob = bucket.blob(destination_blob_name)
          blob.upload_from_filename(source_file_name)
          return render_template("adminpage.html")
    else:
        #for post method else
        pass
    return render_template("adminpage.html")


def send_mail(email,msgs):
    message = Mail(
        from_email='balaji.m.2016.cse@rajalakshmi.edu.in',
        to_emails=email,
        subject='....Baboozle Reminder....',
        html_content = msgs)
    try:
        sg = SendGridAPIClient('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')
        sg.send(message)
    except:
        pass

@app.route("/loadscoreboard",methods=["POST","GET"])
def loadscoreboard():
    cnxa = pymysql.connect(user=db_user, password=db_password, host=host, db=db_name)
    with cnxa.cursor() as cursor:
        try:
            sqlque = "SELECT distinct quizname from GCPquiz order by quizname;"
            cursor.execute(sqlque)
            gcpquiz = cursor.fetchall()
            cnxa.commit()
        except:
            gcpquiz=()
        try:
            sqlque = "SELECT distinct quizname from AWSquiz order by quizname;"
            cursor.execute(sqlque)
            awsquiz = cursor.fetchall()
            cnxa.commit()
        except:
            awsquiz=()
        try:
            sqlque = "SELECT distinct quizname from Azurequiz order by quizname;"
            cursor.execute(sqlque)
            azurequiz = cursor.fetchall()
            cnxa.commit()
        except:
            azurequiz=()
    cursor.close()
    return render_template('scoreboard.html',gcpquiz=gcpquiz,awsquiz=awsquiz,azurequiz=azurequiz)


@app.route("/remindmail",methods=["POST","GET"])
def remindmail():
    if request.method == 'POST':
        sendmails= request.form['sendmails']
        if sendmails !='':
            sendmails=sendmails[:-1]
            reminde = '<p>Reminder that You didnt complete a quiz.</p><br><strong><a href="http://34.70.143.201/">Go Ahead And Get Bamboozled</a></strong>'
            send_mail(sendmails,reminde)
        else:
            pass
    return render_template('adminpage.html')
    

@app.route("/ajaxscoreboard",methods=["POST","GET"])
def ajaxscoreboard():
    cnxa = pymysql.connect(user=db_user, password=db_password, host=host, db=db_name)
    with cnxa.cursor() as cursor:
        if request.method == 'POST':
            combined = request.form['query']
            x = combined.split('.') 
            ocsp = x[0]
            search_word = x[1]
            print(search_word)
            if search_word == '':
                pass
            else:    
                sqlque = "SELECT email,quizname,totalscore,attempt from {}score where quizname='{}' order by attempt desc;".format(ocsp,search_word)
                cursor.execute(sqlque)
                quizscoreboard = cursor.fetchall()
                cnxa.commit()
            try:
                nonpart = "select email from personal where email NOT IN (select distinct email from {}score where quizname='{}');".format(ocsp,search_word)
                cursor.execute(nonpart)
                nonparty = cursor.fetchall()
                cnxa.commit()
            except:
                nonparty=()
    cursor.close()
    return  render_template('scoreboardtable.html', quizscoreboard=quizscoreboard,nonparty=nonparty)

@app.route("/ajaxlivesearch",methods=["POST","GET"])
def ajaxlivesearch():
    cnxa = pymysql.connect(user=db_user, password=db_password, host=host, db=db_name)
    with cnxa.cursor() as cursor:
        if request.method == 'POST':
            search_word = request.form['query']
            # print(search_word)
            if search_word == '':
                sqlque = "SELECT csp,cid,email,cname,edate,validity from cert order by csp"
                cursor.execute(sqlque)
                numrows = int(cursor.rowcount)
                certtable = cursor.fetchall()
                cnxa.commit()
            else:    
                sqlque = "SELECT csp,cid,email,cname,edate,validity from cert WHERE cname LIKE '%{}%' OR email LIKE '%{}%' OR csp LIKE '%{}%' order by csp;".format(search_word,search_word,search_word)
                cursor.execute(sqlque)
                numrows = int(cursor.rowcount)
                certtable = cursor.fetchall()
                cnxa.commit()
    cursor.close()
    return  render_template('allcertificatecard.html', certtable=certtable)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
