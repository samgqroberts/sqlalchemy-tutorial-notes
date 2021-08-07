print('\n -- Connecting -- \n')

from sqlalchemy import create_engine
engine = create_engine('sqlite:///:memory:', echo=True)

print('\n -- Declare a Mapping -- \n')

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from sqlalchemy import Column, Integer, String
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    fullname = Column(String)
    nickname = Column(String)

    def __repr__(self):
        return "<User(name='%s', fullname='%s', nickname='%s')>" % (
            self.name, self.fullname, self.nickname
        )

print('\n -- Create a Schema -- \n')

print(User.__table__)

Base.metadata.create_all(engine)

print('\n -- Create an Instance of the Mapped Class -- \n')
ed_user = User(name='ed', fullname='Ed Jones', nickname='edsnickname')
print(ed_user.name)
print(ed_user.nickname)
print(ed_user.id)

print('\n -- Creating a Session -- \n')

from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
session = Session()

print('\n -- Adding and Updating Objects -- \n')

session.add(ed_user)

our_user = session.query(User).filter_by(name='ed').first()
print(our_user)

print(ed_user is our_user)

session.add_all([
    User(name='wendy', fullname='Wendy Williams', nickname='windy'),
    User(name='mary', fullname='Mary Contrary', nickname='mary'),
    User(name='fred', fullname='Fred Flintstone', nickname='freddy'),
])

ed_user.nickname = 'eddie'

print(session.dirty)

print(session.new)

session.commit()

print(ed_user.id)

print('\n -- Rolling Back -- \n')

ed_user.name = 'Edwardo'

fake_user = User(name='fakeuser', fullname='Invalid', nickname='12345')
session.add(fake_user)

print(session.query(User).filter(User.name.in_(['Edwardo', 'fakeuser'])).all())

session.rollback()
print(ed_user.name)
print(fake_user in session)

print('\n -- Querying -- \n')

for instance in session.query(User).order_by(User.id):
    print(instance.name, instance.fullname)

for name, fullname in session.query(User.name, User.fullname):
    print(name, fullname)

for row in session.query(User, User.name).all():
    print(row.User, row.name)

for row in session.query(User.name.label('name_label')).all():
    print(row.name_label)

from sqlalchemy.orm import aliased
user_alias = aliased(User, name='user_alias')
for row in session.query(user_alias, user_alias.name).all():
    print(row.user_alias)

for u in session.query(User).order_by(User.id)[1:3]:
    print(u)

for name, in session.query(User.name).filter_by(fullname='Ed Jones'):
    print(name)

for name, in session.query(User.name).filter(User.fullname=='Ed Jones'):
    print(name)

for user in session.query(User).\
        filter(User.name=='ed').\
        filter(User.fullname=='Ed Jones'):
    print(user)
