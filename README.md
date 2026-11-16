
# VITALWATCH
### Patient Vitals Monitoring and Early-Alert System

## 1. Project Overview
VitalWatch is a web-based healthcare monitoring
system that records patient vital signs and
identifies abnormal readings.

## 2. Technologies Used
- Python
- Flask
- SQLite
- HTML
- CSS

## 3. Core Features
1. Patient registration and vitals recording.
2. Automatic abnormal-value alerts.
3. Trend detection using the last 3 readings.
4. Active patient alert dashboard.
5. Printable ward shift handover report.

## 4. Additional Features
- Simple early-warning score.
- Patient risk indicators.
- Vital signs graphs.
- Patient search.
- Alert history.
- Escalation notifications.

## 5. Installation

Install dependencies:

python -m pip install -r requirements.txt

## 6. Run the Application

python app.py

Open in browser:

http://127.0.0.1:5000

## 7. Database
SQLite automatically creates vitalwatch.db
to store patient details and vital readings.

## 8. Safety Note
This is an educational prototype.
Its thresholds and scoring are not clinically
validated and must not be used for real
patient-care decisions.
