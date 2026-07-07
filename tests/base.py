import unittest
from app import create_app, db


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app({
            'TESTING': True,
            'WTF_CSRF_ENABLED': False,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        })

        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

        db.drop_all()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self, email, password):
        return self.client.post(
            '/login',
            data={'email': email, 'password': password},
            follow_redirects=True
        )
