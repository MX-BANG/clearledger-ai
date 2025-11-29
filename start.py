"""
Easy Startup Script
Runs both backend and frontend simultaneously
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def check_env_file():
    """Check if .env file exists"""
    if not Path('.env').exists():
        print("❌ .env file not found!")
        print("\n📝 Please create .env file:")
        print("1. Copy .env.example to .env")
        print("2. Add your Gemini API key")
        print("\nGet API key from: https://makersuite.google.com/app/apikey")
        sys.exit(1)
    
    # Check if API key is set
    with open('.env', 'r') as f:
        content = f.read()
        if 'your_gemini_api_key_here' in content or 'GEMINI_API_KEY=' not in content:
            print("⚠️ Warning: Gemini API key not configured in .env file!")
            print("Get your free API key from: https://makersuite.google.com/app/apikey")
            proceed = input("\nDo you want to continue anyway? (y/N): ")
            if proceed.lower() != 'y':
                sys.exit(1)

def create_directories():
    """Create necessary directories"""
    dirs = [
        'data/uploads',
        'data/processed', 
        'data/exports',
        'database'
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created")

def start_backend():
    """Start FastAPI backend"""
    print("\n🚀 Starting Backend (FastAPI)...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return backend_process

def start_frontend():
    """Start Streamlit frontend"""
    print("🎨 Starting Frontend (Streamlit)...")
    frontend_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "frontend/app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return frontend_process

def main():
    print("="*60)
    print("🤖 AI Bookkeeping Cleanup Engine")
    print("="*60)
    
    # Check environment
    print("\n🔍 Checking environment...")
    check_env_file()
    create_directories()
    
    print("\n✅ Environment check complete!")
    print("\n" + "="*60)
    print("Starting servers...")
    print("="*60)
    
    # Start backend
    backend = start_backend()
    
    # Wait for backend to start
    print("\n⏳ Waiting for backend to initialize (5 seconds)...")
    time.sleep(5)
    
    # Start frontend
    frontend = start_frontend()
    
    # Wait for frontend to start
    print("⏳ Waiting for frontend to initialize (3 seconds)...")
    time.sleep(3)
    
    print("\n" + "="*60)
    print("✅ APPLICATION STARTED SUCCESSFULLY!")
    print("="*60)
    
    print("\n🌐 Access the application at:")
    print("   Frontend: http://localhost:8501")
    print("   Backend API: http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    
    print("\n💡 Tips:")
    print("   - Frontend opens automatically in browser")
    print("   - Press Ctrl+C to stop both servers")
    print("   - Check terminal for any errors")
    
    print("\n" + "="*60)
    print("Servers are running... (Press Ctrl+C to stop)")
    print("="*60)
    
    # Open browser
    try:
        webbrowser.open('http://localhost:8501')
    except:
        pass
    
    # Keep running
    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        backend.terminate()
        frontend.terminate()
        print("✅ Servers stopped successfully!")
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\n💡 Try running servers manually:")
        print("   Terminal 1: uvicorn backend.main:app --reload")
        print("   Terminal 2: streamlit run frontend/app.py")
        sys.exit(1)