from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note

from .constants import (ADD, DELETE, DETAIL, EDIT, HOME, LIST, LOGIN, LOGOUT,
                        SIGNUP, SUCCESS)

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='username')
        cls.author = User.objects.create(username='author')
        cls.client = Client()
        cls.note = Note.objects.create(
            title='Title of the note',
            text='Note text',
            slug='slug_1',
            author=cls.author
        )

    def test_availability(self):
        pages = (
            HOME,
            LOGIN,
            LOGOUT,
            SIGNUP
        )
        for page in pages:
            with self.subTest(page=page):
                response = self.client.get(reverse(page))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_auth_user_can_get_page(self):
        self.client.force_login(self.user)
        urls = (
            LIST,
            SUCCESS,
            ADD
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(reverse(url))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_only_author_can_do(self):
        users_and_statuses = (
            (self.user, HTTPStatus.NOT_FOUND),
            (self.author, HTTPStatus.OK)
        )
        pages = (
            EDIT,
            DELETE,
            DETAIL
        )
        for user, status in users_and_statuses:
            for page in pages:
                with self.subTest(user=user, status=status, page=page):
                    self.client.force_login(user)
                    response = self.client.get(
                        reverse(page, args=(self.note.slug,))
                    )
                    self.assertEqual(response.status_code, status)

    def test_anonymous_redirect(self):
        pages_slugs = (
            (LIST, None),
            (SUCCESS, None),
            (ADD, None),
            (DETAIL, self.note.slug),
            (EDIT, self.note.slug),
            (DELETE, self.note.slug)
        )
        login_url = reverse(LOGIN)
        for page, slug in pages_slugs:
            with self.subTest(page=page, slug=slug):
                if slug is not None:
                    url = reverse(page, args=(slug, ))
                else:
                    url = reverse(page)
                response = self.client.get(url)
                redirect_url = f'{login_url}?next={url}'
                self.assertRedirects(response, redirect_url)
