from flask import Flask, render_template, request, redirect, url_for, flash
import pymysql
import serial

app = Flask(__name__)
isLogIn = False

## ============  SQL FUNCTIONS ==================
def serverSetup ():
	global conn, SensorDB
	conn = pymysql.connect(
    host='127.0.0.1',
    port=3306,
    user='root',
    passwd='090078601',
    db='sensor')
	SensorDB = conn.cursor()

def readAndStore(ser, room, numberOfPeople):
	try:
		SensorDB.execute('Select max(idData) from data')
		startingPoint = SensorDB.fetchall()[0][0]
		while keepReading():
			total = 0
			for n in range(30):
				j = int(str(ser.readline())[2:4])
				total += j
			SensorDB.execute('INSERT INTO data (value) VALUES ('+str(total/30)+')')
		conn.commit()
	except serial.serialutil.SerialException:
		if startingPoint != 0:
			stopReading(startingPoint, room, numberOfPeople)
		else:
			pass

def stopReading(startingPoint, room, numberOfPeople):
	SensorDB.execute('Select max(idData) from data')
	endingPoint = SensorDB.fetchall()[0][0]
	add = str(startingPoint) + ',' + room + ',' + str(endingPoint) + ',' + str(numberOfPeople)
	SensorDB.execute('INSERT INTO readings (classRoom, startInstance, endInstance, people) VALUES ('+add+')')	


## ========================  WEBSITE ==========================

@app.route('/')
def Index():
    return render_template('homepage.html', title = 'Home - AQM')

@app.route('/class')
def classRoom():
	render_template('classroom.html', title = "Classrooms - AQM")

@app.route('/indicator')
def indicator():
	render_template('indicator.html', title = "Indicators - AQM")

@app.route('/live')
def live():
	render_template('live.html', title = "Live Data - AQM")

@app.route('/about')
def about():
	render_template('about.html', title = "About AQM")

@app.route('/login')
def loginPage():
	global isLogIn
	if isLogIn:
		return redirect ('/admin')
	else:
		return render_template('login.html', title = 'Admin Login - AQM', flashyMsg = '')		


## ============== ADMIN Pages ===============
@app.route('/login', methods=['POST'])
def loginAfter():
	global isLogIn
	name = request.form["name"].lower()
	password = request.form['pword']

	SensorDB.execute('Select * from admins')
	users = SensorDB.fetchall()

	if (name,password) in users:
		isLogIn = True
		return redirect('/admin')
	else:
		return render_template('login.html', title = 'Admin Login - AQM', flashyMsg = 'Incorrect Username or Password')

@app.route('/admin')
def adminPanel():
	if isLogIn:
		return render_template('adminPanel.html', title = 'Admin Panel - AQM', flashyMsg = '')
	else:
		return render_template('adminPanel.html', title = 'Admin Panel - AQM', flashyMsg = '') ############################################

@app.route('/readData')
def readData():
	if isLogIn:
		return render_template('readData.html', title = 'Data Reading - AQM', flashyMsg = '')
	else:
		return redirect('/login')

@app.route('/readData', methods = ['POST'])
def readDataAfter():
	room = request.form('classRoom')
	numberOfPeople = request.form('people')

	SensorDB.execute('Select classRoom from classroom')
	crooms = SensorDB.fetchall()
	if (room,) in crooms:
		try:
			ser = serial.Serial('COM5', 9600)
		except:
			return render_template('readData.html', title = 'Data Reading - AQM', flashyMsg = "Sensor Not Connected")

		return render_template('readData.html', title = 'Data Reading - AQM', flashyMsg = "Data Reading Has started", reading = True)
		readAndStore(ser, room, numberOfPeople)
	else:
		return render_template('readData.html', title = 'Data Reading - AQM', flashyMsg = "This classroom doesn't exist")

@app.route('/addCR',)
def addCR():
	if isLogIn:
		return render_template('addCR.html', title = 'Add Classrooms - AQM', flashyMsg = '')
	else:
		return redirect('/login')

@app.route('/addCR', methods = ['POST'])
def addCRAfter():
	room = request.form('classRoom')
	openings = request.form('openings')
	floorplan = request.form('floorplan')

	SensorDB.execute('Select classRoom from classroom')
	crooms = SensorDB.fetchall()
	if (room,) in crooms:
		return render_template('addCR.html', title = 'Add Classrooms - AQM', flashyMsg = 'ClassRoom already exist')
	else:
		add = room  + ',' + str(openings) + ',' + str(floorplan)
		SensorDB.execute('INSERT INTO classroom (classRoom, openings, floorplan) VALUES ('+add+')')
		return render_template('addCR.html', title = 'Add Classrooms - AQM', flashyMsg = 'ClassRoom added')

@app.route('/addAdmin',)
def addAdmin():
	if isLogIn:
		print(isLogIn)
		return render_template('addAdmin.html', title = 'Add New Admin - AQM', flashyMsg = '')
	else:
		return redirect('/login')

@app.route('/addAdmin', methods = ['POST'])
def addAdminAfter():
	name = request.form('name')
	pword = request.form('pword')

	SensorDB.execute('Select adminName from admins')
	users = SensorDB.fetchall()
	if (name,) in users:
		return render_template('addAdmin.html', title = 'Add New Admin - AQM', flashyMsg = 'Username already taken')
	else:
		add = name + ',' + str(pword)
		SensorDB.execute('INSERT INTO admins (adminName, pword) VALUES ('+add+')')
		return render_template('addCR.html', title = 'Add New Admin - AQM', flashyMsg = 'Admin added')

@app.route('/Logout',)
def Logout():
	if isLogIn:
		isLogIn = False
	return redirect('/login')

## =============== MAIN ==============
serverSetup()
if __name__ == "__main__":
    app.run(debug=True)

conn.close()
SensorDB.close()