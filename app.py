from os import getenv, path
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, request
from flask_cors import CORS
from flask_mail import Mail, Message

load_dotenv(path.join(path.dirname(__file__), '.env'))

app = Flask(__name__)

app.config['CORS_ORIGINS'] = getenv('CORS_ORIGINS')
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = getenv('MAIL_USERNAME')


CORS(app)
mail = Mail(app)

def honeypot(f):
  @wraps(f)
  def decorated_function(*args, **kwargs):
    if request.is_json:
      if 'honeypot' in request.json:
        if request.json['honeypot'] is not None:
          if len(request.json['honeypot']) > 0:
            return {'status': 'error', 'message': 'Forbidden'}, 403
          return f(*args, **kwargs)
      return {'status': 'error', 'message': 'Missing field: honeypot'}, 400
    else:
      return {'status': 'error', 'message': 'Invalid Content-Type: JSON expected'}, 400
  return decorated_function

def validate(f):
  @wraps(f)
  def decorated_function(*args, **kwargs):
    if request.is_json:
      data = request.json
      fields = ['name', 'email', 'message']
      for field in fields:
        if field in data:
          if data[field] is not None:
            if len(data[field]) == 0:
              return {'status': 'error', 'message': f'Invalid data: {field} is empty'}, 400
            continue
        return {'status': 'error', 'message': f'Missing field: {field}'}, 400
      return f(*args, **kwargs)
    else:
      return {'status': 'error', 'message': 'Invalid Content-Type: JSON expected'}, 400
  return decorated_function

@app.post('/')
@honeypot
@validate
def contactme():
  data = request.json
  msg = Message(
    subject=f'New contact message from: {data["name"]}',
    recipients=[app.config['MAIL_USERNAME']],
    body='{name} sends you the next message:\n {message}\nReply to: {email}'.format(**data),
  )
  mail.send(msg)
  return {'status': 'success', 'message': 'Email sent successfully'}, 201