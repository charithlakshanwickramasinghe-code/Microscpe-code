#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>

// =====================================================
// ESP32-S3 CONFOCAL SCANNER
//
// X axis = Motor 1
// Y axis = Motor 2
// Z axis = Motor 3
//
// DRV8825 = 1/32 microstepping
// NEMA17   = 200 full steps/revolution
//
// 200 x 32 = 6400 microsteps/revolution
//
// Lead screw = 8 mm/revolution
//
// 6400 / 8 = 800 microsteps/mm
//
// Examples:
// 8  microsteps = 10 um
// 16 microsteps = 20 um
// 32 microsteps = 40 um
// 64 microsteps = 80 um
//
// CJMCU-101 analog output = GPIO 3
// =====================================================


// =====================================================
// WIFI SETTINGS
// =====================================================

// CHANGE THESE

const char* WIFI_SSID =
  "Charith's iPhone";

const char* WIFI_PASSWORD =
  "1234567890";


// =====================================================
// PUBLIC MQTT BROKER
// =====================================================

const char* MQTT_SERVER =
  "broker.hivemq.com";

const int MQTT_PORT = 1883;


// =====================================================
// MQTT TOPICS
//
// Use a unique topic name because this is a
// PUBLIC MQTT broker.
// =====================================================

const char* MQTT_TOPIC_DATA =
  "dulip-confocal-7f3a9c/scan/data";

const char* MQTT_TOPIC_STATUS =
  "dulip-confocal-7f3a9c/scan/status";


// =====================================================
// WIFI + MQTT OBJECTS
// =====================================================

WiFiClient wifiClient;

PubSubClient mqttClient(wifiClient);


// =====================================================
// PIN MAP
// =====================================================

// ---------------- X AXIS ----------------

#define EN_X   4
#define DIR_X  5
#define STP_X  6


// ---------------- Y AXIS ----------------

#define EN_Y   15
#define DIR_Y  16
#define STP_Y  17


// ---------------- Z AXIS ----------------

#define EN_Z   40
#define DIR_Z  41
#define STP_Z  42


// ---------------- LIGHT SENSOR ----------------

#define LIGHT_SENSOR_PIN 3


// =====================================================
// MECHANICAL SETTINGS
// =====================================================

const int MICROSTEPS_PER_REV = 6400;

const float LEAD_SCREW_MM_PER_REV = 8.0;

// 6400 / 8 = 800 microsteps/mm

const int MICROSTEPS_PER_MM = 800;


// =====================================================
// MOTOR SPEED
// =====================================================

const int STEP_DELAY_US = 2000;


// =====================================================
// SENSOR SETTINGS
// =====================================================

const int SETTLE_TIME_MS = 100;

const int SENSOR_SAMPLES = 20;


// =====================================================
// Z DIRECTION
// =====================================================

enum ZDirection
{
  Z_UP,
  Z_DOWN
};


// =====================================================
// WIFI CONNECTION
// =====================================================

void connectWiFi()
{
  if (WiFi.status() == WL_CONNECTED)
  {
    return;
  }

  Serial.println();
  Serial.print("Connecting to WiFi");

  WiFi.mode(WIFI_STA);

  WiFi.begin(
    WIFI_SSID,
    WIFI_PASSWORD
  );

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);

    Serial.print(".");
  }

  Serial.println();

  Serial.println("WiFi connected");

  Serial.print("ESP32 IP: ");

  Serial.println(
    WiFi.localIP()
  );
}


// =====================================================
// MQTT CONNECTION
// =====================================================

void connectMQTT()
{
  while (!mqttClient.connected())
  {
    Serial.print(
      "Connecting to public MQTT broker..."
    );

    char clientID[50];

    uint64_t chipID =
      ESP.getEfuseMac();

    snprintf(
      clientID,
      sizeof(clientID),
      "ESP32S3-Confocal-%08X",
      (uint32_t)chipID
    );


    if (
      mqttClient.connect(clientID)
    )
    {
      Serial.println(" connected!");

      mqttClient.publish(
        MQTT_TOPIC_STATUS,
        "scanner_connected"
      );
    }

    else
    {
      Serial.print(
        " failed. MQTT state = "
      );

      Serial.println(
        mqttClient.state()
      );

      delay(2000);
    }
  }
}


