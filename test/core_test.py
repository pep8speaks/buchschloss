"""Test core"""

import datetime
import pytest
import peewee

from buchschloss import core, models, utils, config

temp_test_db = peewee.SqliteDatabase(':memory:')


@pytest.fixture  # adapted from http://docs.peewee-orm.com/en/3.1.0/peewee/api.html#Database.bind_ctx
def db():
    """bind the models to the test database"""
    with temp_test_db.bind_ctx(models.models):
        temp_test_db.create_tables(models.models)
        try:
            yield
        finally:
            temp_test_db.drop_tables(models.models)


def create_book(lib='main'):
    """create a Book with falsey values. The Library can be specified"""
    return models.Book.create(isbn=0, author='', title='', language='', publisher='',
                              year=0, medium='', shelf='', library=lib)


def test_misc_data(db):
    """test the misc_data accessor for the misc table"""
    models.Misc.create(pk='test_pk_1', data=[1, 2, 3])
    models.Misc.create(pk='test_pk_2', data=0)
    assert core.misc_data.test_pk_1 == [1, 2, 3]
    core.misc_data.test_pk_2 = 'test_string'
    assert models.Misc.get_by_id('test_pk_2').data == 'test_string'
    models.db.connect()
    assert core.misc_data.test_pk_1 == [1, 2, 3]
    assert models.db.close()
    models.db.connect()
    core.misc_data.test_pk_1 += [4]
    assert core.misc_data.test_pk_1 == [1, 2, 3, 4]
    assert models.db.close()
    with pytest.raises(AttributeError):
        core.misc_data.does_not_exist
    with pytest.raises(AttributeError):
        core.misc_data.also_doesnt_exist = None


def test_person_new(db):
    """test Person.new"""
    for level in range(3):
        core.current_login.level = level
        with pytest.raises(core.BuchSchlossBaseError):
            core.Person.new(123, 'first', 'last', 'cls')
    core.current_login.level = 3
    core.Person.new(123, 'first', 'last', 'cls')
    p = models.Person.get_by_id(123)
    assert p.id == 123
    assert p.first_name == 'first'
    assert p.last_name == 'last'
    assert p.max_borrow == 3
    assert len(p.libraries) == 0
    assert p.pay_date is None
    core.current_login.level = 4
    old_today = datetime.date.today()  # in case this is run around midnight...
    core.Person.new(124, 'first', 'last', 'cls', 5, pay=True)
    p = models.Person.get_by_id(124)
    assert p.id == 124
    assert p.max_borrow == 5
    assert p.pay_date in (datetime.date.today(), old_today)
    core.Person.new(125, 'first', 'last', 'cls', pay_date=datetime.date(1956, 1, 31))
    p = models.Person.get_by_id(125)
    assert p.id == 125
    assert p.pay_date == datetime.date(1956, 1, 31)
    models.Library.create(name='main')
    core.Person.new(126, 'first', 'last', 'cls')
    p = models.Person.get_by_id(126)
    assert p.id == 126
    assert list(p.libraries) == [models.Library.get_by_id('main')]


def test_person_edit(db):
    """test Person.edit"""
    models.Person.create(id=123, first_name='first', last_name='last', class_='cls',
                         max_borrow=3, pay_date=datetime.date(1956, 1, 31))
    for level in range(3):
        core.current_login.level = level
        with pytest.raises(core.BuchSchlossBaseError):
            core.Person.edit(123)
    core.current_login.level = 4
    core.Person.edit(123, first_name='other_value')
    assert models.Person.get_by_id(123).first_name == 'other_value'
    core.Person.edit(123, last_name='value_for_last', pay_date=None)
    p = models.Person.get_by_id(123)
    assert p.last_name == 'value_for_last'
    assert p.pay_date is None
    old_today = datetime.date.today()
    core.Person.edit(123, pay=True)
    assert models.Person.get_by_id(123).pay_date in (datetime.date.today(), old_today)
    models.Library.create(name='lib_1')
    models.Library.create(name='lib_2')
    e = core.Person.edit(123, libraries=('lib_1', 'lib_does_not_exist'))
    assert e
    assert list(models.Person.get_by_id(123).libraries) == [models.Library.get_by_id('lib_1')]
    with pytest.raises(core.BuchSchlossBaseError):
        core.Person.edit(124)
    with pytest.raises(TypeError):
        core.Person.edit(123, no_option=123)
    with pytest.raises(TypeError):
        core.Person.edit(123, id=124)


