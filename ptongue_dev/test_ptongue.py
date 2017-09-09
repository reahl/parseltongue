

from ptongue import Session, GemObject


class Stone:
   def start(self):
       pass
   def stop(self):
       pass
   def is_started(self):
       return False

class NetLdi:
   def start(self, guest_mode=True):
       pass
   def stop(self):
       pass


def test_login_captive_os_user():
    session = Session('DataCurator', 'swordfish')
    assert session.is_logged_in

    session.logout()
    assert not session.is_logged_in

def test_login_os_user():
    session = Session('DataCurator', 'swordfish', host_username='vagrant', host_password='vagrant')
    assert session.is_logged_in

    session.logout()
    assert not session.is_logged_in


def test_resolve_string_symbol():
    session = Session('DataCurator', 'swordfish')
    try:
        nil = session.resolve_symbol('nil') 
        assert isinstance(nil, GemObject)
        assert nil.oop == 20
    finally:
        session.logout()

     
def test_resolve_symbol_object():
    session = Session('DataCurator', 'swordfish')
    try:
        nil_symbol = session.new_symbol('nil')
        assert isinstance(nil_symbol, GemObject)
        nil = session.resolve_symbol(nil_symbol) 
        assert isinstance(nil, GemObject)
        assert nil.oop == 20
    finally:
        session.logout()


def test_basic_perform_returns_value():
    session = Session('DataCurator', 'swordfish')
    try:
        date_class = session.resolve_symbol('Date')
        return_object = date_class.perform('yourself')
        assert date_class.oop == returned_object.oop
    finally:
        session.logout()
    

def test_transactions():
    pass



