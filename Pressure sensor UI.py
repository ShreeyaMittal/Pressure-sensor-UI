import tkinter as tk
from tkinter import messagebox, scrolledtext
import serial
from datetime import datetime
import threading
import time
import os
#import subprocess
from pylatex.utils import NoEscape
from pylatex import Document, Section, Command, LongTable, NewLine, Figure
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure as Fig
import xml.etree.ElementTree as ET
import sys
import scipy
import numpy as np

#(change port as necessary)
arduino_port = 'COM9'
baud_rate = 9600

start_time=None
elapsed_time=0
collecting=False
data_buffer=[]
timestamps=[]
current_duration=[]
pressures=[]

plot_window, canvas = None, None  # reference to the plot window
#fitted_plot_window, canvas_fit=None, None #reference to fitted plot window
ax, fig = None, None  #reference to the plot axis
#ax_fit, fig_fit=None, None #reference to fitted plot axis

stop_flag=False
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

output_folder = f"D:\SNU Files\CERN\Arduino code\Pressure_sensor_Voltage_reading/PressureMonitorOutput_{timestamp}"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

def exp_fit(x, m, t, b):
    return m * np.exp(-x / t) + b
# Function to update the elapsed time display
def update_timer():
    if collecting and not stop_flag:
        global elapsed_time
        elapsed_time = time.time() - start_time
        timer_label.config(text=f"Elapsed Time: {elapsed_time:.1f} sec")

        #checking if duration is reached

        total_duration_seconds=(hours_var.get()*3600)+(minutes_var.get()*60)+(seconds_var.get())
        if total_duration_seconds > 0 and elapsed_time >= total_duration_seconds:
            messagebox.showinfo("Time Over", "The program has concluded reading pressure data")
            print("Time limit reached. Stopping data collection.")
            stop_data()
            return
        root.after(100, update_timer)

# Function to check if the file is empty
def is_file_empty(file_path):
    return not os.path.exists(file_path) or os.stat(file_path).st_size == 0
def create_xml_file():
    global timestamps, current_duration, pressures
    try:
        root_xml = ET.Element("DataLog") 
        metadata = ET.SubElement(root_xml, "Metadata")
        ET.SubElement(metadata, "DataLogger").text = field1_entry.get()
        ET.SubElement(metadata, "DetectorNumber").text = field2_entry.get()
        measurements = ET.SubElement(root_xml, "Measurements")
        
        #Adding data to the XML file
        for i in range(len(timestamps)):
            measurement = ET.SubElement(measurements, "Measurement", SerialNumber=str(i + 1))
            ET.SubElement(measurement, "Timestamp").text = timestamps[i]
            ET.SubElement(measurement, "ElapsedTime").text = f"{current_duration[i]:.2f}"  # Seconds
            ET.SubElement(measurement, "Pressure").text = f"{pressures[i]:.6f}"  # Full precision

        #Save the XML file
        xml_filename = os.path.join(output_folder, "output_data.xml")
        tree = ET.ElementTree(root_xml)
        tree.write(xml_filename, encoding="utf-8", xml_declaration=True)
        print(f"XML file successfully created: {xml_filename}")
        messagebox.showinfo("XML created", f"XML file successfully created: {xml_filename}")
    except Exception as e:
        print(f"Error generating XML file: {e}")
        messagebox.showerror("XML Creation Error", "Error generating XML file.")

