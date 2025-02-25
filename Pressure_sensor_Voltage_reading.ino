#include <Wire.h>
#include "DFRobot_RGBLCD1602.h"

#define SENSOR_PIN A0  // Analog input pin
#define SAMPLE_INTERVAL 100  // Time between readings (ms)
#define AVERAGE_DURATION 10000  // Total averaging time taken per output (ms)

DFRobot_RGBLCD1602 lcd(/*RGBAddr*/0x6B ,/*lcdCols*/16,/*lcdRows*/2);  //16 characters and 2 lines of show

void setup() {
    Serial.begin(9600);
    while (!Serial);
    Serial.println("Arduino Mega is running...");
    lcd.init();  
    //lcd.backlight();
    lcd.setCursor(0, 0);
    lcd.print("Pressure Monitor");
}
void loop(){
    float sumVoltage = 0.0;
    int sampleCount = 0;
    int serialno=1;
    unsigned long startTime = millis();

    while (millis() - startTime < AVERAGE_DURATION) {
        int rawValue = analogRead(SENSOR_PIN);
        float voltage = (rawValue / 1023.0) * 5.0;
        sumVoltage += voltage;
        sampleCount++;

        delay(SAMPLE_INTERVAL);
    }

    float averageVoltage = sumVoltage / sampleCount;
    //Serial.print("Average Voltage (last 5s): ");
    //Serial.print(averageVoltage);
    //Serial.println(" V");
    float pressure = (averageVoltage-0.48)*0.981/0.0565 + 1013;//standard pressure=1013mbar at 2.52V, every additional 1cm of water increases pressure by 0.0292mbar, and 1cm water equals 0.981mbar pressure
    //Serial.print("Average pressure value: ");
    Serial.println(pressure);
    //Serial.println("mbar/hPa");
    //updating LCD display
    lcd.clear();
    lcd.setCursor(1, 1);
    lcd.print(pressure);
    lcd.print(" mbar");
    lcd.setCursor(1,0);
    lcd.print(averageVoltage);
    lcd.print("V");
}
