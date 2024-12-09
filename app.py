
import cv2
import base64
import time
import logging
import numpy as np
import os

from apps import create_app, socketio, db
from apps.models import ExpresionData, PoseData
from ultralytics import YOLO
from flask import request, jsonify, json
from tf_keras.models import load_model
from dotenv import load_dotenv
# from twilio.rest import Client

# Constants
SEQUENCE_LENGTH = 15
NUM_KEYPOINTS = 17
frame_buffer = []
frame_count = 0
emotion_scores = {
    'marah': 0,
    'sedih': 0,
    'cemas': 0
}

THRESHOLD = 5

app = create_app()

if os.getenv("FLASK_ENV") != "migration":
    expression_model = YOLO("ekspresi_ncnn_model")
    pose_model = YOLO("pose_ncnn_model/yolov8l-pose.pt")

    load_pose_model = load_model("pose_ncnn_model/runs/model.h5")

    # Load classes from classes.json
    with open('pose_ncnn_model/runs/classes.json', 'r') as f:
        pose_classes = json.load(f)

    latest_expression_frame = None
    latest_pose_frame = None
    latest_raw_expression_frame = None
    latest_raw_pose_frame = None

def process_pose_frame(frame, keypoints):
    frame_data = []
    if keypoints.shape[1] > 0:  # Check if keypoints are detected
        for kp in keypoints[0]:
            frame_data.extend([kp[0], kp[1]])
    else:
        # If no keypoints detected, fill with zeros
        frame_data = [0] * (NUM_KEYPOINTS * 2)
    return frame_data

# Function to draw skeleton
def draw_skeleton(img, keypoints, bounding_box, confidence_threshold=0.5):
    x_min, y_min, x_max, y_max = bounding_box
    
    # Define the pairs of keypoints that should be connected
    skeleton = [
        (0, 1), (0, 2), (1, 3), (2, 4),  # Head
        (5, 6), (5, 11), (6, 12),  # Body
        (11, 12),  # Hip
        (5, 7), (7, 9), (6, 8), (8, 10),  # Arms
        (11, 13), (13, 15), (12, 14), (14, 16)  # Legs
    ]

    # Check if keypoints have confidence scores
    has_confidence = keypoints.shape[1] == 3

    def is_within_box(pt, x_min, y_min, x_max, y_max):
        return x_min <= pt[0] <= x_max and y_min <= pt[1] <= y_max

    for pair in skeleton:
        pt1 = (int(keypoints[pair[0], 0] * img.shape[1]), int(keypoints[pair[0], 1] * img.shape[0]))
        pt2 = (int(keypoints[pair[1], 0] * img.shape[1]), int(keypoints[pair[1], 1] * img.shape[0]))

        if has_confidence:
            if keypoints[pair[0], 2] > confidence_threshold and keypoints[pair[1], 2] > confidence_threshold:
                if is_within_box(pt1, x_min, y_min, x_max, y_max) and is_within_box(pt2, x_min, y_min, x_max, y_max):
                    cv2.line(img, pt1, pt2, (0, 255, 0), 2)
        else:
            if is_within_box(pt1, x_min, y_min, x_max, y_max) and is_within_box(pt2, x_min, y_min, x_max, y_max):
                cv2.line(img, pt1, pt2, (0, 255, 0), 2)

    # Draw keypoints
    for i in range(keypoints.shape[0]):
        pt = (int(keypoints[i, 0] * img.shape[1]), int(keypoints[i, 1] * img.shape[0]))
        if has_confidence:
            if keypoints[i, 2] > confidence_threshold and is_within_box(pt, x_min, y_min, x_max, y_max):
                cv2.circle(img, pt, 4, (0, 0, 255), -1)
        else:
            if is_within_box(pt, x_min, y_min, x_max, y_max):
                cv2.circle(img, pt, 4, (0, 0, 255), -1)

    return img