// =====================================================
// ENSURE INTERNET + MQTT CONNECTION
// =====================================================

void ensureConnections()
{
  if (
    WiFi.status() != WL_CONNECTED
  )
  {
    connectWiFi();
  }

  if (
    !mqttClient.connected()
  )
  {
    connectMQTT();
  }

  mqttClient.loop();
}


// =====================================================
// PUBLISH STATUS
// =====================================================

void publishStatus(
  const char* message
)
{
  ensureConnections();

  mqttClient.publish(
    MQTT_TOPIC_STATUS,
    message
  );

  mqttClient.loop();
}


// =====================================================
// PUBLISH ONE SCAN POINT
// =====================================================

void publishScanPoint(
  int zLevel,
  long zMicrosteps,
  int row,
  int column,
  float xMM,
  float yMM,
  int intensity
)
{
  ensureConnections();


  char payload[256];


  snprintf(
    payload,
    sizeof(payload),

    "{"
    "\"z_level\":%d,"
    "\"z_microsteps\":%ld,"
    "\"row\":%d,"
    "\"column\":%d,"
    "\"x_mm\":%.4f,"
    "\"y_mm\":%.4f,"
    "\"intensity\":%d"
    "}",

    zLevel,
    zMicrosteps,
    row,
    column,
    xMM,
    yMM,
    intensity
  );


  mqttClient.publish(
    MQTT_TOPIC_DATA,
    payload
  );


  mqttClient.loop();
}


// =====================================================
// ONE MICROSTEP
// =====================================================

void oneStep(int stepPin)
{
  digitalWrite(
    stepPin,
    HIGH
  );

  delayMicroseconds(
    STEP_DELAY_US
  );


  digitalWrite(
    stepPin,
    LOW
  );

  delayMicroseconds(
    STEP_DELAY_US
  );
}


// =====================================================
// X AXIS
// =====================================================

void moveXPlusOneStep()
{
  digitalWrite(
    DIR_X,
    HIGH
  );

  delayMicroseconds(5);

  oneStep(STP_X);
}


void moveXMinusOneStep()
{
  digitalWrite(
    DIR_X,
    LOW
  );

  delayMicroseconds(5);

  oneStep(STP_X);
}


// =====================================================
// Y AXIS
// =====================================================

void moveYPlusOneStep()
{
  digitalWrite(
    DIR_Y,
    HIGH
  );

  delayMicroseconds(5);

  oneStep(STP_Y);
}


void moveYMinusOneStep()
{
  digitalWrite(
    DIR_Y,
    LOW
  );

  delayMicroseconds(5);

  oneStep(STP_Y);
}


// =====================================================
// Z AXIS
// =====================================================

void moveZPlusOneStep()
{
  digitalWrite(
    DIR_Z,
    HIGH
  );

  delayMicroseconds(5);

  oneStep(STP_Z);
}


void moveZMinusOneStep()
{
  digitalWrite(
    DIR_Z,
    LOW
  );

  delayMicroseconds(5);

  oneStep(STP_Z);
}


// =====================================================
// X MULTIPLE MICROSTEPS
// =====================================================

void moveXPlus(uint32_t steps)
{
  for (
    uint32_t i = 0;
    i < steps;
    i++
  )
  {
    moveXPlusOneStep();
  }
}


void moveXMinus(uint32_t steps)
{
  for (
    uint32_t i = 0;
    i < steps;
    i++
  )
  {
    moveXMinusOneStep();
  }
}


// =====================================================
// Y MULTIPLE MICROSTEPS
// =====================================================

void moveYPlus(uint32_t steps)
{
  for (
    uint32_t i = 0;
    i < steps;
    i++
  )
  {
    moveYPlusOneStep();
  }
}


void moveYMinus(uint32_t steps)
{
  for (
    uint32_t i = 0;
    i < steps;
    i++
  )
  {
    moveYMinusOneStep();
  }
}


