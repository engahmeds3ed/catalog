from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
	__tablename__ = 'user'

	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=False)
	email = Column(String(250), nullable=False)
	picture = Column(String(250))


class Category(Base):
	__tablename__ = 'category'

	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=False)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)

	@property
	def serialize(self):
		"""Return object data in easily serializeable format"""
		return {
			'name': self.name,
			'id': self.id,
		}


class Item(Base):
	__tablename__ = 'items'

	id = Column(Integer, primary_key=True)
	name = Column(String(80), nullable=False)
	description = Column(String(250))
	created = Column(DateTime, nullable=False)
	picture = Column(String(250))
	category_id = Column(Integer, ForeignKey('category.id'))
	category = relationship(Category, backref=backref('items', cascade='all, delete'))
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)

	@property
	def serialize(self):
		"""Return object data in easily serializeable format"""
		return {
			'name': self.name,
			'description': self.description,
			'id': self.id,
			'picture': self.picture,
			'category': self.category.serialize,
		}

engine = create_engine('postgresql+psycopg2://catalog:catalog@localhost/catalog')
Base.metadata.create_all(engine)