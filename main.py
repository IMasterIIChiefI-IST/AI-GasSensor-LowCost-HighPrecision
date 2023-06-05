import math
import time
import tkinter as tk
from collections import OrderedDict
from datetime import datetime
from math import log10, sin
from random import randint
from time import sleep
from typing import Union
import matplotlib
import numpy as np
import pandas as pd

CALIBRATION_SAMPLE_TIMES: int = 50
CALIBRATION_SAMPLE_INTERVAL: int = 500
READ_SAMPLE_INTERVAL: int = 50
READ_SAMPLE_TIMES: int = 5


# SOME PARTS OF THE CODE WAS BASED AND REVERSED ENGINEERED FROM THE SENSOR CALIBRATION ARDUINO CODE FROM
# sandboxelectronics.com MQ2 SENSOR MODULE

# From the TECHNICAL DATA graphs Clean_Air constant
# Clean_Air_Rs_Ro = [.9777, .7999, .9956, .5563] # Clean_Air_Rs_Ro  = Log10(graph_clean_air)
# The resistance used when generating the TECHNICAL DATA graphs
# Ro_defaults = [10, 20, 10, 20]
# Rs_CLEAN_AIR = [Rl_defaults[i] * Clean_Air_defaults[i] for i in range(len(Clean_Air_defaults))]
# The real resistance used on the modules
# Ro = [.998, .989, .996, 1.984]
# RO_CLEAR_AIR_FACTOR=(Sensor resistance in clean air)/RO, which is derived from the chart in datasheet
# Ro_CLEAN_AIR_FACTOR = [Rs_CLEAN_AIR[i] / Ro[i] for i in range(len(Clean_Air_defaults))]
# VOLTAGE CONSTANT
# Voltage5V = 5


class MQ_Sensor:
    gases = None

    def __init__(self, Clean_Air_Rs_Ro, Ro_defaults, Ro, Rs_CLEAN_AIR=None, Ro_CLEAN_AIR_FACTOR=None,
                 Voltage=5 + np.random.normal(0, 1)):
        self.my_class = None
        self.Clean_Air_defaults = Clean_Air_Rs_Ro
        self.Rl_defaults = Ro_defaults
        if Rs_CLEAN_AIR is None:
            self.Rs_CLEAN_AIR = Ro_defaults * Clean_Air_Rs_Ro
        self.Ro = Ro
        if Ro_CLEAN_AIR_FACTOR is None:
            self.Ro_CLEAN_AIR_FACTOR = self.Rs_CLEAN_AIR / self.Ro
        self.Voltage = Voltage

    @staticmethod
    def noise(amplitude=1):
        return np.random.normal(0, amplitude)

    def Bits_out(self, volt, noise):
        return (float(volt) * 1023) / (self.Voltage + noise)

    def Voltage_out(self, rs_ro, noise):
        # Rs = rs_ro * self.Ro #only when the REAL ro is equal to the experimental ro
        rs = rs_ro * (self.Ro * self.Ro_CLEAN_AIR_FACTOR)
        v_out = (self.Voltage + noise) * self.Ro / (self.Ro + rs)
        return v_out

    @staticmethod
    def Rs_Ro_ratio(ppm, x, y, m):
        # log(rs_ro) = m * (log(ppm) - x) + y
        rs_ro = pow(10, m * (log10(ppm) - x) + y)
        return rs_ro

    @staticmethod
    def PPM(rs_ro, x, y, m):
        # log(ppm) = (log(rs_ro) - y) / m + x
        ppm = pow(10, ((log10(rs_ro) - y) / m) + x)
        return ppm

    def Rs(self, raw_adc, noise):
        raw_adc += noise
        rs = 0
        for i in range(READ_SAMPLE_TIMES):
            rs += (self.Ro * (1023 - raw_adc) / raw_adc)
            sleep(READ_SAMPLE_INTERVAL)
        rs = rs / READ_SAMPLE_TIMES
        return rs

    def Ro(self, raw_adc, noise):
        raw_adc += noise
        ro = 0
        for i in range(CALIBRATION_SAMPLE_TIMES):
            ro += (self.Ro * (1023 - raw_adc) / raw_adc)
            sleep(READ_SAMPLE_INTERVAL)
        ro = ro / CALIBRATION_SAMPLE_TIMES
        ro = ro / self.Ro_CLEAN_AIR_FACTOR
        return ro

    @property
    def get_gases(self):
        if self.gases is None:
            raise ValueError("For each sensor you must calculate the lines for the gases")
        for key in list(self.gases.keys()):
            if len(self.gases[key]) != 3:
                raise ValueError(
                    "The data inserted follows the wrong data type , there should only be 3 fields X, Y ,M ")
            for elem in self.gases[key]:
                if not isinstance(elem, (int, float, bytes)):
                    raise ValueError("The data inserted follows the wrong data type")

        return list(self.gases.keys())

    def Generate(self, ppm: Union[dict, OrderedDict]):
        if not isinstance(ppm, (dict, OrderedDict)):
            raise ValueError("the input data must be a dictionary")
        if not set(ppm.keys()).issubset(set(self.gases.keys())):
            raise ValueError(
                "Check the gases names are correctly written or there is some missing gasses for this sensor")
        result = []
        for key in self.gases.keys():
            result.append(self.Rs_Ro_ratio(ppm[key], **self.gases[key]))
        return pd.Series(result, index=set(self.gases.keys()))