// =====================================================
// Z MULTIPLE MICROSTEPS
// =====================================================

void moveZPlus(uint32_t steps)
{
  for (
    uint32_t i = 0;
    i < steps;
    i++
  )
  {
    moveZPlusOneStep();
  }
}


void moveZMinus(uint32_t steps)
{
  for (
    uint32_t i = 0;
    i < steps;
    i++
  )
  {
    moveZMinusOneStep();
  }
}


// =====================================================
// LIGHT INTENSITY
// =====================================================

int getLightIntensity()
{
  uint32_t total = 0;


  for (
    int i = 0;
    i < SENSOR_SAMPLES;
    i++
  )
  {
    total += analogRead(
      LIGHT_SENSOR_PIN
    );

    delayMicroseconds(200);
  }


  return (
    total / SENSOR_SAMPLES
  );
}


// =====================================================
// OUTPUT + PUBLISH ONE POINT
// =====================================================

void processScanPoint(
  int zLevel,
  long zMicrosteps,
  int row,
  int column,
  float xMM,
  float yMM
)
{
  // Allow mechanical vibration to settle

  delay(
    SETTLE_TIME_MS
  );


  // Get averaged light intensity

  int intensity =
    getLightIntensity();


  // ---------------------------------------------------
  // SERIAL OUTPUT
  // ---------------------------------------------------

  Serial.print(zLevel);
  Serial.print(",");

  Serial.print(zMicrosteps);
  Serial.print(",");

  Serial.print(row);
  Serial.print(",");

  Serial.print(column);
  Serial.print(",");

  Serial.print(xMM, 4);
  Serial.print(",");

  Serial.print(yMM, 4);
  Serial.print(",");

  Serial.println(intensity);


  // ---------------------------------------------------
  // MQTT OUTPUT
  // ---------------------------------------------------

  publishScanPoint(
    zLevel,
    zMicrosteps,
    row,
    column,
    xMM,
    yMM,
    intensity
  );
}


// =====================================================
// SCAN ONE XY PLANE
//
// widthMM
// lengthMM
// xyStepMicrosteps
// zLevel
// zPositionMicrosteps
//
// Initial XY position is treated as CENTER.
//
// After scanning:
//
// X returns to center
// Y returns to center
// =====================================================

