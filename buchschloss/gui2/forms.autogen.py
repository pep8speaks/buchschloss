"""These forms were autogenerated from the models in ..\models.py by autoform.py"""


class ModelForm(mtkf.Form):
    id: mtkf.Element = IntEntry


class PersonForm(mtkf.Form):
    s_nr: mtkf.Element = IntEntry
    first_name: mtkf.Element = Entry
    last_name: mtkf.Element = Entry
    class_: mtkf.Element = Entry
    max_borrow: mtkf.Element = IntEntry
    pay_date: mtkf.Element = ...
    libraries: mtkf.Element = ...


class LibraryForm(mtkf.Form):
    person: mtkf.Element = ...
    name: mtkf.Element = Entry
    id: mtkf.Element = IntEntry


class BookForm(mtkf.Form):
    isbn: mtkf.Element = IntEntry
    author: mtkf.Element = Entry
    title: mtkf.Element = Entry
    series: mtkf.Element = Entry
    language: mtkf.Element = Entry
    publisher: mtkf.Element = Entry
    concerned_people: mtkf.Element = Entry
    year: mtkf.Element = IntEntry
    medium: mtkf.Element = Entry
    genres: mtkf.Element = Entry
    library: mtkf.Element = ...
    shelf: mtkf.Element = Entry
    is_active: mtkf.Element = CheckbuttonWithVar
    id: mtkf.Element = IntEntry
    library_id: mtkf.Element = ...
    groups: mtkf.Element = ...


class GroupForm(mtkf.Form):
    book: mtkf.Element = ...
    name: mtkf.Element = Entry
    id: mtkf.Element = IntEntry


class BorrowForm(mtkf.Form):
    person: mtkf.Element = ...
    book: mtkf.Element = ...
    is_back: mtkf.Element = CheckbuttonWithVar
    return_date: mtkf.Element = ...
    id: mtkf.Element = IntEntry
    person_id: mtkf.Element = ...
    book_id: mtkf.Element = ...


class MemberForm(mtkf.Form):
    name: mtkf.Element = Entry
    password: mtkf.Element = ...
    salt: mtkf.Element = ...
    level: mtkf.Element = IntEntry


class MiscForm(mtkf.Form):
    pk: mtkf.Element = Entry
    data: mtkf.Element = ...