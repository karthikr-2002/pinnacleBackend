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
        if User.objects.filter(username__iexact=employee_id).exists():
            raise forms.ValidationError('This Employee ID is already used as a login username.')
        return employee_id

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

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

        user = User(
            username=employee_id,
            employee_id=employee_id,
            first_name=first_name,
            last_name=last_name,
            email=self.cleaned_data['email'],
            phone=self.cleaned_data['phone'],
            role='user',
            job_title='Care Staff',
            avatar_url=f'https://api.dicebear.com/7.x/bottts/svg?seed={employee_id}',
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
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Leave blank to keep the current password',
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

    def __init__(self, *args, instance=None, **kwargs):
        from evaluations.models import Unit
        self.instance = instance
        super().__init__(*args, **kwargs)
        self.fields['unit'].queryset = Unit.objects.all().order_by('name')
        if instance and not self.is_bound:
            self.fields['full_name'].initial = instance.get_full_name() or instance.username
            self.fields['employee_id'].initial = instance.employee_id or instance.username
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
        username_qs = User.objects.filter(username__iexact=employee_id)
        if self.instance:
            username_qs = username_qs.exclude(pk=self.instance.pk)
        if username_qs.exists():
            raise forms.ValidationError('This Employee ID is already used as a login username.')
        return employee_id

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

        user.username = employee_id
        user.employee_id = employee_id
        user.first_name = first_name
        user.last_name = last_name
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])
        photo = self.cleaned_data.get('photo')
        if photo:
            user.photo = photo
        user.save()

        unit = self.cleaned_data['unit']
        user.assigned_units.set([unit])
        return user
