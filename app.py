# Import modules
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import RPi.GPIO as GPIO
import glob
import time
import Resources_rc
import _thread

# Set GPIO pins, modes and variables
GPIO.setmode(GPIO.BOARD)

TACH1 = 22      # BCM 25
TACH2 = 18      # BCM 24
R1 = 37         # BCM 26
R2 = 33         # BCM 13
fan1 = 12       # BCM 18
fan2 = 35       # BCM 19

R1_state = False
R2_state = False

GPIO.setwarnings(False)
GPIO.setup(TACH1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(TACH2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(R1, GPIO.OUT)
GPIO.setup(R2, GPIO.OUT)
GPIO.setup(fan1,GPIO.OUT)
GPIO.setup(fan2,GPIO.OUT)
GPIO.output(R1, R1_state)
GPIO.output(R2, R2_state)

pi_pwm1 = GPIO.PWM(fan1,20000)		#create PWM instance with frequency
pi_pwm2 = GPIO.PWM(fan2,20000)

t1 = time.time()
t2 = time.time()

temp_in = 0.0
temp_out = 0.0
temp_still = 0
cuts = 0
rpm1 = 0
rpm2 = 0
duty1 = 0
duty2 = 0

# Set link to temperature sensors
base_dir = '/sys/bus/w1/devices/'
sens1 = '28-3c01d607476c'
sens2 = '28-3c01d6070861'


# UI Class
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        # Set main windows
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowModality(QtCore.Qt.NonModal)
        MainWindow.resize(1024, 600)
        MainWindow.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        MainWindow.setWindowFlags(Qt.FramelessWindowHint)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # Link icons to resources
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Images/home.png"),
                       QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/Images/off.png"),
                        QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/Images/on.png"),
                        QtGui.QIcon.Normal, QtGui.QIcon.Off)

        # Create LCD for showing fan speed
        self.lcdfan1 = QtWidgets.QLCDNumber(self.centralwidget)
        self.lcdfan1.setGeometry(QtCore.QRect(349, 190, 101, 40))
        self.lcdfan1.setProperty("value", rpm1)
        self.lcdfan1.setObjectName("lcdfan1")
        self.lcdfan2 = QtWidgets.QLCDNumber(self.centralwidget)
        self.lcdfan2.setGeometry(QtCore.QRect(480, 190, 100, 40))
        self.lcdfan2.setProperty("value", rpm2)
        self.lcdfan2.setObjectName("lcdfan2")

        # Create sliders for fan control
        self.sldfan1 = QtWidgets.QSlider(self.centralwidget)
        self.sldfan1.setGeometry(QtCore.QRect(380, 240, 50, 160))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.sldfan1.setFont(font)
        self.sldfan1.setMinimum(1)
        self.sldfan1.setMaximum(100)
        self.sldfan1.setSingleStep(1)
        self.sldfan1.setOrientation(QtCore.Qt.Vertical)
        self.sldfan1.setObjectName("sldfan1")
        self.sldfan1.valueChanged.connect(self.changedutycycle)
        self.sldfan2 = QtWidgets.QSlider(self.centralwidget)
        self.sldfan2.setGeometry(QtCore.QRect(510, 240, 50, 160))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.sldfan2.setFont(font)
        self.sldfan2.setMinimum(1)
        self.sldfan2.setMaximum(100)
        self.sldfan2.setSingleStep(1)
        self.sldfan2.setOrientation(QtCore.Qt.Vertical)
        self.sldfan2.setObjectName("sldfan2")
        self.sldfan2.valueChanged.connect(self.changedutycycle)

        # Create labels to show which LCD and slider corresponds to which fan
        self.lblfan1 = QtWidgets.QLabel(self.centralwidget)
        self.lblfan1.setGeometry(QtCore.QRect(380, 170, 55, 16))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lblfan1.setFont(font)
        self.lblfan1.setAlignment(QtCore.Qt.AlignCenter)
        self.lblfan1.setObjectName("lblfan1")
        self.lblfan2 = QtWidgets.QLabel(self.centralwidget)
        self.lblfan2.setGeometry(QtCore.QRect(510, 170, 55, 16))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lblfan2.setFont(font)
        self.lblfan2.setAlignment(QtCore.Qt.AlignCenter)
        self.lblfan2.setObjectName("lblfan2")

        # Create LCD's to show temperature and cut amount
        self.lcdtemp1 = QtWidgets.QLCDNumber(self.centralwidget)
        self.lcdtemp1.setGeometry(QtCore.QRect(840, 190, 100, 40))
        self.lcdtemp1.setProperty("value", temp_in)
        self.lcdtemp1.setObjectName("lcdtemp1")
        self.lcdtemp2 = QtWidgets.QLCDNumber(self.centralwidget)
        self.lcdtemp2.setGeometry(QtCore.QRect(840, 240, 100, 40))
        self.lcdtemp2.setProperty("value", temp_out)
        self.lcdtemp2.setObjectName("lcdtemp2")
        self.lcdtemp3 = QtWidgets.QLCDNumber(self.centralwidget)
        self.lcdtemp3.setGeometry(QtCore.QRect(840, 290, 100, 40))
        self.lcdtemp3.setProperty("value", temp_still)
        self.lcdtemp3.setObjectName("lcdtemp3")
        self.lcdtemp3_2 = QtWidgets.QLCDNumber(self.centralwidget)
        self.lcdtemp3_2.setGeometry(QtCore.QRect(840, 340, 100, 40))
        self.lcdtemp3_2.setProperty("value", cuts)
        self.lcdtemp3_2.setObjectName("lcdtemp3_2")

        # Create close button
        self.btnClose = QtWidgets.QPushButton(self.centralwidget)
        self.btnClose.setGeometry(QtCore.QRect(10, 10, 50, 50))
        font = QtGui.QFont()
        font.setKerning(True)
        self.btnClose.setFont(font)
        self.btnClose.setAutoFillBackground(False)
        self.btnClose.setText("")
        self.btnClose.setIcon(icon)
        self.btnClose.setIconSize(QtCore.QSize(50, 50))
        self.btnClose.setFlat(True)
        self.btnClose.setObjectName("btnClose")
        self.btnClose.clicked.connect(self.closeEvent)

        # Create '°C' labels + labels to show which temperature corresponds to which sensor
        self.lblC = QtWidgets.QLabel(self.centralwidget)
        self.lblC.setGeometry(QtCore.QRect(940, 190, 40, 40))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.lblC.setFont(font)
        self.lblC.setAlignment(QtCore.Qt.AlignCenter)
        self.lblC.setObjectName("lblC")
        self.lblC_2 = QtWidgets.QLabel(self.centralwidget)
        self.lblC_2.setGeometry(QtCore.QRect(940, 240, 40, 40))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.lblC_2.setFont(font)
        self.lblC_2.setAlignment(QtCore.Qt.AlignCenter)
        self.lblC_2.setObjectName("lblC_2")
        self.lblC_3 = QtWidgets.QLabel(self.centralwidget)
        self.lblC_3.setGeometry(QtCore.QRect(940, 290, 40, 40))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.lblC_3.setFont(font)
        self.lblC_3.setAlignment(QtCore.Qt.AlignCenter)
        self.lblC_3.setObjectName("lblC_3")
        self.lblTemp = QtWidgets.QLabel(self.centralwidget)
        self.lblTemp.setGeometry(QtCore.QRect(730, 190, 100, 40))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lblTemp.setFont(font)
        self.lblTemp.setAlignment(
            QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.lblTemp.setObjectName("lblTemp")
        self.lblTemp_2 = QtWidgets.QLabel(self.centralwidget)
        self.lblTemp_2.setGeometry(QtCore.QRect(730, 240, 100, 40))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lblTemp_2.setFont(font)
        self.lblTemp_2.setAlignment(
            QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.lblTemp_2.setObjectName("lblTemp_2")
        self.lblTemp_3 = QtWidgets.QLabel(self.centralwidget)
        self.lblTemp_3.setGeometry(QtCore.QRect(730, 290, 100, 40))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lblTemp_3.setFont(font)
        self.lblTemp_3.setAlignment(
            QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.lblTemp_3.setObjectName("lblTemp_3")
        self.lblTemp_4 = QtWidgets.QLabel(self.centralwidget)
        self.lblTemp_4.setGeometry(QtCore.QRect(730, 340, 100, 40))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lblTemp_4.setFont(font)
        self.lblTemp_4.setAlignment(
            QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.lblTemp_4.setObjectName("lblTemp_4")

        # Create button and label to control the pump relais
        self.btnPump = QtWidgets.QPushButton(self.centralwidget)
        self.btnPump.setGeometry(QtCore.QRect(80, 200, 50, 50))
        font = QtGui.QFont()
        font.setKerning(True)
        self.btnPump.setFont(font)
        self.btnPump.setAutoFillBackground(False)
        self.btnPump.setText("")
        self.btnPump.setIcon(icon1)
        self.btnPump.setIconSize(QtCore.QSize(50, 50))
        self.btnPump.setFlat(True)
        self.btnPump.setObjectName("btnPump")
        self.btnPump.clicked.connect(self.changepump)
        self.lblPump = QtWidgets.QLabel(self.centralwidget)
        self.lblPump.setGeometry(QtCore.QRect(70, 160, 71, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lblPump.setFont(font)
        self.lblPump.setAlignment(QtCore.Qt.AlignCenter)
        self.lblPump.setObjectName("lblPump")

        # Create button and label to control the fan relais
        self.lblFans = QtWidgets.QLabel(self.centralwidget)
        self.lblFans.setGeometry(QtCore.QRect(70, 280, 71, 31))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lblFans.setFont(font)
        self.lblFans.setAlignment(QtCore.Qt.AlignCenter)
        self.lblFans.setObjectName("lblFans")
        self.btnFans = QtWidgets.QPushButton(self.centralwidget)
        self.btnFans.setGeometry(QtCore.QRect(80, 320, 50, 50))
        font = QtGui.QFont()
        font.setKerning(True)
        self.btnFans.setFont(font)
        self.btnFans.setAutoFillBackground(False)
        self.btnFans.setText("")
        self.btnFans.setIcon(icon1)
        self.btnFans.setIconSize(QtCore.QSize(50, 50))
        self.btnFans.setFlat(True)
        self.btnFans.setObjectName("btnFans")
        self.btnFans.clicked.connect(self.changefans)

        # Create button to make cuts
        self.btnCut = QtWidgets.QPushButton(self.centralwidget)
        self.btnCut.setGeometry(QtCore.QRect(42, 467, 941, 111))
        font = QtGui.QFont()
        font.setPointSize(24)
        font.setBold(False)
        font.setWeight(50)
        self.btnCut.setFont(font)
        self.btnCut.setObjectName("btnCut")

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        
        sensor_sens1 = round(((((read_temp(sens1) - 3.0) * 99.0) / 98.8) + 3.0), 1)
        sensor_sens2 = round(((((read_temp(sens2) - 3.0) * 99.0) / 98.0) + 3.0), 1)
        self.lcdtemp1.setProperty("value", sensor_sens1)
        self.lcdtemp2.setProperty("value", sensor_sens2)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.lblfan1.setText(_translate("MainWindow", "Fan 1"))
        self.lblfan2.setText(_translate("MainWindow", "Fan 2"))
        self.lblC.setText(_translate("MainWindow", "°C"))
        self.lblC_2.setText(_translate("MainWindow", "°C"))
        self.lblC_3.setText(_translate("MainWindow", "°C"))
        self.lblTemp.setText(_translate("MainWindow", "Temp IN"))
        self.lblTemp_2.setText(_translate("MainWindow", "Temp OUT"))
        self.lblTemp_3.setText(_translate("MainWindow", "Temp Still"))
        self.lblPump.setText(_translate("MainWindow", "Pump"))
        self.lblFans.setText(_translate("MainWindow", "Fans"))
        self.btnCut.setText(_translate("MainWindow", "CUT"))
        self.lblTemp_4.setText(_translate("MainWindow", "Cuts"))

    def closeEvent(self):
        GPIO.cleanup()
        sys.exit()

    def changefans(self):
        global R1_state
        global speed1
        global speed2
        if R1_state == True:
            pi_pwm1.stop()
            pi_pwm2.stop()
            R1_state = False
            GPIO.output(R1, R1_state)
            self.btnFans.setIcon(QIcon(QPixmap(":/Images/off.png")))
            _thread.start_new_thread(setfanlcd, (0.1, 0.5))
            GPIO.remove_event_detect(TACH1)
            time.sleep(0.1)
            GPIO.remove_event_detect(TACH2)
        else:
            R1_state = True
            GPIO.output(R1, R1_state)
            self.btnFans.setIcon(QIcon(QPixmap(":/Images/on.png")))
            pi_pwm1.start(float(self.sldfan1.value()))
            pi_pwm2.start(float(self.sldfan2.value()))
            GPIO.add_event_detect(TACH1, GPIO.FALLING, fell1)
            time.sleep(0.1)
            GPIO.add_event_detect(TACH2, GPIO.FALLING, fell2)
            _thread.start_new_thread(setfanlcd, (0.1, 0.5))

    def changepump(self):
        global R2_state
        if R2_state == True:
            R2_state = False
            GPIO.output(R2, R2_state)
            self.btnPump.setIcon(QIcon(QPixmap(":/Images/off.png")))
        else:
            R2_state = True
            GPIO.output(R2, R2_state)
            self.btnPump.setIcon(QIcon(QPixmap(":/Images/on.png")))
            _thread.start_new_thread(settemplcd, (0.1, 0.5))

    def changedutycycle(self):
        duty1 = self.sldfan1.value()
        duty2 = self.sldfan2.value()
        pi_pwm1.ChangeDutyCycle(float(duty1))
        pi_pwm2.ChangeDutyCycle(float(duty2))

def fell1(n):
    global t1
    global rpm1
    dt = time.time() - t1
    if dt < 0.01:
        return  # reject spuriously short pulses
    freq = 1 / dt
    rpm1 = (freq / 2) * 60
    t1 = time.time()
    return rpm1

def fell2(n):
    global t2
    global rpm2
    dt = time.time() - t2
    if dt < 0.01:
        return  # reject spuriously short pulses
    freq = 1 / dt
    rpm2 = (freq / 2) * 60
    t2 = time.time()
    return rpm2

def setfanlcd(delay1, delay2):
    while R1_state == True:
        ui.lcdfan1.setProperty("value", rpm1)
        ui.lcdfan2.setProperty("value", rpm2)
        time.sleep(1)
    if R1_state == False:
        ui.lcdfan1.setProperty("value", 0)
        ui.lcdfan2.setProperty("value", 0)

def read_temp_raw(sensor):
    device_folder = glob.glob(base_dir + sensor)[0]
    device_file = device_folder + '/w1_slave'
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp(sensor):
    lines = read_temp_raw(sensor)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = round((float(temp_string) / 1000.0), 1)
        return temp_c

def settemplcd(delay1, delay2):
    while R2_state == True:
        sensor_sens1 = round(
            ((((read_temp(sens1) - 3.0) * 99.0) / 98.8) + 3.0), 1)
        sensor_sens2 = round(
            ((((read_temp(sens2) - 3.0) * 99.0) / 98.0) + 3.0), 1)
        ui.lcdtemp1.setProperty("value", sensor_sens1)
        ui.lcdtemp2.setProperty("value", sensor_sens2)
        time.sleep(delay2)







if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
