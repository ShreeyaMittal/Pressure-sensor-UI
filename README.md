# Pressure-sensor-UI
## User Report
### Pressure Sensor: Honeywell
 ABPDJJT001PGAA5
Pin out
Pin 1: GND
Pin 3: Vout
Pin 6: VDD
### Pressure Calibration
Done using barometer in lab. 
The output voltage can be estimated as pressure (V to mbar) using the barometer.
Pressure = (averageVoltage-0.47)*0.981/0.057 + 1013 (mbar)
Note: Standard pressure (1 atm) = 1013 mbar at 0.48 V, every additional 1 cm of water increases pressure by 0.057 V on the barometer, and 1 cm water equals 0.981 mbar pressure.
### Arduino IDE
#### Setup: Install a Python Environment (preferably in VS Code) and the latest version of Arduino IDE. Connect the Arduino board to the PC via a USB serial port and check the connection.
Install the library DFRobot_RGBLCD1602 from Github (click on Download ZIP). On Arduino IDE, go to Sketch→ Include Library →Add .ZIP Library and select the library from its stored location. 
Compile and upload the code to Arduino Mega 2560. Once that is done, shut down the IDE. The board will keep running the code once it has been uploaded.

### Python code
1. Once the Arduino board is connected to the PC, check the Arduino serial monitor for information on which port is used for data transfer, and change the arduino_port value in line 21 (you may also change the baud_rate in line 22 if needed).
2. Change the output_folder value in line 40, to wherever you want to store the output files in your system once they are generated. If not, the folder names currently given will be created in your system.
3. Once the code is run, a UI window will show up. The user has to input their name, the detector number, and the initial temperature and pressure values. If the program is to be run for a specific duration of time, input that at the bottom of the window (Duration: Hours, Minutes, and Seconds) and click Submit. If not, just click Submit and click Stop whenever you wish the program to stop running. If you do so after inputting a specific duration, it will still stop as soon as the button is pressed.
4. Once the Submit button is pressed, a live plot will show up that updates with every new pressure reading. The lcd display and GUI window update simultaneously, and new values are samples and averaged over every 10 seconds.
### Functions:
1. exp_fit() creates a fitted version of the pressure data readings so that users can compare the actual readings with the theoretical values.
2. update_timer() updates the Elapsed Time Display on the primary GUI window. It also stops the program after the desired time interval (if inputted before starting the data collection)
3. is_file_empty(file_path) returns whether the file location of file_path is empty or contains a blank file.
4. create_xml_file() creates an .xml file with column values of Timestamp, Elapsed Time and Pressure when the program ends. This file is created in the output folder path defined earlier with the name ‘output_data.xml’ and a message box shows up confirming its creation, name and location.
5. create_latex_file()creates a pdf file using LaTeX for formatting. The first section contains details from the user input, the second section contains the table of pressure values collected during the runtime, and the third section contains the plots.
6. on_close() handles the closing of the main GUI window, to properly deal with temporary files created and packages used during runtime.
7. submit_data() is the event handler of the ‘Submit’ button. It starts the program and disables the input fields. It also launches the second GUI window to plot the live pressure values while they are collected. It also launches:
- read_from_serial(): prints the live pressure reading on the UI window and pushes each new value inside the data buffer. To do this it calls:
  - update_gui_log(data): Updates the main window continuously.
- update_plot(): updates the second UI window with the live plot to increment each new pressure value to the graph as it is read. Updates the plot window every 3 seconds.
8. stop_data(): calls on create_latex_file and create_xml_file, and stops reading values from the sensor. It also writes each value in the data buffer to a .txt file in the same folder, as ‘output.txt’ and shows a message box to confirm the creation of the PDF, TXT and XML files.

 
Optimal Package Versions
ipykernel: 6.29.5
ipython: 8.27
iso8601: 2.1.0
jupyter_client: 8.6.3
lxml: 5.3.1
matplotlib: 3.9.2
matplotlib-inline: 0.1.7
numpy: 1.1 – 1.7/2.2.3
namex: 0.0.8
openpyxl: 3.1.5
pdflatex: 0.1.3
PyLaTeX: 1.4.2
MikTex: latest version
pylatexenc: 2.10
PyAML: 6.0.2
scipy: 1.14.1
serial: 0.0.97
Note
While installing the packages make sure that python is added to path.
The same is true for the installation of MiKTeX
Path can be accessed by going to System → Control Panel → Edit environment variables → PATH→Edit and add the location of your packages 
To verify the installation of packages after installation you can run pip show <packagename>, or inside terminal run python, and then write:
>>>import package_name
>>>print(package_name.__file__)
