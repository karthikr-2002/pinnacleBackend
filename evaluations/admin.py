from django.contrib import admin
from .models import Unit, EvaluationTemplate, Question, Evaluation, EvaluationSubmission, Rating


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    fields = (
        ('order', 'question_text'),
        ('label_0', 'label_1'),
        ('label_2', 'label_3'),
        ('label_4', 'label_5'),
    )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('template', 'order', 'question_text', 'label_0', 'label_5')
    list_filter = ('template',)
    search_fields = ('question_text',)
    fields = ('template', 'order', 'question_text', 'label_0', 'label_1', 'label_2', 'label_3', 'label_4', 'label_5')


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'place', 'total_employees', 'created_at')
    search_fields = ('name', 'place')
    filter_horizontal = ('users',)


@admin.register(EvaluationTemplate)
class EvaluationTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'questions_count', 'created_by', 'created_at')
    search_fields = ('title', 'description')
    inlines = [QuestionInline]


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('title', 'template', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'template', 'units')
    search_fields = ('title', 'description')
    filter_horizontal = ('units', 'users')


class RatingInline(admin.TabularInline):
    model = Rating
    extra = 0
    readonly_fields = ('question', 'score', 'score_label', 'comment')
    can_delete = False


@admin.register(EvaluationSubmission)
class EvaluationSubmissionAdmin(admin.ModelAdmin):
    list_display = ('evaluation', 'evaluator', 'evaluatee', 'unit', 'average_score', 'submitted_at')
    list_filter = ('evaluation', 'unit', 'submitted_at')
    search_fields = (
        'evaluator__username', 'evaluatee__username',
        'evaluator__first_name', 'evaluatee__first_name',
        'evaluation__title'
    )
    inlines = [RatingInline]
    readonly_fields = ('evaluation', 'evaluator', 'evaluatee', 'unit', 'submitted_at')
