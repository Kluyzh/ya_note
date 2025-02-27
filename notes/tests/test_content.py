from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note

from .constants import ADD, EDIT, LIST

User = get_user_model()


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.not_author = User.objects.create(username='not_author')
        cls.author = User.objects.create(username='author')
        cls.client = Client()
        cls.note = Note.objects.create(
            title='Title of the note',
            text='Note text',
            slug='slug_1',
            author=cls.author
        )

    def test_note_in_object_list(self):
        self.client.force_login(self.author)
        response = self.client.get(reverse(LIST))
        self.assertIn(self.note, response.context['object_list'])

    def test_note_not_in_object_list(self):
        self.client.force_login(self.not_author)
        response = self.client.get(reverse(LIST))
        self.assertNotIn(self.note, response.context['object_list'])

    def test_form_in_page(self):
        self.client.force_login(self.author)
        pages_args = (
            (EDIT, self.note.slug),
            (ADD, None)
        )
        for page, arg in pages_args:
            with self.subTest(page=page, arg=arg):
                if arg is not None:
                    response = self.client.get(reverse(page, args=(arg,)))
                else:
                    response = self.client.get(reverse(page))
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