def create_latex_file():
    global elapsed_time, timestamps, current_duration, pressures
    data_logger=field1_entry.get()
    detector_number=field2_entry.get()
    init_temperature=field3_entry.get()
    init_pressure=field4_entry.get()
    doc=Document()
    #document title and section
    doc.preamble.append(Command('title', 'Arduino Data Collection'))
    doc.preamble.append(Command('author', f'Data Logger: {data_logger}'))
    doc.append(NoEscape(r'\maketitle'))
    start_time=None
    with doc.create(Section('Run Details: ')):
        doc.append(NewLine(f"Detector Number: {detector_number}"))
        doc.append(NewLine(f"Initial Temperature Value: {init_temperature}"))
        doc.append(NewLine(f"Initial Pressure Value: {init_pressure}"))
    
    with doc.create(Section('Collected Data:')):
        serial_number=1
        with doc.create(LongTable('|c|c|c|')) as table:
            table.add_hline()
            table.add_row(('Serial Number','Timestamp', 'Pressure (mbar/hPa)'))
            table.add_hline()
            table.end_table_header()
        #appending the data to the LaTeX document
        for entry in data_buffer:
            if "Arduino Mega is running" in entry or "Operator" in entry:
                continue
            else:
                timestamp_str, pressure_str = entry.split(", ")
                pressure=float(pressure_str)  # Extract pressure value
                timestamp = datetime.strptime(timestamp_str.strip(), "%Y-%m-%d %H:%M:%S")
                timestamps.append(timestamp_str)

                if start_time is None:#first valid entry
                    start_time = timestamp

                elapsed_time_1 = (timestamp - start_time).total_seconds()  # Convert to seconds
        
                # Add the collected data to the LaTeX table
                table.add_row((serial_number, f"{elapsed_time_1: .2f}", pressure))
                current_duration.append(elapsed_time_1)
                pressures.append(float(pressure))#for plotting the graph
                #pressure_data.append([pressure_str])
            serial_number+=1
            table.add_hline()
        doc.append(NewLine(""))
        doc.append(NewLine(f"Total runtime: {elapsed_time}"))
 
    #Plot the timestamps and pressure values
    if timestamps and pressures and current_duration:
        plt.figure(figsize=(8,4))
        plt.plot(current_duration, pressures, marker='o', linestyle='-', color='b', markersize=4)
        plt.xlabel("Elapsed Time")
        plt.ylabel("Pressure(mbar/hPa)")
        plt.title("Pressure Over Time")
        plt.grid(True)
        # Save the plot as a PDF to embed in LaTeX
        plot_filename='pressure_plot.pdf'
        plot_path = os.path.join(output_folder, plot_filename)
        plt.savefig(plot_path, format='pdf', bbox_inches='tight')
        plt.close()

        # Save final fitted curve plot
    fitted_plot_filename = "fitted_plot.pdf"
    fitted_plot_path = os.path.join(output_folder, fitted_plot_filename)

    if len(current_duration) > 2:
        a_type = np.column_stack((np.array(current_duration), np.array(pressures)))
        params, _ = scipy.optimize.curve_fit(exp_fit, a_type[:, 0], a_type[:, 1])
        m, t, b = params

        fit_x = np.linspace(min(current_duration), max(current_duration), 100)
        fit_y = exp_fit(fit_x, m, t, b)

        plt.figure(figsize=(8, 4))
        plt.scatter(current_duration, pressures, color='blue', label="Actual Data")
        plt.plot(fit_x, fit_y, color='red', linestyle='--', label="Fitted Curve")
        plt.xlabel("Elapsed Time (s)")
        plt.ylabel("Pressure (mbar/hPa)")
        plt.title("Fitted Exponential Decay")
        plt.legend()
        plt.grid(True)
        plt.savefig(fitted_plot_path, format='pdf', bbox_inches='tight')
        plt.close()

        # Compute R²
        squaredDiffs = np.square(a_type[:, 1] - exp_fit(a_type[:, 0], m, t, b))
        squaredDiffsFromMean = np.square(a_type[:, 1] - np.mean(a_type[:, 1]))
        rSquared = 1 - np.sum(squaredDiffs) / np.sum(squaredDiffsFromMean)
        rSquared1 = round(rSquared, 3)

        # Embed the plot inside the PDF
        with doc.create(Section("Pressure Plot")):
            with doc.create(Figure(position='htbp')) as plot:
                plot.add_image(plot_path, width=NoEscape(r'0.9\textwidth'))  # Properly include image
                plot.add_caption("Pressure variation over time.")

            with doc.create(Figure(position='htbp')) as plot2:
                plot2.add_image(fitted_plot_path, width=NoEscape(r'0.9\textwidth'))
                plot2.add_caption(f"Fitted exponential decay curve (R² = {rSquared1}).")


    try:
        tex_path = os.path.join(output_folder, "output")
        doc.generate_pdf(tex_path, compiler='pdflatex')
        print("PDF successfully created.")
    except Exception as e:
        print(f"Error generating PDF: {e}")
        
        if not os.path.exists(f"{tex_path}.tex"):
            print("Output.tex was not created.")
            return
        aux_files=[f"{tex_path}.aux", f"{tex_path}.log", f"{tex_path}.out", f"{tex_path}.tex"]
        for file in aux_files:
            if os.path.exists(file):
                os.remove(file)
                print(f"Deleted {file}")