void scanArea(
  float widthMM,
  float lengthMM,
  uint32_t xyStepMicrosteps,
  int zLevel,
  long zPositionMicrosteps
)
{
  // ===================================================
  // VALIDATION
  // ===================================================

  if (
    widthMM <= 0 ||
    lengthMM <= 0
  )
  {
    Serial.println(
      "ERROR: Invalid XY size"
    );

    return;
  }


  if (
    xyStepMicrosteps == 0
  )
  {
    Serial.println(
      "ERROR: XY step cannot be zero"
    );

    return;
  }


  // ===================================================
  // XY STEP IN MILLIMETERS
  // ===================================================

  float xyStepMM =
    (float)xyStepMicrosteps /
    MICROSTEPS_PER_MM;


  // ===================================================
  // NUMBER OF SCAN INTERVALS
  // ===================================================

  int xIntervals =
    lroundf(
      (
        widthMM *
        MICROSTEPS_PER_MM
      )
      /
      xyStepMicrosteps
    );


  int yIntervals =
    lroundf(
      (
        lengthMM *
        MICROSTEPS_PER_MM
      )
      /
      xyStepMicrosteps
    );


  if (
    xIntervals < 1
  )
  {
    xIntervals = 1;
  }


  if (
    yIntervals < 1
  )
  {
    yIntervals = 1;
  }


  // ===================================================
  // TOTAL MICROSTEPS
  // ===================================================

  uint32_t totalXSteps =
    (uint32_t)xIntervals *
    xyStepMicrosteps;


  uint32_t totalYSteps =
    (uint32_t)yIntervals *
    xyStepMicrosteps;


  // ===================================================
  // CENTER OFFSETS
  // ===================================================

  uint32_t xNegativeOffset =
    totalXSteps / 2;


  uint32_t xPositiveOffset =
    totalXSteps -
    xNegativeOffset;


  uint32_t yNegativeOffset =
    totalYSteps / 2;


  uint32_t yPositiveOffset =
    totalYSteps -
    yNegativeOffset;


  // ===================================================
  // NUMBER OF POINTS
  // ===================================================

  int xPoints =
    xIntervals + 1;


  int yPoints =
    yIntervals + 1;


  // ===================================================
  // INFORMATION
  // ===================================================

  Serial.println();

  Serial.print(
    "Scanning Z level "
  );

  Serial.println(zLevel);


  Serial.print(
    "XY step = "
  );

  Serial.print(
    xyStepMicrosteps
  );

  Serial.print(
    " microsteps = "
  );

  Serial.print(
    xyStepMM * 1000.0
  );

  Serial.println(" um");


  Serial.print(
    "X points = "
  );

  Serial.println(xPoints);


  Serial.print(
    "Y points = "
  );

  Serial.println(yPoints);


  // ===================================================
  // MOVE CENTER → BOTTOM LEFT
  // ===================================================

  moveXMinus(
    xNegativeOffset
  );


  moveYMinus(
    yNegativeOffset
  );


  // ===================================================
  // SERPENTINE SCAN
  // ===================================================

  for (
    int row = 0;
    row < yPoints;
    row++
  )
  {
    float yPosition =
      (
        -(float)yNegativeOffset
        +
        (
          (float)row *
          xyStepMicrosteps
        )
      )
      /
      MICROSTEPS_PER_MM;


    // =================================================
    // EVEN ROW
    //
    // LEFT → RIGHT
    // =================================================

    if (
      (row % 2) == 0
    )
    {
      // First point

      float xPosition =
        -(float)xNegativeOffset
        /
        MICROSTEPS_PER_MM;


      processScanPoint(
        zLevel,
        zPositionMicrosteps,
        row,
        0,
        xPosition,
        yPosition
      );


      // Remaining points

      for (
        int col = 1;
        col < xPoints;
        col++
      )
      {
        moveXPlus(
          xyStepMicrosteps
        );


        xPosition =
          (
            -(float)xNegativeOffset
            +
            (
              (float)col *
              xyStepMicrosteps
            )
          )
          /
          MICROSTEPS_PER_MM;


        processScanPoint(
          zLevel,
          zPositionMicrosteps,
          row,
          col,
          xPosition,
          yPosition
        );
      }
    }


    // =================================================
    // ODD ROW
    //
    // RIGHT → LEFT
    // =================================================

    else
    {
      int col =
        xPoints - 1;


      float xPosition =
        (float)xPositiveOffset
        /
        MICROSTEPS_PER_MM;


      processScanPoint(
        zLevel,
        zPositionMicrosteps,
        row,
        col,
        xPosition,
        yPosition
      );


      for (
        col = xPoints - 2;
        col >= 0;
        col--
      )
      {
        moveXMinus(
          xyStepMicrosteps
        );


        xPosition =
          (
            -(float)xNegativeOffset
            +
            (
              (float)col *
              xyStepMicrosteps
            )
          )
          /
          MICROSTEPS_PER_MM;


        processScanPoint(
          zLevel,
          zPositionMicrosteps,
          row,
          col,
          xPosition,
          yPosition
        );
      }
    }


    // =================================================
    // NEXT Y ROW
    // =================================================

    if (
      row <
      yPoints - 1
    )
    {
      moveYPlus(
        xyStepMicrosteps
      );
    }
  }


  // ===================================================
  // RETURN Y TO CENTER
  // ===================================================

  moveYMinus(
    yPositiveOffset
  );


  // ===================================================
  // RETURN X TO CENTER
  // ===================================================

  int lastRow =
    yPoints - 1;


  if (
    (lastRow % 2) == 0
  )
  {
    // Ended at +X

    moveXMinus(
      xPositiveOffset
    );
  }

  else
  {
    // Ended at -X

    moveXPlus(
      xNegativeOffset
    );
  }


  Serial.print(
    "Z level "
  );

  Serial.print(zLevel);

  Serial.println(
    " complete"
  );


  Serial.println(
    "XY returned to center"
  );
}


