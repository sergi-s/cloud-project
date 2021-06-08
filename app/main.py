from models import db, UserFavs
from flask import Flask, request, render_template
import redis
import os

PEOPLE_FOLDER = os.path.join('static', 'imgs')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = PEOPLE_FOLDER

POSTGRES_USER = os.environ['POSTGRES_USER']
POSTGRES_PASSWORD = os.environ['POSTGRES_PASSWORD']
POSTGRES_DB = os.environ['POSTGRES_DB']
POSTGRES_HOST = os.environ['POSTGRES_HOST']
POSTGRES_PORT = os.environ['POSTGRES_PORT']

REDIS_HOST = os.environ['REDIS_HOST']
REDIS_PORT = os.environ['REDIS_PORT']

#! postgresql://username:password@host:port/database
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'


db.init_app(app)
with app.app_context():
    # To creates database with all the models defined in models.py
    # * m4 kol 4waya nb3at el context
    db.create_all()
    db.session.commit()

red = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)


@app.route("/")
def main():
    return render_template('index.html')


@app.route("/save", methods=['POST'])
def save():
    username = str(request.form['username']).lower()
    ID = str(request.form['ID']).lower()
    GPA = str(request.form['GPA']).lower()

    print("NAME", username)
    print("ID", ID)
    print("GPA", GPA)

    print(red.hgetall(ID))
    # return "Saved"
    # ? check if data of the username already exists in the redis
    if red.hgetall(ID).keys():
        print("hget ID:", red.hgetall(ID))
        # * return a msg to the template, saying the user already exists(from redis)
        return render_template('index.html', user_exists=1, msg='(From Redis)', ID=ID, username=red.hget(ID, "username").decode('utf-8'), GPA=red.hget(ID, "GPA").decode('utf-8'))

    # ? if not in redis, then check in db
    elif len(list(red.hgetall(ID))) == 0:
        record = UserFavs.query.filter_by(ID=ID).first()
        print("Records fecthed from db:", record)

        if record:
            red.hset(ID, "username", username)
            red.hset(ID, "GPA", GPA)
            # * return a msg to the template, saying the user already exists(from database)
            return render_template('index.html', user_exists=1, msg='(From DataBase)', ID=ID, username=record.username, GPA=record.GPA)

    # ?if data of the username doesnot exist anywhere, create a new record in DataBase and store in Redis also
    # ?create a new record in DataBase
    new_record = UserFavs(ID=ID, username=username, GPA=GPA)
    db.session.add(new_record)
    db.session.commit()

    # store in Redis also
    red.hset(ID, "username", username)
    red.hset(ID, "GPA", GPA)

    # cross-checking if the record insertion was successful into database
    record = UserFavs.query.filter_by(ID=ID).first()
    print("Records fetched from db after insert:", record)

    # cross-checking if the insertion was successful into redis
    print("key-values from redis after insert:", red.hgetall(ID))

    # return a success message upon saving
    return render_template('index.html', saved=1, ID=ID, username=red.hget(ID, "username").decode('utf-8'), GPA=red.hget(ID, "GPA").decode('utf-8'))


@app.route("/keys", methods=['GET'])
def keys():
    records = UserFavs.query.all()
    IDs = []
    imgs = []
    for record in records:
        img = os.path.join(app.config['UPLOAD_FOLDER'], 'sergi.png')
        # img = url_for('static', '/sergi.png')
        IDs.append((record.ID, record.username, record.GPA, img))
        # imgs.append(img)
    return render_template('index.html', keys=1, Students=IDs)


@app.route("/get", methods=['POST'])
def get():
    ID = request.form['ID']
    print("ID:", ID)
    user_data = red.hgetall(ID)
    print("GET Redis:", user_data)

    if not user_data:
        record = UserFavs.query.filter_by(ID=ID).first()
        print("GET Record:", record)
        if not record:
            print("No data in redis or db")
            return render_template('index.html', no_record=1, msg=f"Record not yet defined for {ID}")
        red.hset(ID, "place", record.username)
        red.hset(ID, "food", record.GPA)
        return render_template('index.html', get=1, msg="(From DataBase)", ID=ID, username=record.username, GPA=record.GPA)
    return render_template('index.html', get=1, msg="(From Redis)", ID=ID, usename=user_data[b'username'].decode('utf-8'), GPA=user_data[b'GPA'].decode('utf-8'))