def on_close():
    global stop_flag
    if not stop_flag:
        stop_data()  # Ensure data collection stops
    root.quit()
    root.destroy()
    print("Cleanup and exiting program...")
    sys.exit()

def submit_data():
    global collecting, start_time, stop_flag, data_buffer, start_time, elapsed_time, pressure_values, x_time
    collecting=True
    stop_flag=False
    pressure_values=[]
    x_time=[]
    start_time=time.time()
    update_timer()
    
    field1_data = field1_entry.get()
    field2_data = field2_entry.get()
    field3_data=float(field3_entry.get())
    field4_data=float(field4_entry.get())
    #disabling input fields for the duration of the runtime
    
    submit_button.config(state=tk.DISABLED)
    hours_entry.config(state=tk.DISABLED)
    minutes_entry.config(state=tk.DISABLED)
    seconds_entry.config(state=tk.DISABLED)
    field1_entry.config(state=tk.DISABLED)
    field2_entry.config(state=tk.DISABLED)
    field3_entry.config(state=tk.DISABLED)
    field4_entry.config(state=tk.DISABLED)

    data_buffer.append(f"Operator: {field1_data}, Sensor: {field2_data}")
    #second GUI window
    plot_window=tk.Toplevel(root)
    plot_window.title("Live Pressure Plot")
    fig, ax=plt.subplots(figsize=(8,4))
    ax.set_xlabel("Elapsed Time (s)")
    ax.set_ylabel("Pressure (mbar/hPa)")
    ax.set_title("Live Pressure over Time")
    ax.grid(True)
    #implementing figure in a Tk window
    canvas=FigureCanvasTkAgg(fig, master=plot_window)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    #live updates
    #update_plot()
    #threading.Thread(target=read_from_serial, daemon=True).start()
    try:
        ser = serial.Serial(arduino_port, baud_rate, timeout=1)
        if not ser.is_open:
            ser.open()
        time.sleep(2)  # Give some time for the connection to establish
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open serial port: {e}")
        return
    label_text = f"Initial Temperature: {field3_data:.2f} mbar | Initial Pressure: {field4_data:.2f} °C"
    initial_label = tk.Label(plot_window, text=label_text)
    initial_label.pack(pady=5)  # Add some spacing above the plot

    def read_from_serial():
        global collecting
        try:
            while collecting and not stop_flag and ser.is_open:
                if ser.in_waiting > 0:
                    arduino_data = ser.readline().decode('utf-8').strip()
                    #print(f"Raw Serial Data: '{arduino_data}'")#debugging message
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    elapsed=time.time()-start_time 
                    try:
                        p_value = float(arduino_data)  # Convert pressure value
                        print ("Pressure live: ", p_value)
                        pressure_values.append(p_value)
                        x_time.append(elapsed)

                        formatted_data = f"{timestamp}, {arduino_data}"
                        data_buffer.append(formatted_data)
                        root.after(0, update_gui_log, arduino_data)
                        #for latest reading only, replace formatted data with arduino data

                    except (IndexError, ValueError):
                        continue  # Ignore invalid float conversion

        except Exception as e:
            messagebox.showerror("Error", f"Serial Read Error: {e}")
        
        finally:
            ser.close()
    def update_plot():
        #print("Updating plot...")
        if not collecting or stop_flag or not plot_window.winfo_exists():
            #print("Plot update stopped.")
            return
        
        ax.clear()  # This clears the entire plot correctly
        ax.plot(x_time, pressure_values, marker='o', linestyle='-', color='b', markersize=4)
    
        ax.set_xlabel("Elapsed Time (s)")
        ax.set_ylabel("Pressure (mbar/hPa)")
        ax.set_title("Pressure Over Time")
        ax.grid(True)
        canvas.draw()
        plot_window.after(3000, update_plot)

    def update_gui_log(data):
        print(f"Updating GUI log with: {data}")  # Debug print
        #output_text.config(state=tk.NORMAL)
        #output_text.insert(tk.END, data + "\n")
        #output_text.config(state=tk.DISABLED)
        #output_text.yview(tk.END)#auto-scrolling, might disable later on
        #for latest reading only,
        latest_reading_label.config(text=f"Latest Reading: {data}")

    if ser.is_open:
        try:
            # Write data to the Arduino
            ser.write(f"{field1_data},{field2_data}\n".encode('utf-8'))
            status_label.config(text="Data Sent to Arduino")
            read_thread = threading.Thread(target=read_from_serial)
            read_thread.daemon = True
            read_thread.start()
            update_plot()
            #pressure plot
            #show_pressure_plot()
        except Exception as e:
            status_label.config(text=f"Error: {str(e)}")
            ser.close()
    else:
        status_label.config(text="Could not open serial port.")

