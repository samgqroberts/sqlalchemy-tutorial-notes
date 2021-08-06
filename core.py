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

print('\n - Specifying Bound Parameter Behaviors - \n')

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

print('\n - Specifying Result-Column Behaviors - \n')

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

print('\n - Using text() fragments inside bigger statements - \n')

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

print('\n Using More Specific Text with table(), literal_column(), and column() - \n')

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

print('\n - Ordering or Grouping by a Label - \n')

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

u1a, u1b = users.alias(), users.alias()
stmt = select([u1a, u1b]).\
    where(u1a.c.name > u1b.c.name).\
        order_by(u1a.c.name)  # using "name" here would be ambiguous
print(conn.execute(stmt).fetchall())

print('\n -- Using Aliases and Subqueries -- \n')

a1 = addresses.alias()
a2 = addresses.alias()
s = select([users]).\
    where(and_(
        users.c.id == a1.c.user_id,
        users.c.id == a2.c.user_id,
        a1.c.email_address == 'jack@msn.com',
        a2.c.email_address == 'jack@yahoo.com'
    ))
print(conn.execute(s).fetchall())

a1 = addresses.alias('a1')

address_subq = s.alias()
s = select([users.c.name]).where(users.c.id == address_subq.c.id)
print(conn.execute(s).fetchall())

print('\n -- Using Joins -- \n')

print(users.join(addresses))

print(users.join(addresses, addresses.c.email_address.like(users.c.name + '%')))

s = select([users.c.fullname]).select_from(
    users.join(addresses, addresses.c.email_address.like(users.c.name + '%'))
)
print(conn.execute(s).fetchall())

s = select([users.c.fullname]).select_from(users.outerjoin(addresses))
print(s)

print('\n -- Common Table Expressions (CTE) -- \n')

users_cte = select([users.c.id, users.c.name]).where(users.c.name == 'wendy').cte()
stmt = select([addresses]).where(addresses.c.user_id == users_cte.c.id).order_by(addresses.c.id)
print(conn.execute(stmt).fetchall())

users_cte = select([users.c.id, users.c.name]).cte(recursive=True)
users_recursive = users_cte.alias()
users_cte = users_cte.union(select([users.c.id, users.c.name]).where(users.c.id > users_recursive.c.id))
stmt = select([addresses]).where(addresses.c.user_id == users_cte.c.id).order_by(addresses.c.id)
print(conn.execute(stmt).fetchall())

print('\n -- Everything Else -- \n')

print('\n - Bind Parameter Objects - \n')

from sqlalchemy.sql import bindparam
s = users.select(users.c.name == bindparam('username'))
print(conn.execute(s, username='wendy').fetchall())

s = users.select(users.c.name.like(bindparam('username', type_=String) + text("'%'")))
print(conn.execute(s, username='wendy').fetchall())

s = select([users, addresses]).\
    where(
        or_(
            users.c.name.like(
                bindparam('name', type_=String) + text("'%'")
            ),
            addresses.c.email_address.like(
                bindparam('name', type_=String) + text("'@%'")
            )
        )
    ).\
    select_from(users.outerjoin(addresses)).\
    order_by(addresses.c.id)
print(conn.execute(s, name='jack').fetchall())

print('\n - Functions - \n')

from sqlalchemy.sql import func
print(func.now())

print(func.concat('x', 'y'))

print(func.xyz_my_goofy_function())

print(func.current_timestamp())

print(conn.execute(
    select([
        func.max(addresses.c.email_address, type_=String).label('maxemail')
    ])
).scalar())

from sqlalchemy.sql import column
calculate = select([column('q'), column('z'), column('r')]).\
    select_from(
        func.calculate(bindparam('x'), bindparam('y'))
    )
calc = calculate.alias()
print(select([users]).where(users.c.id > calc.c.z))

calc1 = calculate.alias('c1').unique_params(x=17, y=45)
calc2 = calculate.alias('c2').unique_params(x=5, y=12)
s = select([users]).\
    where(users.c.id.between(calc1.c.z, calc2.c.z))
print(s)
print(s.compile().params)

print('\n - Window Functions - \n')

s = select([
    users.c.id,
    func.row_number().over(order_by=users.c.name)
])
print(s)

s = select([
    users.c.id,
    func.row_number().over(
        order_by=users.c.name,
        rows=(-2, None)
    )
])
print(s)

print('\n - Data Casts and Type Coercion - \n')

from sqlalchemy import cast
s = select([cast(users.c.id, String)])
print(conn.execute(s).fetchall())

import json
from sqlalchemy import JSON
from sqlalchemy import type_coerce
from sqlalchemy.dialects import mysql
s = select([type_coerce({'some_key': {'foo': 'bar'}}, JSON)['some_key']])
print(s.compile(dialect=mysql.dialect()))

print('\n - Unions and Other Set Operations - \n')

from sqlalchemy.sql import union
u = union(
    addresses.select().where(addresses.c.email_address == 'foo@bar.com'),
    addresses.select().where(addresses.c.email_address.like('%@yahoo.com')),
).order_by(addresses.c.email_address)
print(conn.execute(u).fetchall())

from sqlalchemy.sql import except_
u = except_(
    addresses.select().where(addresses.c.email_address.like('%@%.com')),
    addresses.select().where(addresses.c.email_address.like('%@msn.com'))
)
print(conn.execute(u).fetchall())

