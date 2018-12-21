from flask import Flask, render_template, request, redirect, url_for, flash
import pymysql
import serial
import webbrowser

app = Flask(__name__)
isLogIn = False
live = []

## ====================  SQL FUNCTIONS ========================
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
		count = 0
		while True:
			total1 = 0
			total2 = 0
			for n in range(30):
				i, j = str(ser.readline())[2:-5].split(',')
				i = int(i)
				j = int(j)
				total1 += i
				total2 += j
				live.append([count*30 + n, i,j])

			SensorDB.execute("""INSERT INTO data (val1, val2) VALUES ("%d", "%d")""" % (total1/30, total2/30))
			count+=1
			conn.commit()
	except serial.serialutil.SerialException:
		if startingPoint != 0:
			stopReading(startingPoint, room, numberOfPeople)
		else:
			pass

def stopReading(startingPoint, room, numberOfPeople):
	SensorDB.execute('Select max(idData) from data')
	endingPoint = SensorDB.fetchall()[0][0]
	SensorDB.execute("""INSERT INTO readings (classRoom, startInstance, endInstance, people)
		VALUES  ("%s", "%d", "%d", "%d")"""
		% (room, int(startingPoint), int(endingPoint), int(numberOfPeople)))
	conn.commit()

## ========================  WEBSITE ==========================

@app.route('/')
def Index():
    return render_template('homepage.html', title = 'Home - AQM')

@app.route('/class')
def classRoom():
	SensorDB.execute("""SELECT AVG(val1), AVG(val2)
			FROM data, readings
			WHERE idData >= readings.startInstance
			AND idData < readings.endInstance""")
	data = SensorDB.fetchall()
	avg = data[0][0] + data[0][1]

	SensorDB.execute("""SELECT classroom, AVG(val1)+AVG(val2)
			FROM data, readings
			WHERE idData >= readings.startInstance
			AND idData < readings.endInstance
			GROUP BY classroom""")
	data = SensorDB.fetchall()

	colorDic = {}
	for i in data:
		if i[1] < avg - 20:
			colorDic[i[0]] = "red"
		elif i[1] > avg + 20:
			colorDic[i[0]] = "green"
		else:
			colorDic[i[0]] = "yellow"

	return render_template('class.html', title = "Classrooms - AQM", colorDic=colorDic)

@app.route('/class/<name>')
def classRoom2(name):

	SensorDB.execute("""SELECT val1, val2
			FROM data, readings
			WHERE idData >= readings.startInstance
			AND idData < readings.endInstance
			AND classroom = "%s";
			"""
			% (name))
	d = SensorDB.fetchall()
	n = 1
	data = []
	for i in d:
		data.append([n, i[0], i[1]])
		n += 1

	return render_template('classInd.html', title=name.upper(), data=data)

@app.route('/indicators')
def indicator():
	return render_template('indicators.html', title = "Indicators - AQM")

@app.route('/indicators/<name>')
def indicator2(name):

	if name == "ch4":
		SensorDB.execute("""SELECT val1, people
			FROM data, readings
			WHERE idData >= readings.startInstance
			and idData < readings.endInstance""")

		data = SensorDB.fetchall()
		title = "People to CH4"

	if name == "smoke":
		SensorDB.execute("""SELECT val2, people
			FROM data, readings
			WHERE idData >= readings.startInstance
			and idData < readings.endInstance""")

		data = SensorDB.fetchall()
		title = "People to Smoke"

	if name == "open":
		SensorDB.execute("""SELECT (val1+val2)/2, openings
			FROM data, readings, classroom
			WHERE idData >= readings.startInstance
			and idData < readings.endInstance
			and readings.classRoom = classroom.classRoom""")

		data = SensorDB.fetchall()
		title = "Air Quality to Room openings"

	return render_template('indicatorsChar.html', title=title, data=sorted(data))

@app.route('/live')
def liveData():
	return render_template('liveData.html', title = "This Session Data", data=live)

@app.route('/about')
def about():
	return render_template('about.html', title = "About AQM")

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
	global isLogIn
	if isLogIn:
		return render_template('adminPanel.html', title = 'Admin Panel - AQM', flashyMsg = '')
	else:
		return render_template('adminPanel.html', title = 'Admin Panel - AQM', flashyMsg = '') ############################################

@app.route('/readData')
def readData():
	global isLogIn
	if isLogIn:
		return render_template('readData.html', title = 'Data Reading - AQM', flashyMsg = '', Notreading = True)
	else:
		return redirect('/login')

@app.route('/readData', methods = ['POST'])
def readDataAfter():
	room = request.form['classRoom']
	numberOfPeople = request.form['people']

	SensorDB.execute('Select classRoom from classroom')
	crooms = SensorDB.fetchall()
	if (room,) in crooms:
		try:
			ser = serial.Serial('COM5', 9600)
		except:
			return render_template('readData.html', title = 'Data Reading - AQM', flashyMsg = "Sensor Not Connected", Notreading=True)
		
		readAndStore(ser, room, numberOfPeople)
		return redirect('/live')
	else:
		return render_template('readData.html', title = 'Data Reading - AQM', flashyMsg = "This classroom doesn't exist", Notreading=True)

@app.route('/addCR',)
def addCR():
	if isLogIn:
		return render_template('addCR.html', title = 'Add Classrooms - AQM', flashyMsg = '')
	else:
		return redirect('/login')

@app.route('/addCR', methods = ['POST'])
def addCRAfter():
	room = request.form['classRoom']
	openings = int(request.form['openings'])
	floorplan = int(request.form['floorplan'])

	SensorDB.execute('Select classRoom from classroom')
	crooms = SensorDB.fetchall()
	if (room,) in crooms:
		return render_template('addCR.html', title = 'Add Classrooms - AQM', flashyMsg = 'ClassRoom already exist')
	else:
		SensorDB.execute("""INSERT INTO classroom (classRoom, openings, floorplan) VALUES ("%s", "%d", "%d")"""
			% (room, openings, floorplan))
		conn.commit()
		return render_template('addCR.html', title = 'Add Classrooms - AQM', flashyMsg = 'ClassRoom added')

@app.route('/addAdmin',)
def addAdmin():
	if isLogIn:
		return render_template('addAdmin.html', title = 'Add New Admin - AQM', flashyMsg = '')
	else:
		return redirect('/login')

@app.route('/addAdmin', methods = ['POST'])
def addAdminAfter():
	name = request.form['name'].lower()
	pword = request.form['pword']

	SensorDB.execute('Select adminName from admins')
	users = SensorDB.fetchall()
	if (name,) in users:
		return render_template('addAdmin.html', title = 'Add New Admin - AQM', flashyMsg = 'Username already taken')
	else:
		SensorDB.execute("""INSERT INTO admins (adminName, pword) VALUES ("%s", "%s")"""
			% (name, str(pword)))
		conn.commit()
		return render_template('addAdmin.html', title = 'Add New Admin - AQM', flashyMsg = 'Admin added')

@app.route('/logout',)
def Logout():
	global isLogIn
	isLogIn = False
	return redirect('/login')

## =============== MAIN ==============
serverSetup()
if __name__ == "__main__":
    app.run(debug=True)

conn.close()
SensorDB.close()