// =====================================================
// 3D / MULTI-Z SCAN
//
// PARAMETERS:
//
// widthMM
// lengthMM
// xyStepMicrosteps
// zStepMicrosteps
// zLevels
// zDirection
//
// After complete scan:
//
// X = original center
// Y = original center
// Z = original position
// =====================================================

void scanVolume(
  float widthMM,
  float lengthMM,
  uint32_t xyStepMicrosteps,
  uint32_t zStepMicrosteps,
  int zLevels,
  ZDirection zDirection
)
{
  // ===================================================
  // VALIDATE
  // ===================================================

  if (
    widthMM <= 0 ||
    lengthMM <= 0
  )
  {
    Serial.println(
      "ERROR: Invalid XY scan area"
    );

    return;
  }


  if (
    xyStepMicrosteps == 0
  )
  {
    Serial.println(
      "ERROR: Invalid XY step"
    );

    return;
  }


  if (
    zStepMicrosteps == 0
  )
  {
    Serial.println(
      "ERROR: Invalid Z step"
    );

    return;
  }


  if (
    zLevels <= 0
  )
  {
    Serial.println(
      "ERROR: Invalid Z levels"
    );

    return;
  }


  // ===================================================
  // MAKE SURE MQTT IS CONNECTED
  // ===================================================

  ensureConnections();


  // ===================================================
  // START INFORMATION
  // ===================================================

  Serial.println();

  Serial.println(
    "===================================="
  );

  Serial.println(
    "3D CONFOCAL SCAN START"
  );

  Serial.println(
    "===================================="
  );


  Serial.print(
    "X width = "
  );

  Serial.print(widthMM);

  Serial.println(" mm");


  Serial.print(
    "Y length = "
  );

  Serial.print(lengthMM);

  Serial.println(" mm");


  Serial.print(
    "XY step = "
  );

  Serial.print(
    xyStepMicrosteps
  );

  Serial.print(
    " microsteps = "
  );

  Serial.print(
    (
      (float)xyStepMicrosteps /
      MICROSTEPS_PER_MM
    )
    * 1000.0
  );

  Serial.println(" um");


  Serial.print(
    "Z step = "
  );

  Serial.print(
    zStepMicrosteps
  );

  Serial.println(
    " microsteps"
  );


  Serial.print(
    "Z levels = "
  );

  Serial.println(
    zLevels
  );


  Serial.print(
    "Z direction = "
  );


  if (
    zDirection == Z_UP
  )
  {
    Serial.println("UP");
  }

  else
  {
    Serial.println("DOWN");
  }


  // ===================================================
  // CSV HEADER
  // ===================================================

  Serial.println();

  Serial.println(
    "z_level,z_microsteps,row,column,x_mm,y_mm,intensity"
  );


  // ===================================================
  // MQTT START MESSAGE
  // ===================================================

  publishStatus(
    "scan_started"
  );


  long currentZPosition = 0;


  // ===================================================
  // Z LEVEL LOOP
  // ===================================================

  for (
    int level = 0;
    level < zLevels;
    level++
  )
  {
    // -------------------------------------------------
    // Z level status
    // -------------------------------------------------

    char statusMessage[64];

    snprintf(
      statusMessage,
      sizeof(statusMessage),
      "z_level_%d_started",
      level
    );


    publishStatus(
      statusMessage
    );


    // =================================================
    // SCAN XY AT THIS Z
    // =================================================

    scanArea(
      widthMM,
      lengthMM,
      xyStepMicrosteps,
      level,
      currentZPosition
    );


    snprintf(
      statusMessage,
      sizeof(statusMessage),
      "z_level_%d_complete",
      level
    );


    publishStatus(
      statusMessage
    );


    // =================================================
    // NEXT Z LEVEL
    // =================================================

    if (
      level <
      zLevels - 1
    )
    {
      if (
        zDirection ==
        Z_UP
      )
      {
        moveZPlus(
          zStepMicrosteps
        );


        currentZPosition +=
          zStepMicrosteps;
      }

      else
      {
        moveZMinus(
          zStepMicrosteps
        );


        currentZPosition -=
          zStepMicrosteps;
      }


      // Z settling delay

      delay(100);
    }
  }


  // ===================================================
  // RETURN Z TO ORIGINAL POSITION
  // ===================================================

  Serial.println();

  Serial.println(
    "Returning Z to original position..."
  );


  if (
    currentZPosition > 0
  )
  {
    moveZMinus(
      (uint32_t)
      currentZPosition
    );
  }

  else if (
    currentZPosition < 0
  )
  {
    moveZPlus(
      (uint32_t)
      (-currentZPosition)
    );
  }


  currentZPosition = 0;


  // ===================================================
  // COMPLETE
  // ===================================================

  publishStatus(
    "scan_complete"
  );


  Serial.println();

  Serial.println(
    "===================================="
  );

  Serial.println(
    "3D SCAN COMPLETE"
  );

  Serial.println(
    "X = ORIGINAL CENTER"
  );

  Serial.println(
    "Y = ORIGINAL CENTER"
  );

  Serial.println(
    "Z = ORIGINAL POSITION"
  );

  Serial.println(
    "===================================="
  );
}


