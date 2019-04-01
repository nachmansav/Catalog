#!/usr/bin/env python3

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
import random
import string
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

Base = declarative_base()

# Use this secret key to create and verify tokens
secret_key = ''.join(random.choice(
    string.ascii_uppercase + string.digits) for x in xrange(32))


# The Username table.
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(32))
    picture = Column(String)
    email = Column(String, index=True)
    recipes = relationship('Recipe', backref='creator')

    def generate_auth_token(self, expiration=6000):
        s = Serializer(secret_key, expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(secret_key)
        try:
            data = s.loads(token)
        except SignatureExpired:
            # valid Token, but expired
            return None
        except BadSignature:
            # Invalid Token
            return None
        user_id = data['id']
        return user_id


# The Category table.
class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    picture = Column(String)
    recipes = relationship('Recipe', backref='category')
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            'picture': self.picture
            }


# The recipe table.
class Recipe(Base):
    __tablename__ = 'recipe'
    id = Column(Integer, primary_key=True)
    creator_id = Column(String, ForeignKey('user.id'))
    name = Column(String)
    cat_id = Column(String, ForeignKey('category.id'))
    ingredients = Column(String)
    directions = Column(String)
    picture = Column(String)
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'picture': self.picture,
            'creator': self.creator.username,
            'creator_picture': self.creator.picture,
            'name': self.name,
            'cat_id': self.cat_id,
            'ingredients': self.ingredients,
            'directions': self.directions,
            }


engine = create_engine('sqlite:///recipes.db')
Base.metadata.create_all(engine)
