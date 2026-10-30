import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone
from evaluations.models import Unit, EvaluationTemplate, Evaluation, EvaluationSubmission


@login_required(login_url='users:login')
def dashboard_view(request):
    user = request.user
    is_admin = user.is_superuser or getattr(user, 'role', '') == 'admin'
    User = get_user_model()

    if is_admin:
        total_evaluations = Evaluation.objects.count()
        total_submissions = EvaluationSubmission.objects.count()
        total_units = Unit.objects.count()
        total_staff = User.objects.count()

        # Dynamic Status breakdown
        evaluations_all = list(Evaluation.objects.all())
        completed_evals = 0
        in_progress_evals = 0
        not_started_evals = 0
        for ev in evaluations_all:
            st = ev.get_dynamic_status()
            if st == 'completed':
                completed_evals += 1
            elif st == 'in_progress':
                in_progress_evals += 1
            else:
                not_started_evals += 1

        # Care Unit Submissions Bar Chart (Top units with recorded reviews)
        units_with_subs = list(
            Unit.objects.annotate(
                subs_count=Count('submissions', distinct=True),
                staff_count=Count('users', distinct=True)
            ).order_by('-subs_count')[:6]
        )
        unit_chart_labels = [u.name for u in units_with_subs if u.subs_count > 0]
        unit_chart_data = [u.subs_count for u in units_with_subs if u.subs_count > 0]
        if not unit_chart_labels:
            unit_chart_labels = [u.name for u in units_with_subs[:4]]
            unit_chart_data = [0 for _ in unit_chart_labels]

        # Evaluation Status Donut Chart series & labels
        status_series = [completed_evals, in_progress_evals, not_started_evals]
        status_labels = ['Completed', 'In Progress', 'Not Started']

        # Recent Evaluation Submissions (Live Activity Feed)
        recent_submissions = EvaluationSubmission.objects.select_related(
            'evaluator', 'evaluatee', 'unit', 'evaluation'
        ).order_by('-submitted_at')[:6]

        # Active / Running Evaluations with completion progress
        active_evaluations = []
        for ev in Evaluation.objects.select_related('template').prefetch_related('units__users', 'submissions').order_by('-created_at')[:5]:
            subs_count = ev.submissions.count()
            tot_expected = 0
            for un in ev.units.all():
                n = un.users.count()
                if n > 1:
                    tot_expected += n * (n - 1)
            pct = round((subs_count / tot_expected) * 100) if tot_expected > 0 else (100 if subs_count > 0 else 0)
            if pct > 100:
                pct = 100
            active_evaluations.append({
                'id': ev.id,
                'title': ev.title,
                'template_title': ev.template.title if ev.template else '',
                'units_count': ev.units.count(),
                'subs_count': subs_count,
                'expected_count': tot_expected,
                'progress_pct': pct,
                'status_code': ev.get_dynamic_status(),
                'status_display': ev.get_dynamic_status_display(),
            })

        # Care Units Quick Leaderboard
        care_units_list = units_with_subs[:5]

        context = {
            'is_admin': True,
            'page_title': 'Home',
            'active_menu': 'modern',
            'user_name': user.get_full_name() or user.username,
            'total_evaluations': total_evaluations,
            'total_submissions': total_submissions,
            'total_units': total_units,
            'total_staff': total_staff,
            'completed_evals': completed_evals,
            'in_progress_evals': in_progress_evals,
            'not_started_evals': not_started_evals,
            'unit_chart_labels_json': json.dumps(unit_chart_labels),
            'unit_chart_data_json': json.dumps(unit_chart_data),
            'status_series_json': json.dumps(status_series),
            'status_labels_json': json.dumps(status_labels),
            'recent_submissions': recent_submissions,
            'active_evaluations': active_evaluations,
            'care_units_list': care_units_list,
        }
    else:
        # Non-admin Care Staff view
        today = timezone.now().date()
        user_units = list(user.assigned_units.prefetch_related('users').all())
        available_evals = Evaluation.objects.filter(
            units__in=user_units,
            start_date__lte=today,
            status__in=['not_started', 'in_progress', 'active']
        ).distinct().select_related('template')

        in_progress_evals_count = 0
        not_started_evals_count = 0
        completed_evals_count = 0

        for ev in available_evals:
            done, total = ev.get_user_progress(user)
            is_done = (done == total and total > 0)
            if is_done:
                completed_evals_count += 1
            elif done > 0:
                in_progress_evals_count += 1
            else:
                not_started_evals_count += 1

        total_pending_evals = in_progress_evals_count + not_started_evals_count

        context = {
            'is_admin': False,
            'page_title': 'Home',
            'active_menu': 'modern',
            'user_name': user.get_full_name() or user.username,
            'user_units': user_units,
            'assigned_units_count': len(user_units),
            'total_pending_evals': total_pending_evals,
            'in_progress_evals_count': in_progress_evals_count,
            'not_started_evals_count': not_started_evals_count,
            'completed_evals_count': completed_evals_count,
        }

    return render(request, 'dashboard/index.html', context)
