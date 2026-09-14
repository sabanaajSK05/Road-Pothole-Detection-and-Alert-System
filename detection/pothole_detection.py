import cv2
import serial
import time
import smtplib
from email.mime.text import MIMEText
from ultralytics import YOLO


# =========================================================
# CONFIGURATION
# =========================================================

# YOLO model
MODEL_PATH = "best.pt"

# ESP32 serial port
# Change COM port according to your computer
SERIAL_PORT = "COM3"

# GPS baud rate
GPS_BAUD_RATE = 115200

# Email configuration
SENDER_EMAIL = "your_email@gmail.com"
APP_PASSWORD = "your_app_password"
AUTHORITY_EMAIL = "authority_email@gmail.com"

# Confidence threshold
CONFIDENCE_THRESHOLD = 0.50

# Prevent repeated emails for the same detection
EMAIL_COOLDOWN = 30


# =========================================================
# LOAD YOLO MODEL
# =========================================================

print("Loading YOLO model...")

model = YOLO(MODEL_PATH)

print("YOLO model loaded successfully.")


# =========================================================
# CONNECT TO ESP32
# =========================================================

print("Connecting to ESP32...")

try:
    gps_serial = serial.Serial(
        SERIAL_PORT,
        GPS_BAUD_RATE,
        timeout=1
    )

    print("ESP32 connected successfully.")

except Exception as e:
    print("Could not connect to ESP32.")
    print("Error:", e)
    gps_serial = None


# =========================================================
# FUNCTION: READ GPS
# =========================================================

def get_gps_location():

    if gps_serial is None:
        return None, None

    latitude = None
    longitude = None

    start_time = time.time()

    while time.time() - start_time < 5:

        try:
            line = gps_serial.readline().decode(
                "utf-8",
                errors="ignore"
            ).strip()

            # ESP32 sends:
            # Latitude: xx.xxxxxx
            # Longitude: xx.xxxxxx

            if line.startswith("Latitude:"):
                latitude = float(
                    line.replace("Latitude:", "").strip()
                )

            elif line.startswith("Longitude:"):
                longitude = float(
                    line.replace("Longitude:", "").strip()
                )

            if latitude is not None and longitude is not None:
                return latitude, longitude

        except Exception:
            continue

    return None, None


# =========================================================
# FUNCTION: SEND EMAIL
# =========================================================

def send_email(latitude, longitude):

    subject = "Pothole Detected - Road Monitoring System"

    message = f"""
POTHOLE DETECTED

A pothole has been detected by the Smart Pothole Detection
and Alert System.

Location:

Latitude: {latitude}
Longitude: {longitude}

Google Maps:
https://www.google.com/maps?q={latitude},{longitude}

Please inspect the location and take the necessary action.

Regards,
Smart Pothole Detection System
"""

    email = MIMEText(message)

    email["Subject"] = subject
    email["From"] = SENDER_EMAIL
    email["To"] = AUTHORITY_EMAIL

    try:

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465
        ) as server:

            server.login(
                SENDER_EMAIL,
                APP_PASSWORD
            )

            server.sendmail(
                SENDER_EMAIL,
                AUTHORITY_EMAIL,
                email.as_string()
            )

        print("Email alert sent successfully.")

    except Exception as e:

        print("Email could not be sent.")
        print("Error:", e)


# =========================================================
# OPEN CAMERA
# =========================================================

print("Opening camera...")

cap = cv2.VideoCapture(0)

if not cap.isOpened():

    print("Camera could not be opened.")
    exit()

print("Camera started successfully.")
print("Press Q to quit.")


# =========================================================
# MAIN LOOP
# =========================================================

last_email_time = 0

while True:

    # Capture frame
    ret, frame = cap.read()

    if not ret:

        print("Could not read camera frame.")
        break


    # -----------------------------------------------------
    # YOLO DETECTION
    # -----------------------------------------------------

    results = model(frame)


    # Get first result
    result = results[0]


    # Draw bounding boxes
    annotated_frame = result.plot()


    # -----------------------------------------------------
    # CHECK FOR POTHOLE
    # -----------------------------------------------------

    pothole_detected = False

    for box in result.boxes:

        confidence = float(box.conf[0])

        if confidence >= CONFIDENCE_THRESHOLD:

            pothole_detected = True

            print(
                f"Pothole detected "
                f"(Confidence: {confidence:.2f})"
            )


    # -----------------------------------------------------
    # GPS + EMAIL
    # -----------------------------------------------------

    current_time = time.time()

    if pothole_detected:

        # Avoid sending continuous emails
        if current_time - last_email_time >= EMAIL_COOLDOWN:

            print("Reading GPS location...")

            latitude, longitude = get_gps_location()


            if latitude is not None and longitude is not None:

                print("GPS Location:")
                print("Latitude:", latitude)
                print("Longitude:", longitude)

                # Send alert
                send_email(
                    latitude,
                    longitude
                )

                last_email_time = current_time

            else:

                print(
                    "GPS location not available."
                )


    # -----------------------------------------------------
    # DISPLAY RESULT
    # -----------------------------------------------------

    cv2.imshow(
        "Smart Pothole Detection",
        annotated_frame
    )


    # Press Q to exit
    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


# =========================================================
# CLEANUP
# =========================================================

cap.release()

cv2.destroyAllWindows()

if gps_serial is not None:
    gps_serial.close()

print("System stopped.")
