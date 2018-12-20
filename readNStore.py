import pymysql
import serial

conn = pymysql.connect(
	host='127.0.0.1',
	port=3306,
	user='root',
	passwd='090078601',
	db='sensor')
SensorDB = conn.cursor()


def readAndStore():
	try:
		ser = serial.Serial('COM5', 9600)
		startingPoint = int(SensorDB.execute('Select idData from data'))
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
			print("Average1 = "+str(total1/30))
			print("Average2 = "+str(total2/30))
			SensorDB.execute("""INSERT INTO data (val1, val2) VALUES ("%d", "%d")""" % (total1/30, total2/30))
			count+=1

	except serial.serialutil.SerialException:
		conn.commit()
		stopReading(startingPoint, count)
		print("Done Reading")

def stopReading(startingPoint, count):
	endPoint = startingPoint + count
	insertS = "INSERT INTO readings (classRoom, startInstance, endInstance, people) VALUES ('"+room+"',"+str(startingPoint)+","+str(endPoint)+","+str(numberOfPeople)+")"
	print(room, startingPoint, endPoint, numberOfPeople)
	SensorDB.execute(insertS)
	conn.commit()
	SensorDB.close()
	conn.close()

startingPoint = endPoint = 0
room = input ("Enter Room: ")
numberOfPeople = int(input("Enter numberOfPeople: "))
readAndStore()