class MQ_2(MQ_Sensor):
    # MQ_2
    # data format:{ x, y, slope} (after Log10)
    gases = {
        "H2": [2.30103, 0.32222, -0.481],
        "LPG": [2.30103, 0.20412, -0.4645],
        "CH4": [2.30103, 0.49136, -0.3841],
        "CO": [2.30103, 0.7076, -0.3494],
        "Alcohol": [2.30103, 0.4624, -0.3903],
        "Smoke": [2.30103, 0.5185, -0.4358],
        "C3H8": [2.30103, 0.23045, -0.47033]
    }

    def __init__(self, Clean_Air_Rs_Ro, Ro_defaults, Ro, Rs_CLEAN_AIR=None, Ro_CLEAN_AIR_FACTOR=None,
                 Voltage=5 + np.random.normal(0, 1)):
        super().__init__(Clean_Air_Rs_Ro, Ro_defaults, Ro, Rs_CLEAN_AIR, Ro_CLEAN_AIR_FACTOR, Voltage)


class MQ_5(MQ_Sensor):
    # MQ_5
    # data format:{ x, y, slope} (after Log10)
    gases = {
        "H2": [2.30103, 0.24304, -0.25],
        "LPG": [2.30103, -0.22185, -0.391],
        "CH4": [2.30103, -0.3152, -0.5457],
        "CO": [2.30103, 0.59106, -0.14635],
        "Alcohol": [2.30103, 0.5185, -0.2381]
    }

    def __init__(self, Clean_Air_Rs_Ro, Ro_defaults, Ro, Rs_CLEAN_AIR=None, Ro_CLEAN_AIR_FACTOR=None,
                 Voltage=5 + np.random.normal(0, 1)):
        super().__init__(Clean_Air_Rs_Ro, Ro_defaults, Ro, Rs_CLEAN_AIR, Ro_CLEAN_AIR_FACTOR, Voltage)


class MQ_9(MQ_Sensor):
    # MQ_9
    # data format:{ x, y, slope} (after Log10)
    gases = {
        "LPG": [2.30103, 0.32222, -0.4809],
        "CH4": [2.30103, 0.49136, -0.3804],
        "CO": [2.30103, 0.20412, -0.4385]
    }

    def __init__(self, Clean_Air_Rs_Ro, Ro_defaults, Ro, Rs_CLEAN_AIR=None, Ro_CLEAN_AIR_FACTOR=None,
                 Voltage=5 + np.random.normal(0, 1)):
        super().__init__(Clean_Air_Rs_Ro, Ro_defaults, Ro, Rs_CLEAN_AIR, Ro_CLEAN_AIR_FACTOR, Voltage)


