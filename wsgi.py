from waitress import serve
from main import main_app

if __name__ == '__main__':
    serve(main_app, host='0.0.0.0', port=5000)
