"""
Setup script for Interview Sathi backend.
Automates environment setup and dependency installation.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def check_python_version():
    """Check if Python version is 3.10+."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Python 3.10 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True

def create_env_file():
    """Create .env file from .env.example if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✓ .env file already exists")
        return True
    
    if not env_example.exists():
        print("❌ .env.example not found")
        return False
    
    # Copy .env.example to .env
    with open(env_example, 'r') as src:
        content = src.read()
    
    with open(env_file, 'w') as dst:
        dst.write(content)
    
    print("✓ Created .env file from .env.example")
    print("⚠️  Please edit .env and add your API keys!")
    return True

def install_dependencies():
    """Install Python dependencies."""
    print("Installing Python dependencies...")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True
        )
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_api_keys():
    """Check if API keys are configured."""
    from dotenv import load_dotenv
    load_dotenv()
    
    deepgram_key = os.getenv("DEEPGRAM_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    
    if not deepgram_key or deepgram_key == "your_deepgram_api_key_here":
        print("⚠️  DEEPGRAM_API_KEY not configured in .env")
        print("   Get your key from: https://deepgram.com")
        return False
    
    if not groq_key or groq_key == "your_groq_api_key_here":
        print("⚠️  GROQ_API_KEY not configured in .env")
        print("   Get your key from: https://groq.com")
        return False
    
    print("✓ API keys configured")
    return True

def main():
    """Main setup function."""
    print_header("Interview Sathi - Backend Setup")
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Create .env file
    if not create_env_file():
        return 1
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Check API keys
    api_keys_configured = check_api_keys()
    
    print_header("Setup Complete!")
    
    if api_keys_configured:
        print("✓ All checks passed!")
        print("\nYou can now run the backend:")
        print("  python main.py")
    else:
        print("⚠️  Setup complete, but API keys need configuration")
        print("\nNext steps:")
        print("  1. Edit .env file and add your API keys")
        print("  2. Run: python main.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
