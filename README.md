# NAVI - A user-friendly, customisable, robust Navigation Assistance device for Visually Impaired 
NaVI is a stand-alone device for guiding visually impaired people to walk independently on streets. Built on Raspberry pi platform, this software allows dynamic addition of waypoints to the graph to be used for navigation. It integrates data from a GPS and IMU to implement a fusion algorithm (Kalman Filter) for precise localisation of the user. Once the destination is entered, the most efficient navigation path is computed and instructions are given to user in the form of audio/vibrations. Based on their experiences, users can simultaneously add more information like new route or additional landmarks (footpaths, barriers, etc) which can be globally updated to make navigation more accessible for all the users. A simple audio-haptic interface is designed, for letting visually impaired people use this device. It can be started on a single button press-An initilisation of the object NaVI().

*** This software has been tested to work on Python 2.7 and may not work on Python 3 ***

# Features
1. Accurate localisation: Upto 2 metres
2. Re-routing 
3. Course correction through vibratory and audio feedback
4. Option to store new routes while navigation
5. Addition of accessibility landmarks like foothpaths, traffic signals, etc
6. Lightweight, Compact
7. Easy to use interface 


# Dependencies

On Raspberry Pi, all python dependencies can be installed by typing "sudo pip install _libraryname_"

## Python Dependencies: all these should be on your PYTHONPATH

* NetworkX 
* aenum
* editdistance
* geopy
* numpy
* pyquaternion
* sklearn
* dill
* gmplot
* nvector
* filterpy
* python-vlc

## Other Dependencies

* vlc
* SoX - http://sox.sourceforge.net 
* RTIMULib2 - https://github.com/jeff-loughlin/RTIMULib2
* SVOX PicoTTS - http://rpihome.blogspot.in/2015/02/installing-pico-tts.html

## Hardware Requirements

1. Raspberry Pi
2. GPS Module
3. Bluetooth Headset
4. Buzzer - pulseb.py (Pin numbers can be modified in this file)
5. Vibration - pulsev.py (Pin numbers can be modified in this file)
6. 9 axis IMU
7. 4x4 Keypad - input.py (Pin numbers can be modified in this file)
