from pyaudio import PyAudio, paInt16
from threading import Thread
import numpy as np
import struct
import math
import os
import time
import magichue
import subprocess

class LedDevice():
    light = None
    keys_list = [0.002, 0.00225, 0.0025, 0.00275, 0.003, 0.00325, 0.0035, 0.00375, 0.004, 0.00425, 0.0045, 0.00475, 0.005, 0.00525, 0.0055, 0.00575, 0.006, 0.00625, 0.0065, 0.00675, 0.007, 0.00725, 0.0075, 0.00775, 0.008, 0.00825, 0.0085, 0.00875, 0.009, 0.00925, 0.0095, 0.00975, 0.01, 0.0125, 0.015, 0.0175, 0.02, 0.0225, 0.025, 0.0275, 0.03, 0.0325, 0.035, 0.0375, 0.04, 0.0425, 0.045, 0.0475, 0.05, 0.0525]
    dic = {0.002: 15, 0.00225: 20, 0.0025: 25, 0.00275: 30, 0.003: 35, 0.00325: 40, 0.0035: 45, 0.00375: 50, 0.004: 55, 0.00425: 60, 0.0045: 65, 0.00475: 70, 0.005: 75, 0.00525: 80, 0.0055: 85, 0.00575: 90, 0.006: 95, 0.00625: 100, 0.0065: 105, 0.00675: 110, 0.007: 115, 0.00725: 120, 0.0075: 125, 0.00775: 130, 0.008: 135, 0.00825: 140, 0.0085: 145, 0.00875: 150, 0.009: 155, 0.00925: 160, 0.0095: 165, 0.00975: 170, 0.01: 175, 0.0125: 180, 0.015: 185, 0.0175: 190, 0.02: 195, 0.0225: 200, 0.025: 205, 0.0275: 210, 0.03: 215, 0.0325: 220, 0.035: 225, 0.0375: 230, 0.04: 235, 0.0425: 255, 0.045: 255, 0.0475: 255, 0.05: 255}
    last_brightness = None
    last_note = None
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

class Settings:
    short_normalize = (1.0/32768.0)
    chunk_size = 1024
    buffer_times = 48
    zero_padding = 3
    sampling_rate = 44100
    audio_analyse = None
    
def exception(message, function):
    print(str(message) + " :: " + function)

def get_rms( block ):
    count = len(block)/2
    format = "%dh"%(count)
    shorts = struct.unpack( format, block )

    sum_squares = 0.0
    for sample in shorts:
        n = sample * Settings.short_normalize
        sum_squares += n*n

    return math.sqrt( sum_squares / count )

class AudioAnalyzer(Thread):
    def __init__(self, *args, **kwargs):
        Thread.__init__(self, *args, **kwargs)

        self.buffer = np.zeros(Settings.chunk_size * Settings.buffer_times)
        self.hanning_window = np.hanning(len(self.buffer))

        self.audio_object = PyAudio()
        self.stream = self.audio_object.open(format=paInt16,
                                                 channels=1,
                                                 rate=Settings.sampling_rate,
                                                 input=True,
                                                 output=True,
                                                 frames_per_buffer=Settings.chunk_size)

    @staticmethod
    def frequency_to_number(freq, a4_freq):
        if freq == 0:
            return 0
        return 12 * np.log2(freq / a4_freq) + 69

    @staticmethod
    def number_to_frequency(number, a4_freq):
        return a4_freq * 2.0 ** ((number - 69) / 12.0)

    @staticmethod
    def number_to_note_name(number):
        return LedDevice.note_names[int(round(number) % 12)]

    def run(self):
        while True:
            block = self.stream.read(Settings.chunk_size, exception_on_overflow=False)
            data = np.frombuffer(block, dtype=np.int16)
            self.buffer[:-Settings.chunk_size] = self.buffer[Settings.chunk_size:]
            self.buffer[-Settings.chunk_size:] = data

            numpydata = abs(np.fft.fft(np.pad(self.buffer * self.hanning_window,
                                                  (0, len(self.buffer) * Settings.zero_padding),
                                                  "constant")))
            numpydata = numpydata[:int(len(numpydata) / 2)]
            
            amplitude = get_rms( block )
            
            index = 0
            brightness_value = 0
            for key, value in LedDevice.dic.items():
                if amplitude < LedDevice.dic[0.002]:
                    brightness_value = 0
                if index == len(LedDevice.keys_list)-2:
                    break
                if float(amplitude) >= float(key) and float(amplitude) <= LedDevice.keys_list[index+1]:
                    if LedDevice.last_brightness == value:
                        break
                    brightness_value = value
                    break
                index += 1
            
            frequencies = np.fft.fftfreq(len(numpydata), 1. / Settings.sampling_rate) / 2

            frequency = round(frequencies[np.argmax(numpydata)], 2)
            Settings.audio_analyse = (self.number_to_note_name(frequency), brightness_value)
            time.sleep(0.00001)
            
        self.stream.stop_stream()
        self.stream.close()
        self.audio_object.terminate()

def change_color(color, brightness):
    print((color, brightness))
    LedDevice.light.rgb = color
    LedDevice.light.brightness = brightness

def exec_command(command):
    cmd = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    out = str(cmd.stdout.read().decode()) + str(cmd.stderr.read().decode())

    return out
    
def detect_led_device():
    scan = exec_command('nmap 192.168.0.1/24 -n -P0 -T4 -p 5577 -Pn --max-retries 2 --open')
    if 'Nmap scan report for ' in  scan:
        ip = scan.split('Nmap scan report for ')[1].split('\n')[0]
        
        return ip
    else:
        print('Device not found!')
        print('Retrying ...')
        return detect_led_device()

def connect():
    ip = detect_led_device()
    time.sleep(0.1)
    print('Detected: ' + ip)
    print('Connecting ...')
    LedDevice.light = magichue.Light(ip)
    LedDevice.light.on = True
    print('Done')

def run_analiser():
    analizer.run()

def main():    
    audio_analiser_thread = Thread(target=run_analiser)
    audio_analiser_thread.start()
    time.sleep(2)

    dic = {
           "C": (255,0,0), #RED
           "C#": (0,60,255), #Dark Blue
           "D": (128,0,255), #Purple
           "D#": (255,171,0), #Orange
           "E": ( 213,0,255), #Pink
           "F": (255,255,0), #Yellow
           "F#": (68,255,0), #green
           "G": (255,162,0), #Orange 
           "G#": (0,179,255), #normal Blue
           "A": (0,255,128), #white green 
           "A#": (0,255,255), #ocean blue 
           "B": (255,255,255) #White
    }

    while True:
        if Settings.audio_analyse == None:
            time.sleep(0.1)
            continue
            
        (note, brightness) = Settings.audio_analyse
        print(LedDevice.light)
        if note != LedDevice.last_note and brightness != LedDevice.last_brightness:
            LedDevice.last_note = note
            LedDevice.last_brightness = brightness
            change_color(dic[note], brightness)
            
        else:
            time.sleep(0.001)
        
connect()
analizer = AudioAnalyzer()
main()
