from django import forms
from .models import Unit, EvaluationTemplate, Question, Evaluation
from users.models import User


class UnitForm(forms.ModelForm):
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-[#5D87FF]/20 focus:border-[#5D87FF] bg-slate-50/50 min-h-[140px]',
            }
        ),
        help_text="Select employees assigned to this care unit (hold Ctrl/Cmd to select multiple)"
    )

    class Meta:
        model = Unit
        fields = ('name', 'place', 'users')
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-[#5D87FF]/20 focus:border-[#5D87FF] bg-slate-50/50',
                    'placeholder': 'e.g. Sunrise Care Wing',
                }
            ),
            'place': forms.TextInput(
                attrs={
                    'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-[#5D87FF]/20 focus:border-[#5D87FF] bg-slate-50/50',
                    'placeholder': 'e.g. Building A - Level 2',
                }
            ),
        }


class EvaluationTemplateForm(forms.ModelForm):
    questions_input = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-[#5D87FF]/20 focus:border-[#5D87FF] bg-slate-50/50 min-h-[160px]',
                'placeholder': 'Enter each question on a new line, e.g.:\nHow effectively are infection control protocols followed?\nHow prompt is staff response to resident calls?\nHow thorough is handover documentation?',
            }
        ),
        required=True,
        help_text="Enter one evaluation question per line. Choices will automatically be rated from 0 to 5."
    )

    class Meta:
        model = EvaluationTemplate
        fields = ('title', 'description')
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-[#5D87FF]/20 focus:border-[#5D87FF] bg-slate-50/50',
                    'placeholder': 'e.g. Monthly Clinical Care & Safety Standards',
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-[#5D87FF]/20 focus:border-[#5D87FF] bg-slate-50/50 min-h-[90px]',
                    'placeholder': 'Brief description or guidelines for this template...',
                }
            ),
        }


class EvaluationForm(forms.ModelForm):
    units = forms.ModelMultipleChoiceField(
        queryset=Unit.objects.all(),
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-[#5D87FF]/20 focus:border-[#5D87FF] bg-slate-50/50 min-h-[120px]',
            }
        ),
        help_text="Select units to tag (employees in these units will be invited to evaluate)"
    )

    class Meta:
        model = Evaluation
        fields = ('title', 'description', 'template', 'units', 'status')
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-[#5D87FF]/20 focus:border-[#5D87FF] bg-slate-50/50',
                    'placeholder': 'e.g. October 2026 Monthly Care Unit Assessment',
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-[#5D87FF]/20 focus:border-[#5D87FF] bg-slate-50/50 min-h-[80px]',
                    'placeholder': 'Evaluation instructions or deadline notes...',
                }
            ),
            'template': forms.Select(
                attrs={
                    'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-[#5D87FF]/20 focus:border-[#5D87FF] bg-slate-50/50',
                }
            ),
            'status': forms.Select(
                attrs={
                    'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-[#5D87FF]/20 focus:border-[#5D87FF] bg-slate-50/50',
                }
            ),
        }