u = except_(
    union(
        addresses.select().where(addresses.c.email_address.like('%@yahoo.com')),
        addresses.select().where(addresses.c.email_address.like('%@msn.com'))
    ).alias().select(),  # apply subquery here
    addresses.select(addresses.c.email_address.like('%@msn.com'))
)
print(conn.execute(u).fetchall())

print('\n - Scalar Selects - \n')

stmt = select([func.count(addresses.c.id)]).\
    where(users.c.id == addresses.c.user_id).\
    as_scalar()

print(conn.execute(select([users.c.name, stmt])).fetchall())

stmt = select([func.count(addresses.c.id)]).\
    where(users.c.id == addresses.c.user_id).\
    label("address_count")
print(conn.execute(select([users.c.name, stmt])).fetchall())

print('\n - Correlated Subqueries - \n')

stmt = select([addresses.c.user_id]).\
    where(addresses.c.user_id == users.c.id).\
    where(addresses.c.email_address == 'jack@yahoo.com')
enclosing_stmt = select([users.c.name]).where(users.c.id == stmt)
print(conn.execute(enclosing_stmt).fetchall())

stmt = select([users.c.id]).\
    where(users.c.id == addresses.c.user_id).\
    where(users.c.name == 'jack').\
    correlate(addresses)
enclosing_stmt = select(
    [users.c.name, addresses.c.email_address]
).select_from(users.join(addresses)).\
    where(users.c.id == stmt)
print(conn.execute(enclosing_stmt).fetchall())

stmt = select([users.c.id]).\
    where(users.c.name == 'wendy').\
    correlate(None)
enclosing_stmt = select([users.c.name]).\
    where(users.c.id == stmt)
print(conn.execute(enclosing_stmt).fetchall())

stmt = select([users.c.id]).\
    where(users.c.id == addresses.c.user_id).\
    where(users.c.name == 'jack').\
    correlate_except(users)
enclosing_stmt = select([users.c.name, addresses.c.email_address]).\
    select_from(users.join(addresses)).\
    where(users.c.id == stmt)
print(conn.execute(enclosing_stmt).fetchall())

print('\n - LATERAL correlation - \n')

from sqlalchemy import table, column, select, true
people = table('people', column('people_id'), column('age'), column('name'))
books = table('books', column('book_id'), column('owner_id'))
subq = select([books.c.book_id]).\
    where(books.c.owner_id == people.c.people_id).lateral('book_subq')
print(select([people]).select_from(people.join(subq, true())))

print('\n - Ordering, Grouping, Limiting, Offset...ing... - \n')

stmt = select([users.c.name]).order_by(users.c.name)
print(conn.execute(stmt).fetchall())

stmt = select([users.c.name]).order_by(users.c.name.desc())
print(conn.execute(stmt).fetchall())

stmt = select([users.c.name, func.count(addresses.c.id)]).\
    select_from(users.join(addresses)).\
    group_by(users.c.name)
print(conn.execute(stmt).fetchall())

stmt = select([users.c.name, func.count(addresses.c.id)]).\
    select_from(users.join(addresses)).\
    group_by(users.c.name).\
    having(func.length(users.c.name) > 4)
print(conn.execute(stmt).fetchall())

stmt = select([users.c.name]).\
    where(addresses.c.email_address.contains(users.c.name)).\
    distinct()
print(conn.execute(stmt).fetchall())

stmt = select([users.c.name, addresses.c.email_address]).\
    select_from(users.join(addresses)).\
    limit(1).offset(1)
print(conn.execute(stmt).fetchall())

print('\n -- Inserts, Updates, and Deletes -- \n')

stmt = users.update().values(fullname="Fullname: " + users.c.name)
conn.execute(stmt)

stmt = users.insert().values(name=bindparam('_name') + ' .. name')
conn.execute(stmt, [
    {'id':4, '_name':'name1'},
    {'id':5, '_name':'name2'},
    {'id':6, '_name':'name3'},
])

stmt = users.update().\
    where(users.c.name == 'jack').\
    values(name='ed')
conn.execute(stmt)

stmt = users.update().\
    where(users.c.name == bindparam('oldname')).\
    values(name=bindparam('newname'))
conn.execute(stmt, [
    {'oldname':'jack', 'newname':'ed'},
    {'oldname':'wendy', 'newname':'mary'},
    {'oldname':'jim', 'newname':'jake'},
])

print('\n - Correlated Updates - \n')

stmt = select([addresses.c.email_address]).\
    where(addresses.c.user_id == users.c.id).\
    limit(1)
conn.execute(users.update().values(fullname=stmt))

print('\n - Multiple Table Updates - \n')

# stmt = users.update().\
#     values(name='ed wood').\
#     where(users.c.id == addresses.c.id).\
#     where(addresses.c.email_address.startswith('ed%'))
# conn.execute(stmt)

print('\n - Parameter-Ordered Updates - \n')

print('\n - Deletes - \n')

conn.execute(addresses.delete())
conn.execute(users.delete().where(users.c.name > 'm'))

print('\n - Multiple Table Deletes - \n')

print('\n - Matched Row Counts - \n')

result = conn.execute(users.delete())
print(result.rowcount)