def test_person_view_str(db):
    """test Person.view_str"""
    p = models.Person.create(id=123, first_name='first', last_name='last', class_='cls',
                             max_borrow=3, pay_date=datetime.date(1956, 1, 31))
    core.current_login.level = 0
    with pytest.raises(core.BuchSchlossBaseError):
        core.Person.view_str(123)
    core.current_login.level = 1
    with pytest.raises(core.BuchSchlossBaseError):
        core.Person.view_str(12345)
    assert core.Person.view_str(123) == {
        'id': '123',
        'first_name': 'first',
        'last_name': 'last',
        'class_': 'cls',
        'max_borrow': '3',
        'pay_date': str(utils.FormattedDate.fromdate(datetime.date(1956, 1, 31))),
        'borrows': (),
        'borrow_book_ids': [],
        'libraries': '',
        '__str__': str(models.Person.get_by_id(123)),
    }
    p.libraries.add(models.Library.create(name='main'))
    assert core.Person.view_str(123)['libraries'] == 'main'
    create_book()
    models.Borrow.create(person=123, book=1, return_date=datetime.date(1956, 1, 31))
    info = core.Person.view_str(123)
    assert info['borrows'] == (str(models.Borrow.get_by_id(1)),)
    assert info['borrow_book_ids'] == [1]
    p.libraries.add(models.Library.create(name='testlib'))
    info = core.Person.view_str(123)
    assert info['libraries'] in ('main;testlib', 'testlib;main')
    create_book()
    models.Borrow.create(person=123, book=2, return_date=datetime.date(1956, 1, 31))
    info = core.Person.view_str(123)
    assert info['borrows'] in (
        (str(models.Borrow.get_by_id(1)), str(models.Borrow.get_by_id(2))),
        (str(models.Borrow.get_by_id(2)), str(models.Borrow.get_by_id(1))),
    )
    assert info['borrow_book_ids'] in ([1, 2], [2, 1])


def test_book_new(db):
    """test Book.new"""
    models.Library.create(name='main')
    for level in range(2):
        core.current_login.level = level
        with pytest.raises(core.BuchSchlossBaseError):
            core.Book.new(123, 456, author='author', title='title', language='lang',
                          publisher='publisher', medium='medium', shelf='A1')
    core.current_login.level = 2
    b_id = core.Book.new(123, 456, author='author', title='title', language='lang',
                         publisher='publisher', medium='medium', shelf='A1')
    assert b_id == 1
    b = models.Book.get_by_id(b_id)
    assert b.isbn == 123
    assert b.year == 456
    assert b.author == 'author'
    assert b.title == 'title'
    assert b.language == 'lang'
    assert b.publisher == 'publisher'
    assert b.medium == 'medium'
    assert b.shelf == 'A1'
    assert b.library.name == 'main'
    assert tuple(b.groups) == ()
    with pytest.raises(core.BuchSchlossBaseError):
        core.Book.new(123, 456, author='author', title='title', language='lang',
                      publisher='publisher', medium='medium', shelf='A1',
                      library='does_not_exist')
    models.Library.create(name='other_lib')
    b_id = core.Book.new(123, 456, author='author', title='title', language='lang',
                         publisher='publisher', medium='medium', shelf='A1',
                         library='other_lib')
    assert b_id == 2
    assert models.Book.get_by_id(b_id).library.name == 'other_lib'
    b_id = core.Book.new(123, 456, author='author', title='title', language='lang',
                         publisher='publisher', medium='medium', shelf='A1',
                         groups=['grp0'])
    assert b_id == 3
    assert list(models.Book.get_by_id(b_id).groups) == [models.Group.get_by_id('grp0')]
    b_id = core.Book.new(123, 456, author='author', title='title', language='lang',
                         publisher='publisher', medium='medium', shelf='A1',
                         groups=['grp0', 'grp1'])
    assert b_id == 4
    assert set(models.Book.get_by_id(b_id).groups) == {
        models.Group.get_by_id('grp0'), models.Group.get_by_id('grp1')}


