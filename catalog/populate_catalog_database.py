from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, User, Category, Item

engine = create_engine('sqlite:///catalog.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


user1 = User(name="Roman Rodriguez", email="jose.roman.rodriguez@gmail.com")
session.add(user1)

user2 = User(name="John Wales", email="example@example.com")
session.add(user2)

category1 = Category(name="Soccer")
session.add(category1)

category2 = Category(name="Baseball")
session.add(category2)

category3 = Category(name="Football")
session.add(category3)

category4 = Category(name="Volleyball")
session.add(category4)

category5 = Category(name="Tennis")
session.add(category5)

item1 = Item(name="Bats", description="The best bat in the business.", user_id=1, category_id=2)
session.add(item1)

item2 = Item(name="Soccer Shoes", description="Great for sprinting and kicking.", user_id=1, category_id=1)
session.add(item2)

item3 = Item(name="Tobacco", description="Chew & chew.", user_id=2, category_id=3)
session.add(item3)

item4 = Item(name="Knee Pads", description="Don't hurt yourself in the court.", user_id=2, category_id=4)
session.add(item4)

item5 = Item(name="Tennis ball", description="Green and shiny.", user_id=1, category_id=5)
session.add(item5)

item6 = Item(name="Ball", description="Hard as a stone.", user_id=1, category_id=2)
session.add(item6)

item7 = Item(name="Goalkeeper pads", description="It hurts less.", user_id=1, category_id=1)
session.add(item7)

item8 = Item(name="Foot ball", description="Play with the best.", user_id=1, category_id=3)
session.add(item8)

item9 = Item(name="T-Shirt", description="USA team t-shirt.", user_id=2, category_id=4)
session.add(item9)

item10 = Item(name="Head band", description="Stop the sweat.", user_id=1, category_id=5)
session.add(item10)

session.commit()

print "added menu items!"