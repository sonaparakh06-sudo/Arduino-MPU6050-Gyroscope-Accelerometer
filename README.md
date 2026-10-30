Arduino MPU6050 Gyroscope and Accelerometer

 Project Overview

This project demonstrates interfacing the MPU6050 motion sensor with an Arduino to read accelerometer and gyroscope data along three axes (X, Y, and Z).

The sensor communicates with the Arduino through the I2C communication protocol. The collected raw sensor readings are displayed through the Serial Monitor and can also be viewed using the Arduino Serial Plotter.

This project helped me explore sensor interfacing, I2C communication, and basic embedded programming using Arduino.

 Objectives

- Interface the MPU6050 sensor with an Arduino.
- Read three-axis accelerometer and gyroscope measurements.
- Establish communication between the Arduino and MPU6050 using I2C.
- Display sensor readings through serial communication.
- Understand the basics of motion sensing and sensor data acquisition.

 Components and Tools

Hardware

- Arduino board
- MPU6050 accelerometer and gyroscope module
- Jumper wires

Software

- Arduino IDE
- MPU6050 library
- Wire library for I2C communication

 Working Principle

The MPU6050 is a six-axis motion sensor containing a three-axis accelerometer and a three-axis gyroscope.

- Accelerometer: Measures acceleration along the X, Y, and Z axes, including the effect of gravity.
- Gyroscope: Measures angular velocity around the X, Y, and Z axes.

The Arduino communicates with the sensor through I2C. The program initializes the sensor, checks whether the connection is successful, and continuously retrieves the six raw measurement values.

These readings are transmitted over the serial connection at a baud rate of 115200.

 Implementation

The program performs the following operations:

1. Initializes I2C communication.
2. Starts serial communication at 115200 baud.
3. Initializes the MPU6050 sensor.
4. Checks the sensor connection.
5. Reads accelerometer and gyroscope measurements along all three axes.
6. Prints the readings to the Serial Monitor in a format suitable for viewing in the Serial Plotter.

 Output

The program displays six raw sensor measurements:

- "ax", "ay", "az" — accelerometer readings along the X, Y, and Z axes.
- "gx", "gy", "gz" — gyroscope readings around the X, Y, and Z axes.

The readings change as the sensor moves or rotates.

Note: The program outputs raw sensor values rather than calibrated physical measurements.

 Libraries Used

- "Wire.h" — provides I2C communication functionality.
- "MPU6050.h" — provides functions to initialize the sensor and retrieve motion measurements.

The MPU6050 library used by this project must be installed in the Arduino IDE.
 
  Future Improvements

- Convert raw sensor readings into physical units.
- Implement calibration to reduce sensor offsets.
- Add motion or tilt detection based on sensor readings.
- Explore combining accelerometer and gyroscope data for improved orientation estimation.

 Key Learnings

- Interfacing sensors with Arduino.
- Understanding I2C communication.
- Reading accelerometer and gyroscope data.
- Using libraries to communicate with hardware.
- Displaying sensor measurements through serial communication.

