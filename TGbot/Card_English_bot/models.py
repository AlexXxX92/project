import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()



class Users(Base):
    __tablename__ = 'users'

    id_u = sq.Column(sq.Integer, primary_key=True)
    user = sq.Column(sq.BigInteger,  nullable=False)




class Words(Base):
    __tablename__ = 'words'
    id = sq.Column(sq.Integer, primary_key=True)
    words_eng = sq.Column(sq.String(length=60), nullable=False)
    translation = sq.Column(sq.String(length=100), nullable=False)


class UsersWords(Base):
    __tablename__ = 'userswords'
    id_user = sq.Column(sq.Integer, sq.ForeignKey('users.id_u'), primary_key=True)
    id_words = sq.Column(sq.Integer, sq.ForeignKey('words.id'), primary_key=True)

    user = relationship(Users, backref='users')
    word = relationship(Words, backref='words')

def create_tables(engine):
    Base.metadata.create_all(engine)

def drop_tables(engine):
    Base.metadata.drop_all(engine)

def words_add(session):
    words= {'She': 'Она',
         'He': 'Он',
         'Cat': 'Кошка',
         'Dog': 'Собака',
         'Teacher': 'Учитель',
         'Place': 'Место',
         'House': 'Дом',
         'Work': 'Работа',
         'Devise': 'Устройство',
         'Want': 'Хотеть'
         }
    for key, values in words.items():
        session.add(Words(words_eng=key, translation=values))
        session.commit()