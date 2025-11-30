# Data Acquisition – XIAO ESP32S3 (BeeGard Project)

## Description
This Arduino code allows the **XIAO ESP32S3** board to capture images using its built-in camera and automatically send them to **Edge Impulse** for machine learning model training or inference.

## How it works
1. Connects to a Wi-Fi network.
2. Initializes the camera with low resolution (160x120) to reduce image size.
3. In the main loop:
   - Captures an image (`camera_fb_t *fb = esp_camera_fb_get()`).
   - Sends the image to Edge Impulse via an HTTP POST request.
   - Frees memory of the captured image.
   - Resets the camera to avoid GDMA errors.
4. Repeats every 2 minutes (adjustable via `delay(120000)`).

## Libraries used
- `esp_camera.h` – for camera control.
- `WiFi.h` – for Wi-Fi connection.
- `HTTPClient.h` – for HTTP communication.

## Important notes
- Replace `EI_API_KEY`, `EI_DEVICE_ID`, and `EI_LABEL` with your Edge Impulse credentials.
- Camera reset is necessary after each capture.
- JPEG size is reduced to minimize latency and memory usage.

## Usage
1. Connect the XIAO ESP32S3 to your computer and upload the code via Arduino IDE.
2. Open Serial Monitor to follow Wi-Fi connection and image uploads.
3. Images will appear automatically in Edge Impulse for analysis and training.