// =====================================================
// SETUP
// =====================================================

void setup()
{
  // ===================================================
  // SERIAL
  // ===================================================

  Serial.begin(115200);

  delay(2000);


  // ===================================================
  // X
  // ===================================================

  pinMode(
    EN_X,
    OUTPUT
  );

  pinMode(
    DIR_X,
    OUTPUT
  );

  pinMode(
    STP_X,
    OUTPUT
  );


  // ===================================================
  // Y
  // ===================================================

  pinMode(
    EN_Y,
    OUTPUT
  );

  pinMode(
    DIR_Y,
    OUTPUT
  );

  pinMode(
    STP_Y,
    OUTPUT
  );


  // ===================================================
  // Z
  // ===================================================

  pinMode(
    EN_Z,
    OUTPUT
  );

  pinMode(
    DIR_Z,
    OUTPUT
  );

  pinMode(
    STP_Z,
    OUTPUT
  );


  // ===================================================
  // CJMCU-101
  // ===================================================

  pinMode(
    LIGHT_SENSOR_PIN,
    INPUT
  );

  analogReadResolution(12);


  // ===================================================
  // ENABLE ALL DRV8825
  //
  // EN LOW = enabled
  // ===================================================

  digitalWrite(
    EN_X,
    LOW
  );

  digitalWrite(
    EN_Y,
    LOW
  );

  digitalWrite(
    EN_Z,
    LOW
  );


  digitalWrite(
    STP_X,
    LOW
  );

  digitalWrite(
    STP_Y,
    LOW
  );

  digitalWrite(
    STP_Z,
    LOW
  );


  // ===================================================
  // WIFI
  // ===================================================

  connectWiFi();


  // ===================================================
  // PUBLIC MQTT BROKER
  // ===================================================

  mqttClient.setServer(
    MQTT_SERVER,
    MQTT_PORT
  );


  mqttClient.setBufferSize(
    512
  );


  mqttClient.setKeepAlive(
    60
  );


  connectMQTT();


  Serial.println();

  Serial.println(
    "Confocal Scanner Ready"
  );


  Serial.print(
    "MQTT data topic: "
  );

  Serial.println(
    MQTT_TOPIC_DATA
  );
}


// =====================================================
// LOOP
// =====================================================

void loop()
{
  // ===================================================
  // SCAN SETTINGS
  //
  // scanVolume(
  //
  //   X width mm,
  //   Y length mm,
  //   XY step microsteps,
  //   Z step microsteps,
  //   Z levels,
  //   Z direction
  //
  // );
  // ===================================================


  scanVolume(

    2,     // X width = 10 mm

    2,     // Y length = 10 mm

    32,       // XY step = 40 um

    32,       // Z step = 32 microsteps

    1,        // 5 Z levels

    Z_UP      // Z_UP or Z_DOWN

  );


  // ===================================================
  // STOP AFTER SCAN
  // ===================================================

  while (true)
  {
    mqttClient.loop();

    delay(10);
  }
}