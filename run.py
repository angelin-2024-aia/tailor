#!/usr/bin/env python
"""
TailorPro - Tailor Shop Management System
A complete Flask-based application for managing tailor shops.
"""

import sys
import subprocess

def run_app():
    """Start the Flask development server"""
    print("=" * 60)
    print("🧵  TailorPro - Tailor Shop Management System")
    print("=" * 60)
    print("\n📱 Starting application...\n")
    
    try:
        # Import and run the app
        from app import app, init_db
        
        # Initialize database
        init_db()
        print("✓ Database initialized successfully")
        
        # Start the development server
        print("✓ Starting Flask development server...")
        print("\n🌐 Application running at: http://127.0.0.1:5000")
        print("📖 Press Ctrl+C to stop the server\n")
        
        app.run(debug=True, host='127.0.0.1', port=5000)
        
    except Exception as e:
        print(f"\n❌ Error starting application:")
        print(f"   {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Ensure Python 3.8+ is installed")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Check if port 5000 is available")
        sys.exit(1)

if __name__ == "__main__":
    run_app()
