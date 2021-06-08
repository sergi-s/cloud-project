from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class UserFavs(db.Model):
    username = db.Column(db.String)
    ID = db.Column(db.Integer, primary_key=True)
    GPA = db.Column(db.Float)

    def __init__(self, username, ID, GPA):
        self.username = username
        self.ID = ID
        self.GPA = GPA

    def __repr__(self):
        return f'<Student-ID-GPA : {self.username}-{self.ID}-{self.GPA}'
