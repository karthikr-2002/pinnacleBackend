from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm text-slate-800 transition duration-150 ease-in-out placeholder:text-slate-400 bg-slate-50/50 hover:bg-white',
                'placeholder': 'Enter your username or email',
                'autocomplete': 'username',
                'id': 'login-username',
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm text-slate-800 transition duration-150 ease-in-out placeholder:text-slate-400 bg-slate-50/50 hover:bg-white pr-10',
                'placeholder': 'Enter your password',
                'autocomplete': 'current-password',
                'id': 'login-password',
            }
        )
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                'class': 'w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500 focus:ring-offset-0',
                'id': 'remember-me',
            }
        )
    )


class UserRegisterForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm text-slate-800 transition duration-150 ease-in-out placeholder:text-slate-400 bg-slate-50/50 hover:bg-white',
                'placeholder': 'John',
            }
        )
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm text-slate-800 transition duration-150 ease-in-out placeholder:text-slate-400 bg-slate-50/50 hover:bg-white',
                'placeholder': 'Doe',
            }
        )
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm text-slate-800 transition duration-150 ease-in-out placeholder:text-slate-400 bg-slate-50/50 hover:bg-white',
                'placeholder': 'john.doe@example.com',
            }
        )
    )
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        required=False,
        widget=forms.Select(
            attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm text-slate-800 transition duration-150 ease-in-out bg-slate-50/50 hover:bg-white',
            }
        )
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['username', 'password']:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm text-slate-800 transition duration-150 ease-in-out placeholder:text-slate-400 bg-slate-50/50 hover:bg-white'
                })
        if 'password' in self.fields:
            self.fields['password'].widget.attrs.update({'placeholder': 'Create password'})
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm text-slate-800 transition duration-150 ease-in-out placeholder:text-slate-400 bg-slate-50/50 hover:bg-white',
                'placeholder': 'Confirm password'
            })
