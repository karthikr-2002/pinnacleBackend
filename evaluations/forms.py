from django import forms
from django.utils import timezone
from .models import Unit, EvaluationTemplate, Question, Evaluation


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ('name', 'place')
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
                'placeholder': 'Enter each question on a new line...',
            }
        ),
        required=False,
        help_text="Enter questions or use the dynamic questions builder below."
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
    all_units = forms.BooleanField(required=False, initial=True)
    selected_units = forms.ModelMultipleChoiceField(
        queryset=Unit.objects.all(),
        required=False
    )
    start_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-[#5D87FF]/20 focus:border-[#5D87FF] bg-slate-50/50',
            }
        ),
        required=True,
        initial=timezone.now().date,
        help_text="Evaluation becomes active and appears for staff on this date."
    )
    end_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:ring-2 focus:ring-[#5D87FF]/20 focus:border-[#5D87FF] bg-slate-50/50',
            }
        ),
        required=False,
        help_text="Target closing deadline for display purposes."
    )

    class Meta:
        model = Evaluation
        fields = ('title', 'description', 'template', 'start_date', 'end_date', 'status')
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

    def clean(self):
        cleaned_data = super().clean()
        all_units_checked = cleaned_data.get('all_units')
        chosen_units = cleaned_data.get('selected_units')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', 'End date cannot be earlier than start date.')

        if all_units_checked:
            cleaned_data['final_units'] = list(Unit.objects.all())
        elif chosen_units and chosen_units.exists():
            cleaned_data['final_units'] = list(chosen_units)
        else:
            self.add_error('selected_units', 'Please select at least one care unit.')
            cleaned_data['final_units'] = []

        return cleaned_data


    def save(self, commit=True):
        evaluation = super().save(commit=commit)
        def save_m2m():
            final_units = self.cleaned_data.get('final_units', [])
            evaluation.units.set(final_units)
        if commit:
            save_m2m()
        else:
            self.save_m2m = save_m2m
        return evaluation

