/*
  ESP32 gate scanner: reads QR from a handheld USB/UART scanner
  and posts check-in to KISANQ /api/iot/scan
*/
#include <WiFi.h>
#include <HTTPClient.h>

const char* WIFI_SSID = "MANDI_WIFI";
const char* WIFI_PASS = "change-me";
const char* API_URL = "http://10.0.0.5:8000/api/iot/scan";
const int CENTRE_ID = 1;
const char* DEVICE_ID = "esp32-gate-1";

String buffer;

void setup() {
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, 16, 17);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) delay(400);
}

void loop() {
  while (Serial2.available()) {
    char c = Serial2.read();
    if (c == '\n' || c == '\r') {
      buffer.trim();
      if (buffer.length() > 4) postScan(buffer);
      buffer = "";
    } else {
      buffer += c;
    }
  }
}

void postScan(String qr) {
  if (WiFi.status() != WL_CONNECTED) return;
  HTTPClient http;
  http.begin(API_URL);
  http.addHeader("Content-Type", "application/json");
  String body = "{\"qr_code\":\"" + qr + "\",\"centre_id\":" + String(CENTRE_ID) +
                ",\"device_id\":\"" + String(DEVICE_ID) + "\"}";
  int code = http.POST(body);
  Serial.printf("scan %s -> %d\n", qr.c_str(), code);
  http.end();
}
