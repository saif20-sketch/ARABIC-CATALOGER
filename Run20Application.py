import subprocess
import sys

def run_streamlit():
    print("🚀 Starting Medical AI Librarian...")
    print("📚 Opening browser at http://localhost:8501")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n👋 Shutting down Medical AI Librarian...")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_streamlit()