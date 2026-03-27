from django import forms
from ads.models import Ad, Comment, Message
from django.core.files.uploadedfile import InMemoryUploadedFile
from ads.humanize import naturalsize

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model


# Create the form class.
class CreateForm(forms.ModelForm):
    max_upload_limit = 3 * 1024 * 1024
    max_upload_limit_text = naturalsize(max_upload_limit)

    # Call this 'picture' so it gets copied from the form to the in-memory model
    # It will not be the "bytes", it will be the "InMemoryUploadedFile"
    # because we need to pull out things like content_type

    picture = forms.FileField(required=False, label='File to Upload <= '+max_upload_limit_text)
    upload_field_name = 'picture'

    # Hint: this will need to be changed for use in the ads application :)
    class Meta:
        model = Ad
        fields = ['title', 'price', 'text', 'picture']  # Picture is manual

    # Validate the size of the picture
    def clean(self):
        cleaned_data = super().clean()
        pic = cleaned_data.get('picture')
        if pic is None:
            return
        if len(pic) > self.max_upload_limit:
            self.add_error('picture', "File must be < "+self.max_upload_limit_text+" bytes")

    # Convert uploaded File object to a picture
    def save(self, commit=True):
        instance = super(CreateForm, self).save(commit=False)

        # We only need to adjust picture if it is a freshly uploaded file
        f = instance.picture   # Make a copy
        if isinstance(f, InMemoryUploadedFile):  # Extract data from the form to the model
            bytearr = f.read()
            instance.content_type = f.content_type
            instance.picture = bytearr  # Overwrite with the actual image data

        if commit:
            instance.save()

        return instance

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {
            'text': '',
        }
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 2,
                'id': 'comment-textarea',
                'placeholder': 'Logged in users can comment here...'
            })
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['encrypted_text']
        labels = {
            'encrypted_text': '',
        }
        widgets = {
            'encrypted_text': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Write your message...',
                'class': 'message-input',
            })
        }

    def clean_encrypted_text(self):
        text = self.cleaned_data['encrypted_text'].strip()
        if len(text) < 2:
            raise forms.ValidationError('Message must be at least 2 characters.')
        return text


class NewUserForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = get_user_model()
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super(NewUserForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

# https://docs.djangoproject.com/en/3.0/topics/http/file-uploads/
# https://stackoverflow.com/questions/2472422/django-file-upload-size-limit
# https://stackoverflow.com/questions/32007311/how-to-change-data-in-django-modelform
# https://docs.djangoproject.com/en/3.0/ref/forms/validation/#cleaning-and-validating-fields-that-depend-on-each-other
