import RPi.GPIO as GPIO

# import the library
from RpiMotorLib import RpiMotorLib
    
#define GPIO pin
#GPIO_pins.cleanup()
GPIO_pins = (14, 15, 18) # Microstep Resolution MS1-MS3 -> GPIO Pin
motorXDirection= 16
motorXStep = 21      # Step -> GPIO Pin
#23,24 for the other motor.
motorYDirection = 23
motorYStep = 24

# Declare an named :wqinstance of class pass GPIO pins numbers
motorY = RpiMotorLib.A4988Nema(
        motorXDirection, motorXStep, GPIO_pins, "A4988")
motorX = RpiMotorLib.A4988Nema(motorYDirection, motorYStep, GPIO_pins, "A4988")


# call the function, pass the arguments
motorX.motor_go(1, "Full" , 100, .0007, False, .05)
#:wq
motorX.motor_go(0,"Full",100,0.0007,False,0.05)
motorY.motor_go(0, "Full",100,0.0007, False,0.05)
motorY.motor_go(1,"Full",100,0.0007,False,0.05)
# good practise to cleanup GPIO at some point before exit

#GPIO.cleanup()
