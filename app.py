import os
import uuid
import json
import redis
from flask import Flask, render_template, redirect, request, url_for, make_response
import boto

app = Flask(__name__)
my_uuid = str(uuid.uuid1())
BLUE = "#777799"
GREEN = "#99CC99"

COLOR = BLUE

if 'VCAP_SERVICES' in os.environ:
    VCAP_SERVICES = json.loads(os.environ['VCAP_SERVICES'])
    CREDENTIALS = VCAP_SERVICES["rediscloud"][0]["credentials"]
    r = redis.Redis(host=CREDENTIALS["hostname"], port=CREDENTIALS["port"], password=CREDENTIALS["password"])
else:
    r = redis.Redis(host='192.168.112.128', port='6379')

## r = redis.Redis(host='redis-11762.c14.us-east-1-2.ec2.cloud.redislabs.com', port='11762', password='FJkK7k6uRB9YXogd')

ecs_access_key_id = '131411953564759516@ecstestdrive.emc.com'  
ecs_secret_key = 'UVBcsylBl7QIj65LXv7xIX6llCkI9E+WnTC9X/6a'

session = boto.connect_s3(ecs_access_key_id, ecs_secret_key, host='object.ecstestdrive.com')  
## Get hold of your bucket
bname = 'pp-ph-photobook'
b = session.get_bucket(bname)
print "ECS connection is: " + str(session)
print "Bucket is: " + str(b)

print "Uploading photos ..."
## Create a list of filenames in "photos" to upload to ECS
for each_photo in os.listdir("photos"):
    print "Uploading " + str(each_photo)
    k = b.new_key(each_photo)
    src = os.path.join("photos", each_photo)
    k.set_contents_from_filename(src)
    k.set_acl('public-read')


## Alterntively walk recursively a dir tree. It creates a string and 2 lists
##
##for (dirpath, dirnames, filenames) in os.walk("photos"):

print "Upload complete!"
print "Starting the photoalbum"

@app.route('/')
def mainmenu():

    return """
    <html>
    <body bgcolor="{}">

    <center><h1><font color="white">Hi, I'm GUID:<br/>
    {}</br>
    
    <div class="container">
        <div class="jumbotron">
            <h2>Main Menu</h2>
        </div>
 
        <div class="row marketing">
            <div class="col-lg-6">
                <h5><a href="/agenda">View the Agenda</a></h5>
                <p></p>
 
                <h5><a href="/floorplan">View the Floorplan</a></h5>
                <p></p>
 
                <h5><a href="/feedback">Rate a Session</a></h5>
                <p></p>

                <h5><a href="/photoalbum">View the Photo Album</a></h5>
                <p></p>
            </div>
        </div>
        <footer class="footer">
            <p>&copy; Compuglobalhypermeganet 2017</p>
        </footer>
    </div>    
    </center>
    </body>
    </html>
    """.format(COLOR,my_uuid,)

@app.route('/feedback')
def feedback():

    resp = make_response(render_template('survey.html'))
    return resp

@app.route('/suthankyou.html', methods=['POST'])
def suthankyou():

    global r
    ## This is how you grab the contents from the form
    d = request.form['division']
    s = request.form['state']
    f = request.form['feedback']

    print "Division is " + d
    print "State is " + s
    print "Feedback: " + f

  
    ## Now you can now do someting with variable "f"
    
    Counter = r.incr('counter')
    newsurvey = 'new_survey' + str(Counter)

    r.hmset(newsurvey,{'division': d, 'state': s, 'feedback': f})

    print "the counter is now: ", Counter

    resp = """
        <body bgcolor="{}">
        <center>
        <div class="container">
        <div class="jumbotron">
            <h2> - Thanks for taking the survey! - </h2>
        </div>
 
        <div class="row marketing">
            <div class="col-lg-6">
                <h3><a href="/">Back to main menu</a></h3>
                <p></p>
            </div>
        </div>
        <footer class="footer">
            <p>&copy; Compuglobalhypermeganet 2017</p>
        </footer>
        </div>
        </center>
        </body>
    """.format(COLOR,)

    return resp

@app.route('/agenda')
def agenda():
    
    with open('sessions.txt') as f:
        f_lines = f.readlines()
        f.close()

    agenda_items = []
    agenda = len(f_lines)

    for x in range(agenda):
        agenda_items.append(f_lines[x].split(",",4))

    return render_template('agenda.html', agenda=agenda, agenda_items=agenda_items)

##    return """
##    <html>
##    <body bgcolor="{}">
##    <table>
##    <tr>
##        <th>Date</th>
##        <th>Event</th>
##    </tr>
##
##    {% for row in range(agenda) %}
##        <tr>
##            {% for column in range(3) %}
##            <td> {{ agenda_items[row][column] }} </td>
##            {% endfor %}
##        </tr>
##    {% endfor %}
##    </table>
##    </body>
##    </html>
##    """.format(COLOR,)

@app.route('/floorplan')
def floorplan():

    return """
    <html>
    <body bgcolor="{}">
    <center>
    
    <div class="container">
        <div class="jumbotron">
            <h1>View the Floorplan</h1>
        </div>
 
        <div class="row marketing">
            <div class="col-lg-6">
                <img src=".\\static\\floorplan.jpg">
                <p></p>
             </div>
        </div>
        <footer class="footer">
            <p><h4><a href="/">Home</a></h4>
            <p>&copy; Compuglobalhypermeganet 2017</p>
        </footer>
  
    </center>
    </body>
    </html>
    """.format(COLOR,)

@app.route('/dumpsurveys')
def dumpsurveys():

    global r
    response = "Dump of all reviews so far<br>"
    response += "-----------------------------<br>"
    print "Reading back from Redis"
    for eachsurvey in r.keys('new_survey*'):
        response += "Division : " + r.hget(eachsurvey,'division') + "<br>"
        response += "State : " + r.hget(eachsurvey,'state') + "<br>"
        response += "Feedback : " + r.hget(eachsurvey,'feedback') + "<br>"
        response += "-----------------------------<br>"

    return response

@app.route('/photoalbum')
def photoalbum():

    begin_page = """
    <html>
    <body bgcolor="{}">
    <center><h1>View the Photo Album</h1>""".format(COLOR,)

    mid_page = ""
    ## List all the keys in the bucket and grab the images with html code
    for photo in b.list():
        print(photo.key)
        mid_page += """<hr><h2>{}</h2>
        <img src="http://131411953564759516.public.ecstestdrive.com/pp-ph-photobook/{}" width=500><br>""".format(photo.key, photo.key)
    
    end_page = """
    <footer class="footer">
        <p><h4><a href="/">Home</a></h4>
        <p>&copy; Compuglobalhypermeganet 2017</p>
    </footer>
    </center>
    </body>
    </html>"""

    return begin_page + mid_page + end_page


if __name__ == "__main__":
	app.run(debug=False,host='0.0.0.0', port=int(os.getenv('PORT', '5000')))
