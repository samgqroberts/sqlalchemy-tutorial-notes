print("\n -- Connecting -- \n")

from sqlalchemy import create_engine
from sqlalchemy.sql.elements import literal

engine = create_engine("sqlite:///:memory:", echo=True)

print("\n -- Defined and Create Tables -- \n")

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey

metadata = MetaData()
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String),
    Column("fullname", String),
)
addresses = Table(
    "addresses",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", None, ForeignKey("users.id")),
    Column("email_address", String, nullable=False),
)
metadata.create_all(engine)

print("\n -- Insert Expressions -- \n")

ins = users.insert()
print(str(ins))

ins = users.insert().values(name="jack", fullname="Jack Jones")
print(str(ins))
print(ins.compile().params)

print("\n -- Executing -- \n")

conn = engine.connect()
print(conn)

result = conn.execute(ins)

ins.bind = engine
print(str(ins))

print(result.inserted_primary_key)

print("\n -- Executing Multiple Statements -- \n")

ins = users.insert()
conn.execute(ins, id=2, name="wendy", fullname="Wendy Williams")

conn.execute(
    addresses.insert(),
    [
        {"user_id": 1, "email_address": "jack@yahoo.com"},
        {"user_id": 1, "email_address": "jack@msn.com"},
        {"user_id": 2, "email_address": "www@www.com"},
        {"user_id": 2, "email_address": "wendy@aol.com"},
    ],
)

print("\n -- Selecting -- \n")

from sqlalchemy.sql import select

s = select([users])
result = conn.execute(s)

for row in result:
    print(row)

result = conn.execute(s)
row = result.fetchone()
print("name:", row["name"], "; fullname:", row["fullname"])

row = result.fetchone()
print("name:", row[1], "; fullname:", row[2])

for row in conn.execute(s):
    print("name:", row[users.c.name], "; fullname:", row[users.c.fullname])

result.close()

print("\n -- Selecting Specific Columns -- \n")

s = select([users.c.name, users.c.fullname])
result = conn.execute(s)
for row in result:
    print(row)

for row in conn.execute(select([users, addresses])):
    print(row)

s = select([users, addresses]).where(users.c.id == addresses.c.user_id)
for row in conn.execute(s):
    print(row)

print(users.c.id == addresses.c.user_id)

print("\n -- Operators -- \n")

print(users.c.id == addresses.c.user_id)

print(users.c.id == 7)
print((users.c.id == 7).compile().params)

print(users.c.id != 7)
# None converts to IS NULL
print(users.c.name == None)
# reverse works too
print("fred" > users.c.name)

print(users.c.id + addresses.c.id)

print(users.c.name + users.c.fullname)
# print((users.c.name + users.c.fullname).compile(bind=create_engine("mysql://")))

print(users.c.name.op("tiddlywinks")("foo"))

print("\n -- Conjunctions -- \n")

from sqlalchemy.sql import and_, or_, not_
print(and_(
        users.c.name.like('j%'),
        users.c.id == addresses.c.user_id,
        or_(
            addresses.c.email_address == 'wendy@aol.com',
            addresses.c.email_address == 'jack@yahoo.com'
        ),
        not_(users.c.id > 5)
))

print(users.c.name.like('j%') & (users.c.id == addresses.c.user_id) &
    (
        (addresses.c.email_address == 'wendy@aol.com') | \
        (addresses.c.email_address == 'jack@yahoo.com')
    ) \
    & ~(users.c.id>5)
)

s = select([(users.c.fullname +
            ", " + addresses.c.email_address).label('title')]).\
        where(
            and_(
                users.c.id == addresses.c.user_id,
                users.c.name.between('m', 'z'),
                or_(
                    addresses.c.email_address.like('%aol.com'),
                    addresses.c.email_address.like('%msn.com')
                )
            )
        )
print(conn.execute(s).fetchall())

s = select([(users.c.fullname + ', ' + addresses.c.email_address).label('title')]).\
    where(users.c.id == addresses.c.user_id).\
    where(users.c.name.between('m', 'z')).\
    where(
        or_(
            addresses.c.email_address.like('%@aol.com'),
            addresses.c.email_address.like('%@msn.com')
        )
    )
print(conn.execute(s).fetchall())


print("\n -- Using Textual SQL -- \n")

from sqlalchemy.sql import text
s = text(
    "SELECT users.fullname || ', ' || addresses.email_address AS title "
        "FROM users, addresses "
        "WHERE users.id = addresses.user_id "
        "AND users.name BETWEEN :x AND :y "
        "AND (addresses.email_address LIKE :e1 "
            "OR addresses.email_address LIKE :e2)")
print(conn.execute(s, x='m', y='z', e1='%@aol.com', e2='%@msn.com').fetchall())

stmt = text('SELECT * FROM users WHERE users.name BETWEEN :x AND :y')
stmt = stmt.bindparams(x="m", y="z")

from sqlalchemy.sql import bindparam
stmt = stmt.bindparams(bindparam('x', type_=String), bindparam('y', type_=String))
result = conn.execute(stmt, {'x': 'm', 'y': 'z'})

stmt = stmt.columns(id=Integer, name=String)

stmt = text('SELECT id, name FROM users')
stmt = stmt.columns(users.c.id, users.c.name)

j = stmt.join(addresses, stmt.c.id == addresses.c.user_id)
new_stmt = select([stmt.c.id, addresses.c.id]).select_from(j).where(stmt.c.name == 'x')

stmt = text("SELECT users.id, addresses.id, users.id, "
    "users.name, addresses.email_address AS email "
    "FROM users JOIN addresses ON users.id=addresses.user_id "
    "WHERE users.id = 1").columns(
        users.c.id,
        addresses.c.id,
        addresses.c.user_id,
        users.c.name,
        addresses.c.email_address
    )
result = conn.execute(stmt)

row = result.fetchone()
print(row[addresses.c.email_address])

# print(row['id'])

s = select([
        text("users.fullname || ', ' || addresses.email_address AS title")
    ]).\
        where(
            and_(
                text("users.id = addresses.user_id"),
                text("users.name BETWEEN 'm' AND 'z'"),
                text(
                    "(addresses.email_address LIKE :x "
                    "OR addresses.email_address LIKE :y)")
            )
        ).select_from(text('users, addresses'))
print(conn.execute(s, x='%@aol.com', y='%@msn.com').fetchall())

from sqlalchemy import select, and_, text, String
from sqlalchemy.sql import table, literal_column
s = select([
    literal_column("users.fullname", String) +
    ', ' +
    literal_column("addresses.email_address").label("title")
]).\
    where(
        and_(
            literal_column("users.id") == literal_column("addresses.user_id"),
            text("users.name BETWEEN 'm' AND 'z'"),
            text(
                "(addresses.email_address LIKE :x OR "
                "addresses.email_address LIKE :y)"
            )
        )
    ).select_from(table('users')).select_from(table('addresses'))
print(conn.execute(s, x='%@aol.com', y='%@msn.com').fetchall())

from sqlalchemy import func
stmt = select([
    addresses.c.user_id,
    func.count(addresses.c.id).label('num_addresses')
]).group_by("user_id").order_by("user_id", "num_addresses")
print(conn.execute(stmt).fetchall())

from sqlalchemy import desc
stmt = select([
    addresses.c.user_id,
    func.count(addresses.c.id).label('num_addresses')
]).group_by('user_id').order_by('user_id', desc('num_addresses'))
print(conn.execute(stmt).fetchall())