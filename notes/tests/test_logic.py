from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

from .constants import ADD, DELETE, EDIT, LOGIN, SUCCESS

User = get_user_model()

NOTE_ADD_URL = reverse(ADD)


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='author')
        cls.auth_user = User.objects.create(username='auth_user')
        cls.client = Client()
        cls.note = Note.objects.create(
            title='Title of the note',
            text='Note text',
            slug='slug_1',
            author=cls.author
        )
        cls.note_data = {
            'title': 'New Title',
            'text': 'New text',
            'slug': 'new_slug'
        }
        cls.note_data_without_slug = {
            'title': 'New Title',
            'text': 'New text'
        }

    def test_auth_user_can_create_a_note(self):
        self.client.force_login(self.auth_user)
        response = self.client.post(NOTE_ADD_URL, data=self.note_data)
        self.assertRedirects(response, reverse(SUCCESS))
        self.assertEqual(Note.objects.count(), 2)

    def test_anonymous_cant_create_a_note(self):
        response = self.client.post(NOTE_ADD_URL, data=self.note_data)
        login_url = reverse(LOGIN)
        redirect_url = f'{login_url}?next={NOTE_ADD_URL}'
        self.assertRedirects(response, redirect_url)
        self.assertEqual(Note.objects.count(), 1)

    def test_notes_with_the_same_slug_cant_be_made(self):
        self.client.force_login(self.auth_user)
        note = Note.objects.create(
            title='title of the note',
            text='note text',
            slug=self.note_data['slug'],
            author=self.auth_user
        )
        response = self.client.post(NOTE_ADD_URL, data=self.note_data)
        self.assertFormError(
            response,
            'form',
            'slug',
            errors=(note.slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), 2)

    def test_empty_slug(self):
        self.client.force_login(self.auth_user)
        response = self.client.post(
            NOTE_ADD_URL,
            data=self.note_data_without_slug
        )
        self.assertRedirects(response, reverse(SUCCESS))
        self.assertEqual(Note.objects.count(), 2)
        new_note = Note.objects.get(title=self.note_data_without_slug['title'])
        expected_slug = slugify(self.note_data_without_slug['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_a_note(self):
        self.client.force_login(self.author)
        url = reverse(EDIT, args=(self.note.slug,))
        response = self.client.post(url, self.note_data)
        self.assertRedirects(response, reverse(SUCCESS))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.note_data['title'])
        self.assertEqual(self.note.text, self.note_data['text'])
        self.assertEqual(self.note.slug, self.note_data['slug'])

    def test_author_can_delete_a_note(self):
        self.client.force_login(self.author)
        url = reverse(DELETE, args=(self.note.slug,))
        response = self.client.post(url)
        self.assertRedirects(response, reverse(SUCCESS))
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_edit_note(self):
        self.client.force_login(self.auth_user)
        url = reverse(EDIT, args=(self.note.slug,))
        response = self.client.post(url, self.note_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(pk=self.note.id)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)

    def test_other_user_cant_delete_note(self):
        self.client.force_login(self.auth_user)
        url = reverse(DELETE, args=(self.note.slug,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