class MQ_135(MQ_Sensor):
    # MQ_135
    # data format:{ x, y, slope} (after Log10)
    gases = {
        "CO": [1, 0.4624, -0.268],
        "Alcohol": [1, 0.279, -0.3103],
        "CO2": [1, 0.3423, -0.3377],
        "NH4": [1, 0.3802, -0.3883],
        "Toluene": [1, 0.14613, -0.26655],
        "Acetone": [1, 0.1139, -0.2637]
    }

    def __init__(self, Clean_Air_Rs_Ro, Ro_defaults, Ro, Rs_CLEAN_AIR=None, Ro_CLEAN_AIR_FACTOR=None,
                 Voltage=5 + np.random.normal(0, 1)):
        super().__init__(Clean_Air_Rs_Ro, Ro_defaults, Ro, Rs_CLEAN_AIR, Ro_CLEAN_AIR_FACTOR, Voltage)


def main():
    sensors = [MQ_2(Clean_Air_Rs_Ro=.9777, Ro_defaults=10, Ro=.998),
               MQ_5(Clean_Air_Rs_Ro=.7999, Ro_defaults=20, Ro=.989),
               MQ_9(Clean_Air_Rs_Ro=.9956, Ro_defaults=10, Ro=.996),
               MQ_135(Clean_Air_Rs_Ro=.5563, Ro_defaults=20, Ro=1.984)]

    # Create the Tkinter window
    window = tk.Tk()

    gases = []
    for obj in sensors:
        gases.extend(obj.get_gases)

    gases_ppm = {string: 0 for string in set(gases)}

    # Get the screen width and height
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # Calculate the maximum size for the window
    max_window_width = int(screen_width * 0.8)  # Set the maximum width to 80% of the screen width
    max_window_height = int(screen_height * 0.8)  # Set the maximum height to 80% of the screen height

    # Calculate the scale factor for elements
    scale_factor = min(max_window_width, max_window_height) // 1100  # Adjust the scale factor as needed

    def update_total_points(value):
        if sample_time_slider.get() == 0:
            total_points_label.config(text="Total Points: inf")
            record_switch.config(state="disabled")
            return
        else:
            total_points = int(sample_time_slider.get() * runtime_slider.get())  # Calculate the total points
            total_points_label.config(text=f"Total Points: {total_points}")
            record_switch.config(state="normal")
            return

    def set_random_value(gas):
        for knob in knobs:
            if knob[1] == gas:
                knob[0].set(randint(10, 10000))
                return

    def update_variable(value, gas):
        gases_ppm[gas] = int(value)

    def handle_switch(gas, switch):
        if switch.get():
            for knob in knobs:
                if knob[1] == gas and knob[2] == switch:
                    knob[0].config(state="normal")
                    return
        else:
            for knob in knobs:
                if knob[1] == gas and knob[2] == switch:
                    knob[0].config(state="disabled")
                    return

    def animate_slider(gas, animate_switch_var):
        if not animate_switch_var.get():
            return
        for knob in knobs:
            if knob[1] == gas:
                offset_slider = knob[4]
                freq_entries = knob[5]
                amplitude_entries = knob[6]
                phase_entries = knob[7]
                break
        freqs = []
        amps = []
        phases = []
        offset = offset_slider.get()
        for freq_entry, amplitude_entry, phase_entry in zip(freq_entries, amplitude_entries, phase_entries):
            if not float(freq_entry.get()) == 0 and not float(amplitude_entry.get()) == 0:
                freqs.append(float(freq_entry.get()))
                amps.append(float(amplitude_entry.get()))
                phases.append(float(phase_entry.get()))
        start_time = time.time()
        if len(freqs) > 0:
            total_sum = sum(amps)
            if total_sum >= 10000:
                amps = [(value+offset) * 10000 / total_sum for value in amps]
        while animate_switch_var.get():
            elapsed_time = time.time() - start_time
            values = [amp * math.sin(2 * math.pi * freq * elapsed_time + phase) for freq, amp, phase
                      in zip(freqs, amps, phases)]
            if len(freqs) > 0:
                knob_value = sum(values) + offset
            else:
                knob_value = knob[0].get()
            if knob_value > 10000:
                knob_value = 10000
            if mains_noise_var.get():
                knob_value -= randint(1, 15) * math.sin(2 * math.pi * 60 * elapsed_time)
            knob[0].set(knob_value)
            window.update()
            time.sleep(0.01)

    def recording(recording_switch_var):
        if not recording_switch_var.get():
            return

        # Create an empty DataFrame to store the knob values
        data_frame = pd.DataFrame()

        start_time = time.time()
        end_time = start_time + (float(runtime_slider.get()) * 60)
        if float(sample_time_slider.get()) == 0:
            sample_time = (float(runtime_slider.get()) * 60)
        else:
            sample_time = float(sample_time_slider.get()) * 60

        while time.time() < end_time and recording_switch_var.get():
            elapsed_time = time.time() - start_time
            if elapsed_time % sample_time == 0:
                data = {}
                for knob in knobs:
                    data[knob[1]] = knob[0].get()
                series = pd.Series(data)
                data_frame = data_frame.append(series, ignore_index=True)

        current_datetime = datetime.now()
        date_time_string = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")

        # Generate the file name with the date and hour
        file_name = f"knob_data_{date_time_string}.csv"

        # Write the data_frame to a CSV file
        data_frame.to_csv(file_name, index=False)

    knobs = []
    for gas_ppm, i in zip(gases_ppm.keys(), range(len(gases_ppm.keys()))):

        label = tk.Label(window, text=gas_ppm)
        label.grid(row=i, column=0, padx=10 * scale_factor, pady=5 * scale_factor)

        knob = tk.Scale(window, from_=0, to=10000, orient=tk.HORIZONTAL,
                        command=lambda value, gas=gas_ppm: update_variable(value, gas),
                        width=20 * scale_factor, length=200 * scale_factor)
        knob.set(gases_ppm[gas_ppm])
        knob.grid(row=i, column=1, padx=10 * scale_factor, pady=5 * scale_factor)

        offset_slider = tk.Scale(window, from_=0, to=10000, orient=tk.HORIZONTAL, length=120 * scale_factor)
        offset_slider.grid(row=i, column=2, padx=10 * scale_factor, pady=5 * scale_factor)
        offset_slider.set(5000)

        l = 3
        freq_entries = []
        amplitude_entries = []
        phase_entries = []
        frequencies = [[0, 1], [0, 5], [60, 1000]]
        labels = ["low", "med", "high"]
        for j in range(3):
            label = tk.Label(window, text=labels[j])
            label.grid(row=i, column=j + l, padx=10 * scale_factor, pady=5 * scale_factor)

            freq_slider = tk.Scale(window, from_=frequencies[j][0], to=frequencies[j][1], orient=tk.HORIZONTAL,
                                   resolution=0.1,
                                   length=150 * scale_factor)
            freq_slider.grid(row=i, column=j + l + 1, padx=10 * scale_factor, pady=5 * scale_factor)
            freq_entries.append(freq_slider)

            amplitude_slider = tk.Scale(window, from_=0, to=(10000/(j+1)), orient=tk.HORIZONTAL, length=150 * scale_factor)
            amplitude_slider.grid(row=i, column=j + l + 2, padx=10 * scale_factor, pady=5 * scale_factor)
            amplitude_entries.append(amplitude_slider)

            phase_slider = tk.Scale(window, from_=0, to=6.28, orient=tk.HORIZONTAL, resolution=0.1,
                                    length=150 * scale_factor)
            phase_slider.grid(row=i, column=j + l + 3, padx=10 * scale_factor, pady=5 * scale_factor)
            phase_entries.append(phase_slider)
            l += 4

        animate_switch_var = tk.BooleanVar()
        animate_switch_var.set(False)
        animate_switch = tk.Checkbutton(window, text="Animation", variable=animate_switch_var,
                                        command=lambda gas=gas_ppm, s=animate_switch_var: animate_slider(gas, s))

        animate_switch.grid(row=i, column=17, padx=10 * scale_factor, pady=5 * scale_factor)

        enable_switch_var = tk.BooleanVar()
        enable_switch_var.set(True)
        enable_switch = tk.Checkbutton(window, variable=enable_switch_var, onvalue=True, offvalue=False,
                                       command=lambda gas=gas_ppm, s=enable_switch_var: handle_switch(gas, s))
        enable_switch.grid(row=i, column=18, padx=10 * scale_factor, pady=5 * scale_factor)

        random_button = tk.Button(window, text="Random", command=lambda gas=gas_ppm: set_random_value(gas))
        random_button.grid(row=i, column=19, padx=10 * scale_factor, pady=5 * scale_factor)

        knobs.append((knob, gas_ppm, enable_switch_var, random_button, offset_slider, freq_entries, amplitude_entries, phase_entries, animate_switch))  # Add the knob, gas name, switch, random button, runtime entry, sample time

    def disable_sliders():
        for knob in knobs:
            knob[0].config(state="disabled")
            knob[2].set(False)

    # Add the button to disable the sliders
    disable_button = tk.Button(window, text="disable_slider", command=disable_sliders)
    disable_button.grid(row=len(gases_ppm.keys()), column=0, columnspan=1, padx=10 * scale_factor,
                        pady=5 * scale_factor)

    def reset_offset_sliders():
        for knob in knobs:
            knob[4].set(5000)

        # Add the button to disable the sliders

    reset_button = tk.Button(window, text="reset slider", command=reset_offset_sliders)
    reset_button.grid(row=len(gases_ppm.keys()), column=2, columnspan=1, padx=10 * scale_factor, pady=5 * scale_factor)

    def enable_sliders():
        for knob in knobs:
            knob[0].config(state="normal")
            knob[2].set(True)

    # Add the button to disable the sliders
    enable_button = tk.Button(window, text="enable slider", command=enable_sliders)
    enable_button.grid(row=len(gases_ppm.keys()), column=1, columnspan=1, padx=10 * scale_factor, pady=5 * scale_factor)

    def set_random_values():
        for knob in knobs:
            knob[0].set(randint(10, 10000))

    label = tk.Label(window, text="Runtime in min.")
    label.grid(row=len(gases_ppm.keys()), column=3, padx=10 * scale_factor, pady=5 * scale_factor)
    runtime_slider = tk.Scale(window, from_=0, to=60, orient=tk.HORIZONTAL, resolution=0.1,
                              length=150 * scale_factor,
                              command=lambda value: update_total_points(value))
    runtime_slider.grid(row=len(gases_ppm.keys()), column=4, padx=10 * scale_factor, pady=5 * scale_factor)

    label = tk.Label(window, text="Samples per min.")

    label.grid(row=len(gases_ppm.keys()), column=5, padx=10 * scale_factor, pady=5 * scale_factor)

    sample_time_slider = tk.Scale(window, from_=0, to=3600, orient=tk.HORIZONTAL, resolution=0.1,
                                  length=150 * scale_factor,
                                  command=lambda value: update_total_points(value))
    sample_time_slider.grid(row=len(gases_ppm.keys()), column=6, padx=10 * scale_factor, pady=5 * scale_factor)

    total_points_label = tk.Label(window, text="Total Points: 0")
    total_points_label.grid(row=len(gases_ppm.keys()), column=8, padx=10 * scale_factor, pady=5 * scale_factor)

    # Add the button to disable the sliders
    random_button = tk.Button(window, text="Set Random Values", command=set_random_values)
    random_button.grid(row=len(gases_ppm.keys()), column=9, columnspan=2, padx=10 * scale_factor, pady=5 * scale_factor)

    record_switch_var = tk.BooleanVar()
    record_switch_var.set(False)
    record_switch = tk.Checkbutton(window, text="Record", variable=record_switch_var,
                                   command=lambda s=record_switch_var: recording(s))
    record_switch.grid(row=len(gases_ppm.keys()), column=10, padx=10 * scale_factor, pady=5 * scale_factor)

    mains_noise_var = tk.BooleanVar()
    mains_noise_var.set(False)
    mains_noise_switch = tk.Checkbutton(window, text="mains_noise()", variable=mains_noise_var)
    mains_noise_switch.grid(row=len(gases_ppm.keys()), column=11, padx=10 * scale_factor, pady=5 * scale_factor)


    # Start the Tkinter event loop
    window.mainloop()


if __name__ == '__main__':
    main()
