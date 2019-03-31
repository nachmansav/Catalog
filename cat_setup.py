from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
 
from database_setup import Base, Category
 
engine = create_engine('sqlite:///recipes.db')
Base.metadata.bind = engine
 
DBSession = sessionmaker(bind=engine)
session = DBSession()

#create the categories

appetizers = Category(name = "Appetizers")

session.add(appetizers)
session.commit()

salads = Category(name = "Salads")

session.add(salads)
session.commit()

side_dishes = Category(name = "Side Dishes")

session.add(side_dishes)
session.commit()

meat_poultry = Category(name = "Meat/Poultry")

session.add(meat_poultry)
session.commit()

dairy = Category(name = "Dairy")

session.add(dairy)
session.commit()

desserts = Category(name = "Desserts")

session.add(desserts)
session.commit()

print "Added recipe categories!"