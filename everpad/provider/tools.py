import sys
sys.path.insert(0, '../..')
from evernote.edam.error.ttypes import EDAMUserException
from thrift.protocol import TBinaryProtocol
from thrift.transport import THttpClient
from evernote.edam.userstore import UserStore
from evernote.edam.notestore import NoteStore
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from everpad.provider.models import Base
from everpad.const import HOST, SCHEMA_VERSION
from urlparse import urlparse
import os


ACTION_NONE = 0
ACTION_CREATE = 1
ACTION_DELETE = 2
ACTION_CHANGE = 3
ACTION_NOEXSIST = 4

def _nocase_lower(item):
    return unicode(item).lower()


def set_auth_token(token):
    import keyring
    keyring.set_password('everpad', 'oauth_token', token)


def get_db_session(db_path=None):
    if not db_path:
        db_path = os.path.expanduser('~/.everpad/everpad.%s.db' % SCHEMA_VERSION)
    engine = create_engine('sqlite:///%s' % db_path)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    conn = session.connection()
    conn.connection.create_function('lower', 1, _nocase_lower)
    return session


def get_proxy_config(scheme):
    for fmt in ('%s_proxy', '%s_PROXY'):
        proxy = os.environ.get(fmt % scheme)
        if proxy is not None:
            return proxy
    return None


def get_note_store(auth_token=None):
    if not auth_token:
        auth_token = get_auth_token()
    user_store_uri = "https://" + HOST + "/edam/user"

    user_store_http_client = THttpClient.THttpClient(user_store_uri,
            http_proxy=get_proxy_config(urlparse(user_store_uri).scheme))
    user_store_protocol = TBinaryProtocol.TBinaryProtocol(user_store_http_client)
    user_store = UserStore.Client(user_store_protocol)
    note_store_url = user_store.getNoteStoreUrl(auth_token)
    note_store_http_client = THttpClient.THttpClient(note_store_url,
            http_proxy=get_proxy_config(urlparse(note_store_url).scheme))
    note_store_protocol = TBinaryProtocol.TBinaryProtocol(note_store_http_client)
    return NoteStore.Client(note_store_protocol)
