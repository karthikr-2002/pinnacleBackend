from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required(login_url='users:login')
def dashboard_view(request):
    stats = [
        {
            'name': 'Events',
            'value': '696',
            'bg_color': 'bg-rose-50',
            'text_color': 'text-rose-500',
            'icon_bg': 'bg-rose-100',
            'icon': 'award',
        },
        {
            'name': 'Reports',
            'value': '59',
            'bg_color': 'bg-sky-50',
            'text_color': 'text-sky-500',
            'icon_bg': 'bg-sky-100',
            'icon': 'diagram-project',
        },
        {
            'name': 'Employees',
            'value': '96',
            'bg_color': 'bg-purple-50',
            'text_color': 'text-purple-600',
            'icon_bg': 'bg-purple-100',
            'icon': 'user-tie',
        },
    ]

    context = {
        'stats': stats,
        'user_name': request.user.first_name or request.user.username,
        'page_title': 'Modern Dashboard',
        'active_menu': 'modern',
        'revenue_total': '$36,358',
        'growth_rate': '+9%',
    }
    return render(request, 'dashboard/index.html', context)
