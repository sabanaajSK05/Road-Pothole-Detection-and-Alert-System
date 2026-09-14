#include <TinyGPS++.h>

// GPS object
TinyGPSPlus gps;

// Use UART2 of ESP32
HardwareSerial GPSserial(2);

// ESP32 pins
#define GPS_RX 16
#define GPS_TX 17

void setup()
{
  // Serial Monitor
  Serial.begin(115200);

  // GPS communication
  GPSserial.begin(9600, SERIAL_8N1, GPS_RX, GPS_TX);

  Serial.println("================================");
  Serial.println("ESP32 GPS Module Started");
  Serial.println("Waiting for GPS signal...");
  Serial.println("================================");
}

void loop()
{
  // Read data coming from GPS
  while (GPSserial.available() > 0)
  {
    if (gps.encode(GPSserial.read()))
    {
      if (gps.location.isValid())
      {
        Serial.print("Latitude: ");
        Serial.println(gps.location.lat(), 6);

        Serial.print("Longitude: ");
        Serial.println(gps.location.lng(), 6);

        Serial.println("-----------------------------");
      }
      else
      {
        Serial.println("Waiting for valid GPS location...");
      }
    }
  }

  // Check if GPS is not sending data
  if (millis() > 5000 && gps.charsProcessed() < 10)
  {
    Serial.println("GPS not detected. Check wiring.");
    delay(1000);
  }
}