def process_image(image_data, model_type):
    global latest_expression_frame, latest_pose_frame
    global latest_raw_expression_frame, latest_raw_pose_frame
    global frame_buffer, frame_count
    global emotion_scores

    try:
        # Decode the base64 image data
        image_data = base64.b64decode(image_data)
        np_arr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        frame_count += 1
        # Save the raw frame for both expression and pose
        _, buffer = cv2.imencode('.jpg', frame)
        latest_raw_expression_frame = base64.b64encode(buffer).decode('utf-8')
        latest_raw_pose_frame = base64.b64encode(buffer).decode('utf-8')

        if model_type == 'expression':
            # Expression detection
            expression_frame = frame.copy()
            expression_results = expression_model(expression_frame)

            if expression_results and len(expression_results) > 0:
                for r in expression_results:
                    boxes = r.boxes
                    if boxes is not None and len(boxes) > 0:
                        for box in boxes:
                            b = box.xyxy[0].cpu().numpy().astype(int)
                            cls = int(box.cls[0])
                            conf = float(box.conf[0])
                            label = f"{r.names[cls]} {conf:.2f}"
                            cv2.rectangle(expression_frame, (b[0], b[1]), (b[2], b[3]), (0, 255, 0), 2)
                            cv2.putText(expression_frame, label, (b[0], b[1] - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                             # Track emotion scores
                            if r.names[cls] in ['marah', 'sedih', 'cemas']:
                                emotion_scores[r.names[cls]] += 1

                            # # Check if emotion score reaches the threshold
                            # if emotion_scores['marah'] >= THRESHOLD or emotion_scores['sedih'] >= THRESHOLD or emotion_scores['cemas'] >= THRESHOLD:
                            #     send_whatsapp_notification()

                            # Save expression data to database
                            with app.app_context():
                                data_expression = ExpresionData(
                                    timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                                    expresion=r.names[cls],
                                    confidence=conf
                                )
                                try:
                                    db.session.add(data_expression)
                                    db.session.commit()
                                except Exception as e:
                                    db.session.rollback()
                                    logging.error(f"Database error: {str(e)}")

                # Save the processed expression frame
                _, buffer = cv2.imencode('.jpg', expression_frame)
                latest_expression_frame = base64.b64encode(buffer).decode('utf-8')
            else:
                latest_expression_frame = None

        elif model_type == 'pose':
            # Pose detection
            pose_frame = frame.copy()
            pose_results = pose_model(pose_frame, verbose=False)

            if pose_results and len(pose_results) > 0:
                for r in pose_results:
                    if r.keypoints is not None:
                        keypoints = r.keypoints.xyn.cpu().numpy()

                        # Process frame data for movement classification
                        frame_data = process_pose_frame(pose_frame, keypoints)
                        frame_buffer.append(frame_data)
                        
                        # If we have enough frames, make a movement prediction
                        if len(frame_buffer) >= SEQUENCE_LENGTH:
                            sequence = np.array(frame_buffer, dtype=np.float32)
                            sequence = np.expand_dims(sequence, axis=0)  # Add batch dimension
                            prediction = load_pose_model.predict(sequence)
                            predicted_movement = pose_classes[np.argmax(prediction)]
                            movement_confidence = np.max(prediction)

                            # Menggambar bounding box dan label di frame
                            boxes = r.boxes.xyxy.cpu().numpy()
                            for box in boxes:
                                cv2.rectangle(pose_frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 255, 0), 2)
                                cv2.putText(pose_frame, f"Movement: {predicted_movement}: {movement_confidence:.2f}", 
                                            (int(box[0]), int(box[1])-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                                # Menggambar skeleton dan keypoints di pose_frame
                                if keypoints.shape[1] > 0:
                                    pose_frame = draw_skeleton(pose_frame, keypoints[0], (int(box[0]), int(box[1]), int(box[2]), int(box[3])))

                            # Hapus frame tertua jika sudah mencapai batas
                            if len(frame_buffer) > SEQUENCE_LENGTH:
                                frame_buffer.pop(0)

                            # Simpan data pose ke database
                            with app.app_context():
                                data_pose = PoseData(
                                    timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                                    pose=predicted_movement,
                                    confidence=float(movement_confidence)
                                )
                                try:
                                    db.session.add(data_pose)
                                    db.session.commit()
                                except Exception as e:
                                    db.session.rollback()
                                    logging.error(f"Database error: {str(e)}")

                # Save the processed pose frame
                _, buffer = cv2.imencode('.jpg', pose_frame)
                latest_pose_frame = base64.b64encode(buffer).decode('utf-8')
            else:
                latest_pose_frame = None

    except Exception as e:
        logging.error(f"Error in process_image: {str(e)}")

@app.route('/process_image_expression', methods=['POST'])
def process_image_expression_route():
    data = request.json
    image_data = data['image'].split(',')[1]
    process_image(image_data, 'expression')

    socketio.emit('expression_frame', {'expression_image': latest_expression_frame})
    socketio.emit('raw_expression', {'raw_expression': latest_raw_expression_frame})

    return jsonify({
        'expression_image': 'data:image/jpeg;base64,' + latest_expression_frame,
        'raw_expression': latest_raw_expression_frame,
    })

@app.route('/process_image_pose', methods=['POST'])
def process_image_pose_route():
    data = request.json
    image_data = data['image'].split(',')[1]
    process_image(image_data, 'pose')

    
    socketio.emit('pose_frame', {'pose_image': latest_pose_frame})
    socketio.emit('raw_pose', {'raw_pose': latest_raw_pose_frame})

    return jsonify({
        'pose_image': 'data:image/jpeg;base64,' + latest_pose_frame,
    })

def send_frame():
    global latest_expression_frame
    global latest_pose_frame
    global latest_raw_expression_frame
    global latest_raw_pose_frame

    while True:
        if latest_raw_expression_frame is not None:
            socketio.emit('raw_expression', {
                'raw_expression': latest_raw_expression_frame
            })
            print(f"Sending raw frame data: {latest_raw_expression_frame[:10]}")  # Example: print first 10 chars of frame
        
        if latest_raw_pose_frame is not None:
            socketio.emit('raw_pose', {
                'raw_pose': latest_raw_pose_frame
            })
            print(f"Sending raw frame data: {latest_raw_expression_frame[:10]}")  # Example: print first 10 chars of frame
        
        if latest_expression_frame is not None:
            socketio.emit('expression_frame', {
                'expression_image': latest_expression_frame
            })
            print(f"Sending expression frame data: {latest_expression_frame[:10]}")  # Example: print first 10 chars of frame

        if latest_pose_frame is not None:
            socketio.emit('pose_frame', {
                'pose_image': latest_pose_frame
            })
            print("Sending pose frame data")

        socketio.sleep(0.1)

#Bot Whatsapp

# def send_whatsapp_notification():
#     load_dotenv()
#     account_sid = os.getenv('TWILIO_SID')
#     auth_token = os.getenv('TWILIO_AUTH')
#     client = Client(account_sid, auth_token)

#     try:
#         message = client.messages.create(
#             from_=os.getenv('WA_TWILIO'),
#             body='''EMOKIDS NOTIFICATION

#             Siswa Terdeteksi Mengalami Emosi Tidak Stabil (Marah/Sedih/Cemas).

#             Website: https://emokids.site''',
#             to=os.getenv('WA_TO')  # Ganti nomor dengan nomor tujuan
#         )
#         print(f"WhatsApp notification sent: {message.sid}")

#         # Reset emotion scores after sending notification
#         emotion_scores['marah'] = 0
#         emotion_scores['sedih'] = 0
#         emotion_scores['cemas'] = 0

#     except Exception as e:
#         logging.error(f"Error sending WhatsApp notification: {str(e)}")

if __name__ == '__main__':

    try:
        socketio.start_background_task(send_frame)
        socketio.run(app, debug=True)
    except Exception as e:
        logging.error(f"Error starting the application: {str(e)}")
