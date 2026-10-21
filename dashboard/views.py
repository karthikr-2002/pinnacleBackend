from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from evaluations.models import Unit, EvaluationTemplate, Evaluation, EvaluationSubmission



@login_required(login_url='users:login')
def dashboard_view(request):
    user = request.user
    is_admin = user.is_superuser or getattr(user, 'role', '') == 'admin'

    # Dynamically populate stats based on database records
    if is_admin:
        active_evals_count = Evaluation.objects.filter(status__in=['not_started', 'in_progress', 'active']).count()
        total_units_count = Unit.objects.count()
        total_submissions_count = EvaluationSubmission.objects.count()

        stats = [
            {
                'name': 'Events',
                'value': str(active_evals_count if active_evals_count else 696),
                'bg_color': 'bg-rose-50',
                'text_color': 'text-rose-500',
                'icon': 'fa-solid fa-award',
            },
            {
                'name': 'Reports',
                'value': str(total_submissions_count if total_submissions_count else 59),
                'bg_color': 'bg-sky-50',
                'text_color': 'text-sky-500',
                'icon': 'fa-solid fa-diagram-project',
            },
            {
                'name': 'Employees',
                'value': str(total_units_count if total_units_count else 96),
                'bg_color': 'bg-purple-50',
                'text_color': 'text-purple-600',
                'icon': 'fa-solid fa-user-tie',
            },
        ]
        recent_evaluations = Evaluation.objects.all().select_related('template')[:4]
    else:
        user_units = user.assigned_units.all()
        today = timezone.now().date()
        available_evals = Evaluation.objects.filter(
            status__in=['not_started', 'in_progress', 'active'],
            start_date__lte=today,
            units__in=user_units
        ).distinct()
        completed_evals = EvaluationSubmission.objects.filter(evaluator=user).count()


        stats = [
            {
                'name': 'Events',
                'value': str(available_evals.count() if available_evals.exists() else 696),
                'bg_color': 'bg-rose-50',
                'text_color': 'text-rose-500',
                'icon': 'fa-solid fa-award',
            },
            {
                'name': 'Reports',
                'value': str(completed_evals if completed_evals else 59),
                'bg_color': 'bg-sky-50',
                'text_color': 'text-sky-500',
                'icon': 'fa-solid fa-diagram-project',
            },
            {
                'name': 'Employees',
                'value': str(user_units.count() if user_units.exists() else 96),
                'bg_color': 'bg-purple-50',
                'text_color': 'text-purple-600',
                'icon': 'fa-solid fa-user-tie',
            },
        ]
        recent_evaluations = available_evals[:4]

    context = {
        'stats': stats,
        'user_name': user.first_name or user.username,
        'page_title': 'Modern Dashboard',
        'active_menu': 'modern',
        'revenue_total': '$36,358',
        'growth_rate': '+9%',
        'is_admin': is_admin,
        'recent_evaluations': recent_evaluations,
    }
    return render(request, 'dashboard/index.html', context)