def test_book_edit(db):
    """test Book.edit"""
    models.Library.create(name='main')
    create_book()
    create_book()
    for level in range(2):
        core.current_login.level = level
        with pytest.raises(core.BuchSchlossBaseError):
            core.Book.edit(1, isbn=1)
    core.current_login.level = 2
    assert not core.Book.edit(1, isbn=1)
    assert models.Book.get_by_id(1).isbn == 1
    assert models.Book.get_by_id(2).isbn == 0
    assert not core.Book.edit(1, author='author', shelf='shl')
    assert models.Book.get_by_id(1).author == 'author'
    assert models.Book.get_by_id(1).shelf == 'shl'
    assert models.Book.get_by_id(2).author == ''
    assert models.Book.get_by_id(2).shelf == ''
    models.Library.create(name='lib')
    assert not core.Book.edit(1, library='lib')
    assert models.Book.get_by_id(1).library.name == 'lib'
    assert models.Book.get_by_id(2).library.name == 'main'
    assert core.Book.edit(1, library='does_not_exist')
    assert models.Book.get_by_id(1).library.name == 'lib'
    assert not core.Book.edit(1, medium='med')
    assert not core.Book.edit(1, year=123)
    assert models.Book.get_by_id(1).medium == 'med'
    assert models.Book.get_by_id(1).year == 123
    assert models.Book.get_by_id(2).medium == ''
    assert models.Book.get_by_id(2).year == 0


def test_book_view_str(db):
    """test Book.view_str"""
    for n in range(2):
        models.Library.create(name='lib{}'.format(n))
        models.Group.create(name='grp{}'.format(n))
    models.Book.create(isbn=123, author='author', title='title', language='lang',
                       publisher='publ', year=456, medium='rare', library='lib0',
                       shelf='A5')
    b = models.Book.get_by_id(1)
    core.current_login.level = 0
    assert core.Book.view_str(1) == {
        'id': '1',
        'isbn': '123',
        'author': 'author',
        'title': 'title',
        'language': 'lang',
        'publisher': 'publ',
        'year': '456',
        'medium': 'rare',
        'series': '',
        'concerned_people': '',
        'genres': '',
        'shelf': 'A5',
        'library': 'lib0',
        'groups': '',
        'status': utils.get_name('available'),
        'return_date': '-----',
        'borrowed_by': '-----',
        'borrowed_by_id': None,
        '__str__': str(b),
    }
    b.library = models.Library.get_by_id('lib1')
    b.save()
    assert core.Book.view_str(1)['library'] == 'lib1'
    b.groups.add('grp0')
    assert core.Book.view_str(1)['groups'] == 'grp0'
    b.groups.add('grp1')
    assert core.Book.view_str(1)['groups'] in ('grp0;grp1', 'grp1;grp0')
    models.Person.create(id=123, first_name='first', last_name='last',
                         class_='cls', max_borrow=3)
    borrow = models.Borrow.create(book=1, person=123, return_date=datetime.date(1956, 1, 31))
    data = core.Book.view_str(1)
    assert data['status'] == utils.get_name('borrowed')
    assert data['return_date'] == datetime.date(1956, 1, 31).strftime(config.DATE_FORMAT)
    assert data['borrowed_by'] == str(models.Person.get_by_id(123))
    assert data['borrowed_by_id'] == 123
    borrow.is_back = True
    borrow.save()
    assert core.Book.view_str(1)['status'] == utils.get_name('available')
    b.is_active = False
    b.save()
    assert core.Book.view_str(1)['status'] == utils.get_name('inactive')


def test_library_new(db):
    """test Library.new"""
    models.Library.create(name='main')
    create_book()
    create_book()
    models.Person.create(id=123, first_name='', last_name='', class_='', max_borrow=0)
    models.Person.create(id=456, first_name='', last_name='', class_='', max_borrow=0)
    for level in range(3):
        core.current_login.level = level
        with pytest.raises(core.BuchSchlossBaseError):
            core.Library.new('testlib')
    core.current_login.level = 3
    core.Library.new('testlib')
    assert models.Library.get_or_none(name='testlib')
    with pytest.raises(core.BuchSchlossBaseError):
        core.Library.new('testlib')
    assert models.Library.get_by_id('testlib').pay_required
    core.Library.new('test-1', books=[1], people=[123])
    assert models.Book.get_by_id(1).library.name == 'test-1'
    assert (tuple(models.Person.get_by_id(123).libraries)
            == (models.Library.get_by_id('test-1'),))
    core.Library.new('test-2', books=(1, 2), people=[123, 456])
    assert models.Book.get_by_id(1).library.name == 'test-2'
    assert models.Book.get_by_id(1).library.name == 'test-2'
    assert (set(models.Person.get_by_id(123).libraries) ==
            {models.Library.get_by_id('test-1'), models.Library.get_by_id('test-2')})
    assert (tuple(models.Person.get_by_id(456).libraries)
            == (models.Library.get_by_id('test-2'),))
