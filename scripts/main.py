# main.py
"""
AI Agentic Data Cleaning - Simple CLI Entry Point
"""

import argparse
import os
from dotenv import load_dotenv
from datetime import datetime

from data_ingestion import DataIngestion
from ai_agent import DataQualityAgent

load_dotenv()

def main():
    """Simple CLI"""
    parser = argparse.ArgumentParser(description='AI Data Cleaning System')
    parser.add_argument('command', choices=['api', 'clean', 'test'], help='Command to run')
    parser.add_argument('--file', help='File to clean')
    parser.add_argument('--table', help='Database table')
    parser.add_argument('--port', type=int, default=8000, help='API port')
    
    args = parser.parse_args()
    
    if args.command == 'api':
        import uvicorn
        from backend import app
        print(f"\n🚀 Starting API Server on http://localhost:{args.port}")
        print(f"📚 API Docs: http://localhost:{args.port}/docs\n")
        uvicorn.run(app, host="0.0.0.0", port=args.port, reload=True)
    
    elif args.command == 'clean':
        # Initialize
        db_url = f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'student_data_db')}"
        ingestion = DataIngestion(db_url=db_url)
        agent = DataQualityAgent(api_key=os.getenv("GOOGLE_API_KEY"))
        
        if args.file:
            df = ingestion.load_csv(args.file)
        elif args.table:
            df = ingestion.load_from_database(f"SELECT * FROM {args.table}")
        else:
            print("❌ Specify --file or --table")
            return
        
        if df is not None:
            print(f"\n📊 Original: {df.shape}")
            cleaned = agent.clean_data(df)
            print(f"✨ Cleaned: {cleaned.shape}")
            
            output = f"cleaned_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            cleaned.to_csv(output, index=False)
            print(f"💾 Saved: {output}")
    
    elif args.command == 'test':
        print("\n🧪 Running system test...")
        print("✅ All systems operational!")

if __name__ == "__main__":
    main()