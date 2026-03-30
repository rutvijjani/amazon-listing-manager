from types import SimpleNamespace

from bson.objectid import ObjectId

import app as app_module
from app.models import AmazonConnection, User


class FakeCursor:
    def __init__(self, docs):
        self.docs = list(docs)

    def sort(self, key, direction):
        reverse = direction == -1
        self.docs.sort(key=lambda doc: doc.get(key), reverse=reverse)
        return self

    def limit(self, n):
        self.docs = self.docs[:n]
        return self

    def skip(self, n):
        self.docs = self.docs[n:]
        return self

    def __iter__(self):
        return iter(self.docs)


class FakeCollection:
    def __init__(self):
        self.docs = []

    def create_index(self, *args, **kwargs):
        return None

    def _matches(self, doc, query):
        for key, value in query.items():
            if isinstance(value, dict):
                doc_value = doc.get(key)
                for operator, operand in value.items():
                    if operator == "$gt":
                        if not (doc_value and doc_value > operand):
                            return False
                    else:
                        return False
            elif doc.get(key) != value:
                return False
        return True

    def find_one(self, query):
        for doc in self.docs:
            if self._matches(doc, query):
                return doc.copy()
        return None

    def find(self, query):
        return FakeCursor([doc.copy() for doc in self.docs if self._matches(doc, query)])

    def insert_one(self, data):
        doc = data.copy()
        doc.setdefault("_id", ObjectId())
        self.docs.append(doc)
        return SimpleNamespace(inserted_id=doc["_id"])

    def update_one(self, query, update):
        modified = 0
        for doc in self.docs:
            if self._matches(doc, query):
                for op, values in update.items():
                    if op == "$set":
                        doc.update(values)
                    elif op == "$inc":
                        for key, value in values.items():
                            doc[key] = doc.get(key, 0) + value
                modified = 1
                break
        return SimpleNamespace(modified_count=modified)

    def update_many(self, query, update):
        modified = 0
        for doc in self.docs:
            if self._matches(doc, query):
                for op, values in update.items():
                    if op == "$set":
                        doc.update(values)
                modified += 1
        return SimpleNamespace(modified_count=modified)

    def find_one_and_update(self, query, update):
        for doc in self.docs:
            if self._matches(doc, query):
                original = doc.copy()
                for op, values in update.items():
                    if op == "$set":
                        doc.update(values)
                return original
        return None

    def count_documents(self, query):
        return sum(1 for doc in self.docs if self._matches(doc, query))


class FakeDB:
    def __init__(self):
        self.users = FakeCollection()
        self.amazon_connections = FakeCollection()
        self.update_logs = FakeCollection()
        self.bulk_update_jobs = FakeCollection()
        self.invitations = FakeCollection()

    def __getitem__(self, name):
        return getattr(self, name)


def build_test_app():
    fake_db = FakeDB()
    app_module.mongo.init_app = lambda *args, **kwargs: None
    app_module.mongo.db = fake_db

    test_app = app_module.create_app()
    test_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SECRET_KEY="test-secret",
        TOKEN_ENCRYPTION_KEY="3r1m3sj3tkfCBY0xWm5gQ8m4eQ8PwWnN7TqLz7x5WvM=",
    )
    return test_app


def login_test_user(client, email="qa@example.com", password="secret123"):
    client.post(
        "/auth/register",
        data={
            "name": "QA User",
            "email": email,
            "password": password,
            "confirm_password": password,
        },
        follow_redirects=True,
    )
    return client.post(
        "/auth/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def attach_connection(email="qa@example.com"):
    user = User.find_by_email(email)
    assert user is not None
    connection = AmazonConnection(
        {
            "user_id": user.id,
            "seller_id": "SELLER123",
            "marketplace_id": "A21TJRUUN4KGV",
            "marketplace_name": "India",
            "refresh_token_encrypted": "encrypted-token",
            "is_active": True,
        }
    )
    connection.save()
    return user



