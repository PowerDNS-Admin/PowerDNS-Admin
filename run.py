#!flask/bin/python
from app import app
from config import PORT

if __name__ == '__main__':
    app.run(debug = True, port=PORT)
