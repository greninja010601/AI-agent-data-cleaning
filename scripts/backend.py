# backend.py
"""
FastAPI Backend for AI Data Cleaning
Provides REST API endpoints
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime
import io

# Import modules
from data_ingestion import DataIngestion
from data_cleaning import DataCleaning
from ai_agent import DataQualityAgent

load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="AI Data Cleaning API",
    description="AI-powered data cleaning and quality management system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
db_url = f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'student_data_db')}"
ingestion = DataIngestion(db_url=db_url) if os.getenv('DB_PASSWORD') else None
agent = DataQualityAgent(api_key=os.getenv("GOOGLE_API_KEY")) if os.getenv('GOOGLE_API_KEY') else None

# Create directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("cleaned", exist_ok=True)

# Pydantic models
class CleaningConfig(BaseModel):
    remove_duplicates: bool = True
    handle_missing: str = "fill_median"
    remove_outliers: bool = True
    standardize_text: bool = True

# ==================== Endpoints ====================

@app.get("/")
def read_root():
    """Health check"""
    return {
        "status": "healthy",
        "service": "AI Data Cleaning API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/upload/csv")
async def upload_csv(file: UploadFile = File(...)):
    """Upload CSV file"""
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"uploads/{timestamp}_{file.filename}"
        with open(filename, "wb") as f:
            f.write(contents)
        
        return JSONResponse(content={
            "status": "success",
            "message": "File uploaded successfully",
            "filepath": filename,
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "missing_values": df.isnull().sum().sum(),
            "duplicates": int(df.duplicated().sum())
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

@app.post("/clean/ai")
async def clean_with_ai(filepath: str):
    """Clean data using AI agent"""
    try:
        if not agent:
            raise HTTPException(status_code=503, detail="AI Agent not available - check GOOGLE_API_KEY")
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Load file
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filepath.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        original_shape = df.shape
        missing_before = int(df.isnull().sum().sum())
        
        # Clean with AI
        cleaned_df = agent.clean_data(df)
        
        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"cleaned/{timestamp}_ai_cleaned.csv"
        cleaned_df.to_csv(output_filename, index=False)
        
        return {
            "status": "success",
            "original_shape": original_shape,
            "cleaned_shape": cleaned_df.shape,
            "missing_before": missing_before,
            "missing_after": int(cleaned_df.isnull().sum().sum()),
            "download_url": f"/download/{output_filename}",
            "cleaned_file": output_filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/clean/traditional")
async def clean_traditional(filepath: str, config: Optional[CleaningConfig] = None):
    """Clean data using traditional methods"""
    try:
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="File not found")
        
        df = pd.read_csv(filepath) if filepath.endswith('.csv') else pd.read_excel(filepath)
        
        cleaner = DataCleaning(df)
        
        if config is None:
            config = CleaningConfig()
        
        if config.remove_duplicates:
            cleaner.remove_duplicates()
        if config.handle_missing:
            cleaner.handle_missing_values(strategy=config.handle_missing)
        if config.standardize_text:
            cleaner.remove_whitespace()
        if config.remove_outliers:
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
            if numeric_cols:
                cleaner.remove_outliers(numeric_cols)
        
        cleaned_df = cleaner.get_cleaned_data()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"cleaned/{timestamp}_traditional_cleaned.csv"
        cleaned_df.to_csv(output_filename, index=False)
        
        return {
            "status": "success",
            "summary": cleaner.get_cleaning_summary(),
            "download_url": f"/download/{output_filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/download/{filepath:path}")
async def download_file(filepath: str):
    """Download file"""
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=filepath,
        filename=os.path.basename(filepath),
        media_type='application/octet-stream'
    )

@app.get("/files/uploads")
def list_uploads():
    """List uploaded files"""
    files = []
    if os.path.exists("uploads"):
        for filename in os.listdir("uploads"):
            filepath = os.path.join("uploads", filename)
            files.append({
                "filename": filename,
                "filepath": filepath,
                "size": os.path.getsize(filepath)
            })
    return {"files": files}

@app.get("/files/cleaned")
def list_cleaned():
    """List cleaned files"""
    files = []
    if os.path.exists("cleaned"):
        for filename in os.listdir("cleaned"):
            filepath = os.path.join("cleaned", filename)
            files.append({
                "filename": filename,
                "filepath": filepath,
                "size": os.path.getsize(filepath)
            })
    return {"files": files}

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Starting AI Data Cleaning API Server")
    print("="*60)
    print("Server: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)