def stop_data():
    global collecting, stop_flag
    collecting=False
    stop_flag=True
    #Re-enabling Submit button and duration inputs
    field1_entry.config(state=tk.NORMAL)
    field2_entry.config(state=tk.NORMAL)
    field3_entry.config(state=tk.NORMAL)
    field4_entry.config(state=tk.NORMAL)
    submit_button.config(state=tk.NORMAL)
    hours_entry.config(state=tk.NORMAL)
    minutes_entry.config(state=tk.NORMAL)
    seconds_entry.config(state=tk.NORMAL)
    status_label.config(text="Data collection stopped")

    if data_buffer:
        create_latex_file()
        create_xml_file()
        
        messagebox.showinfo("PDF Generated", "PDF has been generated from the collected data.")
        # Writing data to a file
        with open(os.path.join(output_folder, "sensor_reading.txt"), "a") as file:
            if is_file_empty("sensor_reading.txt"):
                file.write("Timestamp,Arduino Data\n")
            for line in data_buffer:
                file.write(line + "\n")
        messagebox.showinfo("Saved", "Data saved to sensor_reading.txt")

    status_label.config(text="Data collection stopped")

# Create the main window
root = tk.Tk()
root.title("Data Submission GUI")
hours_var=tk.IntVar()
minutes_var=tk.IntVar()
seconds_var=tk.IntVar()

# Adding UI elements for setting time limits
tk.Label(root, text="Duration: Hours:").grid(row=8, column=0, padx=5, pady=5)
hours_entry = tk.Entry(root, textvariable=hours_var, width=5)
hours_entry.grid(row=8, column=1, padx=5, pady=5)

tk.Label(root, text="Minutes:").grid(row=9, column=0, padx=5, pady=5)
minutes_entry = tk.Entry(root, textvariable=minutes_var, width=5)
minutes_entry.grid(row=9, column=1, padx=5, pady=5)

tk.Label(root, text="Seconds:").grid(row=10, column=0, padx=5, pady=5)
seconds_entry = tk.Entry(root, textvariable=seconds_var, width=5)
seconds_entry.grid(row=10, column=1, padx=5, pady=5)

# Create input fields and labels
tk.Label(root, text="Operator Name:").grid(row=0, column=0, padx=10, pady=10)
field1_entry = tk.Entry(root)
field1_entry.grid(row=0, column=1, padx=10, pady=10)

tk.Label(root, text="Detector Number").grid(row=1, column=0, padx=10, pady=10)
field2_entry = tk.Entry(root)
field2_entry.grid(row=1, column=1, padx=10, pady=10)

tk.Label(root, text="Initial Temperature (C)").grid(row=2, column=0, padx=10, pady=10)
field3_entry = tk.Entry(root)
field3_entry.grid(row=2, column=1, padx=10, pady=10)

tk.Label(root, text="Initial Pressure (mbar)").grid(row=3, column=0, padx=10, pady=10)
field4_entry = tk.Entry(root)
field4_entry.grid(row=3, column=1, padx=10, pady=10)

button_frame=tk.Frame(root)
button_frame.grid(row=4, column=0, columnspan=2, pady=10)

submit_button = tk.Button(button_frame, text="Submit", command=submit_data)
submit_button.pack(side=tk.LEFT, padx=10)

stop_button = tk.Button(button_frame, text="Stop", command=stop_data)
stop_button.pack(side=tk.RIGHT, padx=10)
#label displaying elapsed time
timer_label = tk.Label(root, text="Elapsed Time: 0.0 sec")
timer_label.grid(row=5, column=0, columnspan=2, padx=10, pady=5)

#label displaying status messages
status_label = tk.Label(root, text='')
status_label.grid(row=6, column=0, columnspan=2, padx=10, pady=5)

latest_reading_label = tk.Label(root, text="Live Pressure Reading: ")
latest_reading_label.grid(row=7, column=0, columnspan=2, padx=10, pady=5)
root.protocol("WM_DELETE_WINDOW", on_close)
# Start the Tkinter event loop
root.mainloop()

# Debug: Show that this is reached if the program exits
print("Exited the Tkinter event loop.")

