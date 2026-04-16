
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import uuid
from typing import Dict, List
from datetime import datetime
import io
from PIL import Image

from backend.model_loader import DisasterModelLoader
from backend.video_processor import VideoProcessor
from batch_inference.alert_system import AlertSystem
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = FastAPI(title="Disaster Detection System")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
model_loader = DisasterModelLoader()
video_processor = VideoProcessor(model_loader)
alert_system = AlertSystem()

# In-memory storage
users_db: Dict[str, dict] = {}
sessions: Dict[str, str] = {}
processing_status: Dict[str, dict] = {}
video_results: Dict[str, dict] = {}

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/api/register")
async def register(user_data: dict):
    """Register a new user"""
    email = user_data.get("email")
    password = user_data.get("password")
    name = user_data.get("name", "User")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
    
    if email in users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    
    users_db[email] = {
        "email": email,
        "password": password,
        "name": name,
        "created_at": datetime.now().isoformat()
    }
    
    # Create session
    session_id = str(uuid.uuid4())
    sessions[session_id] = email
    
    return {
        "message": "Registration successful",
        "session_id": session_id,
        "user": {"email": email, "name": name}
    }


@app.post("/api/login")
async def login(credentials: dict):
    """Login user"""
    email = credentials.get("email")
    password = credentials.get("password")
    
    if email not in users_db:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if users_db[email]["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create session
    session_id = str(uuid.uuid4())
    sessions[session_id] = email
    
    return {
        "message": "Login successful",
        "session_id": session_id,
        "user": {"email": email, "name": users_db[email]["name"]}
    }


@app.post("/api/upload-media")
async def upload_media(files: List[UploadFile] = File(...), session_id: str = None):
    """Upload and process images or video"""
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    email = sessions[session_id]
    video_id = str(uuid.uuid4())
    
    processing_status[video_id] = {
        "status": "processing",
        "progress": 0,
        "total_frames": 0,
        "processed_frames": 0
    }
    
    # Check if first file is video or image
    is_video = files[0].content_type.startswith("video/")
    
    if is_video:
        # Save video and process (handle only first if video)
        file_path = os.path.join(UPLOAD_DIR, f"{video_id}.mp4")
        with open(file_path, "wb") as f:
            content = await files[0].read()
            f.write(content)
        import asyncio
        asyncio.create_task(process_video_async(video_id, file_path, email))
    else:
        # Process as batch of images
        import io
        from PIL import Image
        images = []
        for file in files:
            content = await file.read()
            images.append(Image.open(io.BytesIO(content)).convert("RGB"))
        
        import asyncio
        asyncio.create_task(process_images_async(video_id, images, email))
    
    return {
        "video_id": video_id,
        "message": f"{len(files)} file(s) uploaded. Processing started.",
        "status": "processing"
    }

# Keep original for backward compatibility
@app.post("/api/upload-video")
async def upload_video(file: UploadFile = File(...), session_id: str = None):
    return await upload_media([file], session_id)


def send_email(to_email: str, subject: str, body: str):
    sender_email = "satyamnaithani14@gmail.com"
    sender_password = "mrqb wgpz ushq cnhs" 

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"[EMAIL SENT] to {to_email}")
    except Exception as e:
        print(f"[EMAIL ERROR]: {e}")
    
async def process_video_async(video_id: str, file_path: str, user_email: str):
    """Process video asynchronously"""
    try:
        # Process video
        results = video_processor.process_video(
            file_path, 
            video_id,
            processing_status
        )
        
        # Detect alerts
        alerts = alert_system.detect_alerts(results["predictions"], video_id)
        
        # Store results
        video_results[video_id] = {
            "predictions": results["predictions"],
            "alerts": alerts,
            "user_email": user_email,
            "processed_at": datetime.now().isoformat()
        }
        
        processing_status[video_id]["status"] = "completed"
        
        # Simulate email notification for alerts
        # if alerts:
        #     print(f"[EMAIL SIMULATION] Sent alert to {user_email}")
        #     print(f"   Subject: Disaster Alert Detected!")
        #     print(f"   Alerts: {len(alerts)} disaster(s) detected in your video")
        
        if alerts:
            subject = "Disaster Alert"
            body = f"""
            ALERT: Potential Disaster Detected.

            A possible disaster event has been identified by the moinitoring system.
            Please stay alert and follow saftery guidlines.
        
            Please don't go near the following location.
            Location : ...

            The nearby authorities have been informed about thhis disaster. 
            Please Stay Safe ~ Team MitoWatts
            This is an automated alert from the Disaster Intelligence System. 
            
            """
            send_email(user_email, subject, body)

    except Exception as e:
        processing_status[video_id]["status"] = "failed"
        processing_status[video_id]["error"] = str(e)
        print(f"Error processing video: {e}")


async def process_images_async(video_id: str, images: List, user_email: str):
    """Process multiple images asynchronously"""
    try:
        # Process images
        results = video_processor.process_images(
            images, 
            video_id,
            processing_status
        )
        
        # Detect alerts
        alerts = alert_system.detect_alerts(results["predictions"], video_id)
        
        # Store results
        video_results[video_id] = {
            "predictions": results["predictions"],
            "alerts": alerts,
            "user_email": user_email,
            "processed_at": datetime.now().isoformat()
        }
        
        processing_status[video_id]["status"] = "completed"
        
        if alerts:
            subject = "Disaster Alert Detected in Batch!"
            body = f"""
            Alert detected in your uploaded image batch.

            Total alerts: {len(alerts)}

            Please check the system dashboard for details.
            """
            send_email(user_email, subject, body)
    except Exception as e:
        processing_status[video_id]["status"] = "failed"
        processing_status[video_id]["error"] = str(e)
        print(f"Error processing image batch: {e}")


@app.get("/api/process-status/{video_id}")
async def get_process_status(video_id: str):
    """Get processing status"""
    if video_id not in processing_status:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return processing_status[video_id]


@app.get("/api/predictions/{video_id}")
async def get_predictions(video_id: str):
    """Get frame-level predictions"""
    if video_id not in video_results:
        # Check if still processing
        if video_id in processing_status and processing_status[video_id]["status"] == "processing":
            return {"status": "processing", "predictions": []}
        raise HTTPException(status_code=404, detail="Results not found")
    
    return {
        "status": "completed",
        "predictions": video_results[video_id]["predictions"]
    }


@app.get("/api/alerts/{video_id}")
async def get_alerts(video_id: str):
    """Get detected alerts"""
    if video_id not in video_results:
        if video_id in processing_status and processing_status[video_id]["status"] == "processing":
            return {"status": "processing", "alerts": []}
        raise HTTPException(status_code=404, detail="Results not found")
    
    alerts = video_results[video_id]["alerts"]
    user_email = video_results[video_id]["user_email"]
    
    return {
        "status": "completed",
        "alerts": alerts,
        "email_sent": len(alerts) > 0,
        "notification_message": f"Alert notification send to {user_email}" if alerts else None
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model_loader.model is not None,
        "active_sessions": len(sessions)
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)






