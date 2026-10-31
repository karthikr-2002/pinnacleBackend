import re
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


INPUT_CLASS = (
    'w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm '
    'focus:ring-2 focus:ring-[#5D87FF]/20 focus:border-[#5D87FF] bg-slate-50/50'
)



def validate_password_complexity(password):
    """
    Validates password complexity:
    - At least 8 characters
    - At least one letter
    - At least one number
    - At least one special character
    """
    if not password:
        raise forms.ValidationError('Password is required.')

    missing = []
    if len(password) < 8:
        missing.append('at least 8 characters')
    if not re.search(r'[A-Za-z]', password):
        missing.append('at least one letter')
    if not re.search(r'\d', password):
        missing.append('at least one number (0-9)')
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?/~`]', password):
        missing.append('at least one special character (e.g. !@#$%^&*)')

    if missing:
        raise forms.ValidationError(
            f"Password must include: {', '.join(missing)}."
        )

class EmployeeCreateForm(forms.Form):
    full_name = forms.CharField(
        label='Employee Name',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'e.g. Sarah Jenkins',
            'autocomplete': 'name',
        }),
    )
    username = forms.CharField(
        label='Username',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'e.g. sarah.jenkins',
            'autocomplete': 'off',
        }),
    )
    employee_id = forms.CharField(
        label='Employee ID',
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'e.g. EMP-1042',
            'autocomplete': 'off',
        }),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'sarah.jenkins@pinnaclecare.com',
            'autocomplete': 'email',
        }),
    )
    photo = forms.ImageField(
        label='Photo',
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'block w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-[#5D87FF] hover:file:bg-blue-100',
            'accept': 'image/*',
        }),
    )
    password = forms.CharField(
        label='Password',
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Set a login password',
            'autocomplete': 'new-password',
        }),
    )
    phone = forms.CharField(
        label='Contact Number',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'e.g. +1 555 0100',
            'autocomplete': 'tel',
        }),
    )
    unit = forms.ModelChoiceField(
        label='Unit',
        queryset=None,
        empty_label='Select a care unit',
        widget=forms.Select(attrs={
            'class': INPUT_CLASS,
        }),
    )

    def __init__(self, *args, **kwargs):
        from evaluations.models import Unit
        super().__init__(*args, **kwargs)
        self.fields['unit'].queryset = Unit.objects.all().order_by('name')

    def clean_employee_id(self):
        employee_id = self.cleaned_data['employee_id'].strip()
        if User.objects.filter(employee_id__iexact=employee_id).exists():
            raise forms.ValidationError('An employee with this ID already exists.')
        return employee_id

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if not username:
            raise forms.ValidationError('Username is required.')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        validate_password_complexity(password)
        return password

    def clean_full_name(self):
        name = ' '.join(self.cleaned_data['full_name'].split())
        if len(name) < 2:
            raise forms.ValidationError('Please enter the employee name.')
        return name

    def save(self):
        full_name = self.cleaned_data['full_name']
        parts = full_name.split(' ', 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ''
        employee_id = self.cleaned_data['employee_id']
        username = self.cleaned_data['username']

        user = User(
            username=username,
            employee_id=employee_id,
            first_name=first_name,
            last_name=last_name,
            email=self.cleaned_data['email'],
            phone=self.cleaned_data['phone'],
            role='user',
            job_title='Care Staff',
            avatar_url='/static/images/default-avatar.png',
        )
        user.set_password(self.cleaned_data['password'])
        photo = self.cleaned_data.get('photo')
        if photo:
            user.photo = photo
        user.save()

        unit = self.cleaned_data['unit']
        unit.users.add(user)
        return user


def split_full_name(full_name):
    parts = full_name.split(' ', 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ''
    return first_name, last_name


class EmployeeEditForm(forms.Form):
    full_name = forms.CharField(
        label='Employee Name',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'e.g. Sarah Jenkins',
            'autocomplete': 'name',
        }),
    )
    username = forms.CharField(
        label='Username',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'e.g. sarah.jenkins',
            'autocomplete': 'off',
        }),
    )
    employee_id = forms.CharField(
        label='Employee ID',
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'e.g. EMP-1042',
            'autocomplete': 'off',
        }),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'sarah.jenkins@pinnaclecare.com',
            'autocomplete': 'email',
        }),
    )
    photo = forms.ImageField(
        label='Photo',
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'block w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-[#5D87FF] hover:file:bg-blue-100',
            'accept': 'image/*',
        }),
    )
    phone = forms.CharField(
        label='Contact Number',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'e.g. +1 555 0100',
            'autocomplete': 'tel',
        }),
    )
    unit = forms.ModelChoiceField(
        label='Unit',
        queryset=None,
        empty_label='Select a care unit',
        widget=forms.Select(attrs={
            'class': INPUT_CLASS,
        }),
    )

    def __init__(self, *args, instance=None, **kwargs):
        from evaluations.models import Unit
        self.instance = instance
        super().__init__(*args, **kwargs)
        self.fields['unit'].queryset = Unit.objects.all().order_by('name')
        if instance and not self.is_bound:
            self.fields['full_name'].initial = instance.get_full_name() or instance.username
            self.fields['username'].initial = instance.username
            self.fields['employee_id'].initial = instance.employee_id or ''
            self.fields['email'].initial = instance.email
            self.fields['phone'].initial = instance.phone or ''
            current_unit = instance.assigned_units.first()
            if current_unit:
                self.fields['unit'].initial = current_unit.pk

    def clean_employee_id(self):
        employee_id = self.cleaned_data['employee_id'].strip()
        qs = User.objects.filter(employee_id__iexact=employee_id)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('An employee with this ID already exists.')
        return employee_id

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if not username:
            raise forms.ValidationError('Username is required.')
        qs = User.objects.filter(username__iexact=username)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_full_name(self):
        name = ' '.join(self.cleaned_data['full_name'].split())
        if len(name) < 2:
            raise forms.ValidationError('Please enter the employee name.')
        return name

    def save(self):
        user = self.instance
        first_name, last_name = split_full_name(self.cleaned_data['full_name'])
        employee_id = self.cleaned_data['employee_id']
        username = self.cleaned_data['username']

        user.username = username
        user.employee_id = employee_id
        user.first_name = first_name
        user.last_name = last_name
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        photo = self.cleaned_data.get('photo')
        if photo:
            user.photo = photo
        user.save()

        unit = self.cleaned_data['unit']
        user.assigned_units.set([unit])
        return user



class EmployeeResetPasswordForm(forms.Form):
    new_password = forms.CharField(
        label='New Password',
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Minimum 8 characters',
            'autocomplete': 'new-password',
        }),
    )
    confirm_password = forms.CharField(
        label='Confirm Password',
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Re-enter new password',
            'autocomplete': 'new-password',
        }),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_password(self):
        password = self.cleaned_data.get('new_password')
        validate_password_complexity(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data

    def save(self):
        self.user.set_password(self.cleaned_data['new_password'])
        self.user.save()
        return self.user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'phone', 'photo')
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-[#5D87FF]/20 focus:border-[#5D87FF] bg-slate-50/50',
                'placeholder': 'name@pinnaclecare.com',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-[#5D87FF]/20 focus:border-[#5D87FF] bg-slate-50/50',
                'placeholder': '+44 7123 456789',
            }),
            'photo': forms.ClearableFileInput(attrs={
                'class': 'w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#5D87FF]/20 focus:border-[#5D87FF] bg-slate-50/50',
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if not email:
            raise forms.ValidationError('Email address is required.')
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class UserSelfPasswordChangeForm(forms.Form):
    current_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-[#5D87FF]/20 focus:border-[#5D87FF] bg-slate-50/50',
            'placeholder': 'Enter current password',
            'autocomplete': 'current-password',
        }),
    )
    new_password = forms.CharField(
        label='New Password',
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-[#5D87FF]/20 focus:border-[#5D87FF] bg-slate-50/50',
            'placeholder': 'Minimum 8 characters with letter, number & symbol',
            'autocomplete': 'new-password',
        }),
    )
    confirm_password = forms.CharField(
        label='Confirm New Password',
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-[#5D87FF]/20 focus:border-[#5D87FF] bg-slate-50/50',
            'placeholder': 'Re-enter new password',
            'autocomplete': 'new-password',
        }),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError('Current password is incorrect.')
        return current_password

    def clean_new_password(self):
        password = self.cleaned_data.get('new_password')
        validate_password_complexity(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('New passwords do not match.')
        return cleaned_data

    def save(self):
        self.user.set_password(self.cleaned_data['new_password'])
        self.user.save()
        return self.user

