from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime
from database_setup import Category, Base, Item, User

engine = create_engine('postgresql+psycopg2://catalog:catalog@localhost/catalog')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy users
User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

User2 = User(name="Ahmed Saed", email="asa@udacity.com",
             picture='http://dummyimage.com/400x400.png/ff4444/ffffff')
session.add(User2)
session.commit()

#categories
category1 = Category(user_id=1, name="Category 1")

session.add(category1)
session.commit()

category2 = Category(user_id=1, name="Category 2")

session.add(category2)
session.commit()

category3 = Category(user_id=1, name="Category 3")

session.add(category3)
session.commit()

category4 = Category(user_id=1, name="Category 4")

session.add(category4)
session.commit()

#Category Items
Item1 = Item(name="Item 1",
               created=datetime.datetime.now(),
               description="Item 1 description here.",
               picture="https://dummyimage.com/400x400.png/ffff44/000000",
               category_id=1,
               user_id=1)
session.add(Item1)
session.commit()

Item2 = Item(name="Item 2",
               created=datetime.datetime.now(),
               description="Item 2 description here.",
               picture="https://dummyimage.com/400x400.png/000000/ffffff",
               category_id=2,
               user_id=1)
session.add(Item2)
session.commit()

Item3 = Item(name="Item 3",
               created=datetime.datetime.now(),
               description="Item 3 description here.",
               picture="https://dummyimage.com/400x400.png/000000/ffff44",
               category_id=3,
               user_id=2)
session.add(Item3)
session.commit()

Item4 = Item(name="Item 4",
               created=datetime.datetime.now(),
               description="Item 4 description here.",
               picture="https://dummyimage.com/400x400.png/efefef/000000",
               category_id=4,
               user_id=2)
session.add(Item4)
session.commit()


print "added initial dummy data!"
