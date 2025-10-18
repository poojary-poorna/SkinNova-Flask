#!/usr/bin/env python3

from app import app

if __name__ == '__main__':
    print("🌟 Starting SkinNova - Smart Beauty Assistant Platform")
    print("💄 Your makeup recommendation system is ready!")
    print("🔗 Open your browser and go to: http://localhost:5000")
    print("⭐ Create an account, take the quizzes, and get your personalized recommendations!")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)=`
    `