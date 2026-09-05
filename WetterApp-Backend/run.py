import os
from dotenv import load_dotenv
from app import create_app

load_dotenv()

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    
    app.run(debug=True, port=port)