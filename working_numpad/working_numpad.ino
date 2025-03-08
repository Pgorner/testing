#include <WiFi.h>
#include <HTTPClient.h>
#include <Arduino_GFX_Library.h>

// WiFi Credentials
const char *ssid = "Tech";
const char *password = "R8gmjM8#Asw&";

// Flask video stream URL
const char *videoStreamURL = "http://192.168.50.181:5000/video_feed";

// Display & SD Card Pin Configuration
#define SPI_MISO 42
#define SPI_MOSI 2
#define SPI_SCLK 1

#define LCD_CS 39
#define LCD_DC 41
#define LCD_RST 40
#define LCD_BL 6

#define LCD_WIDTH  320
#define LCD_HEIGHT 240
#define FRAME_SIZE (LCD_WIDTH * LCD_HEIGHT * 2)  // RGB565 requires 2 bytes per pixel

// Initialize SPI display
Arduino_DataBus *bus = new Arduino_ESP32SPI(LCD_DC, LCD_CS, SPI_SCLK, SPI_MOSI, SPI_MISO, FSPI);
Arduino_ST7789 *gfx = new Arduino_ST7789(bus, LCD_RST, 0, false, LCD_WIDTH, LCD_HEIGHT, 16);

void connectWiFi() {
    Serial.print("🔄 Connecting to WiFi... ");
    WiFi.begin(ssid, password);

    int attempt = 0;
    while (WiFi.status() != WL_CONNECTED && attempt < 10) {  // Reduce retries
        delay(500);
        Serial.print(".");
        attempt++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n✅ WiFi Connected!");
    } else {
        Serial.println("\n❌ WiFi Connection Failed! Restarting...");
        ESP.restart();  // Restart ESP if WiFi fails
    }
}

void setup() {
    Serial.begin(115200);
    connectWiFi();

    // Initialize display
    if (!gfx->begin()) {
        Serial.println("❌ Display init failed!");
        while (1);
    }

    pinMode(LCD_BL, OUTPUT);
    digitalWrite(LCD_BL, HIGH);
    gfx->fillScreen(BLACK);
    
    Serial.println("✅ Display initialized!");
}

void fetchFrame() {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("⚠️ WiFi Disconnected. Attempting Reconnect...");
        connectWiFi();
        return;
    }

    WiFiClient client;
    HTTPClient http;

    Serial.println("🔄 Requesting frame...");
    http.begin(client, videoStreamURL);
    int httpCode = http.GET();

    if (httpCode != HTTP_CODE_OK) {
        Serial.printf("❌ Failed to get frame. HTTP Code: %d\n", httpCode);
        http.end();
        return;
    }

    Serial.println("✅ Frame received! Processing...");

    uint8_t *frameBuffer = (uint8_t *)heap_caps_malloc(FRAME_SIZE, MALLOC_CAP_SPIRAM);
    if (!frameBuffer) {
        Serial.println("❌ Memory allocation failed!");
        http.end();
        return;
    }

    int bytesRead = 0;
    int totalBytes = FRAME_SIZE;

    WiFiClient *stream = http.getStreamPtr();
    while (stream->available() && bytesRead < totalBytes) {
        bytesRead += stream->readBytes(frameBuffer + bytesRead, totalBytes - bytesRead);
    }

    if (bytesRead == totalBytes) {
        Serial.printf("✅ Frame received (%d bytes), displaying...\n", bytesRead);
        gfx->draw16bitRGBBitmap(0, 0, (uint16_t *)frameBuffer, LCD_WIDTH, LCD_HEIGHT);
    } else {
        Serial.printf("❌ Incomplete frame received! (%d / %d bytes)\n", bytesRead, totalBytes);
    }

    free(frameBuffer);  // Free memory
    http.end();
}

void loop() {
    fetchFrame();
    delay(33);  // Maintain ~30 FPS
}
