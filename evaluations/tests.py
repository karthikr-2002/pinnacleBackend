from django.test import TestCase, Client
from django.urls import reverse
from users.models import User
from evaluations.models import Unit, EvaluationTemplate, Question, Evaluation, EvaluationSubmission, Rating


class EvaluationSystemTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Admin user
        self.admin = User.objects.create_superuser(
            username='superadmin',
            email='admin@care.com',
            password='Password123!',
            role='admin'
        )

        # 5 Staff members in Sunrise Wing
        self.staff1 = User.objects.create_user(
            username='nurse_sarah', email='sarah@care.com', password='Password123!',
            role='user', first_name='Sarah', last_name='Jenkins'
        )
        self.staff2 = User.objects.create_user(
            username='doctor_alex', email='alex@care.com', password='Password123!',
            role='user', first_name='Alex', last_name='Smith'
        )
        self.staff3 = User.objects.create_user(
            username='carer_maria', email='maria@care.com', password='Password123!',
            role='user', first_name='Maria', last_name='Garcia'
        )
        self.staff4 = User.objects.create_user(
            username='nurse_david', email='david@care.com', password='Password123!',
            role='user', first_name='David', last_name='Chen'
        )
        self.staff5 = User.objects.create_user(
            username='carer_emma', email='emma@care.com', password='Password123!',
            role='user', first_name='Emma', last_name='Wilson'
        )

        # Care Units
        self.unit_sunrise = Unit.objects.create(name='Sunrise Wing', place='Building A')
        self.unit_sunrise.users.add(self.staff1, self.staff2, self.staff3, self.staff4, self.staff5)

        # Template with multiple questions
        self.template = EvaluationTemplate.objects.create(
            title='Clinical Care & Safety Standards',
            description='Standard template',
            created_by=self.admin
        )
        self.q1 = Question.objects.create(template=self.template, question_text='Infection control protocols', order=1)
        self.q2 = Question.objects.create(template=self.template, question_text='Response to resident calls', order=2)
        self.q3 = Question.objects.create(template=self.template, question_text='Documentation accuracy', order=3)

        # Evaluation tagged to unit_sunrise
        self.evaluation = Evaluation.objects.create(
            title='October Safety Audit',
            template=self.template,
            status='active',
            created_by=self.admin
        )
        self.evaluation.units.add(self.unit_sunrise)

    def test_single_template_can_be_used_by_multiple_evaluations(self):
        eval2 = Evaluation.objects.create(
            title='November Safety Audit',
            template=self.template,
            status='active',
            created_by=self.admin
        )
        self.assertEqual(self.evaluation.template, self.template)
        self.assertEqual(eval2.template, self.template)
        self.assertEqual(self.template.evaluations.count(), 2)
        self.assertEqual(self.template.questions.count(), 3)

    def test_admin_create_unit_does_not_assign_staff(self):
        self.client.login(username='superadmin', password='Password123!')
        response = self.client.get(reverse('evaluations:unit_create'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Assign Employees')
        self.assertNotContains(response, 'Specific Staff')

        response = self.client.post(reverse('evaluations:unit_create'), {
            'name': 'Moonlight Ward',
            'place': 'Building D',
            'all_employees': 'true',
            'users': [self.staff1.id, self.staff2.id],
        })
        self.assertEqual(response.status_code, 302)
        unit = Unit.objects.get(name='Moonlight Ward')
        self.assertEqual(unit.users.count(), 0)
        self.assertTrue(self.unit_sunrise.users.filter(id=self.staff1.id).exists())

    def test_admin_can_view_unit_employees_and_edit_unit(self):
        self.client.login(username='superadmin', password='Password123!')
        list_res = self.client.get(reverse('evaluations:unit_list'))
        self.assertEqual(list_res.status_code, 200)
        self.assertContains(list_res, 'Sunrise Wing')
        self.assertContains(list_res, 'Edit')

        detail_res = self.client.get(reverse('evaluations:unit_detail', args=[self.unit_sunrise.id]))
        self.assertEqual(detail_res.status_code, 200)
        self.assertContains(detail_res, 'Sarah Jenkins')
        self.assertContains(detail_res, 'Edit Care Unit')

        edit_res = self.client.post(reverse('evaluations:unit_edit', args=[self.unit_sunrise.id]), {
            'name': 'Sunrise Wing West',
            'place': 'Building A - Level 3',
        })
        self.assertEqual(edit_res.status_code, 302)
        self.unit_sunrise.refresh_from_db()
        self.assertEqual(self.unit_sunrise.name, 'Sunrise Wing West')
        self.assertEqual(self.unit_sunrise.place, 'Building A - Level 3')

    def test_admin_can_create_evaluation(self):
        self.client.login(username='superadmin', password='Password123!')
        response = self.client.post(reverse('evaluations:evaluation_create'), {
            'title': 'Q4 Clinical Review',
            'description': 'Quarterly review',
            'template': self.template.id,
            'units': [self.unit_sunrise.id],
            'status': 'active',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Evaluation.objects.filter(title='Q4 Clinical Review').exists())

    def test_regular_user_cannot_access_admin_evaluation_views(self):
        self.client.login(username='nurse_sarah', password='Password123!')
        # Cannot access create evaluation
        res = self.client.get(reverse('evaluations:evaluation_create'))
        self.assertEqual(res.status_code, 403)
        # Cannot access admin submissions list
        res_sub = self.client.get(reverse('evaluations:admin_submissions_list'))
        self.assertEqual(res_sub.status_code, 403)

    def test_peer_evaluation_logic_5_users_unit(self):
        """
        When 1 unit has 5 employees, 1 employee evaluates the other 4 employees
        and submits 4 evaluations.
        """
        self.client.login(username='nurse_sarah', password='Password123!')

        # Check employee evaluations list: Sarah sees other 4 colleagues to evaluate
        response = self.client.get(reverse('evaluations:user_evaluations'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'October Safety Audit')
        self.assertContains(response, 'Alex Smith')
        self.assertContains(response, 'Maria Garcia')
        self.assertContains(response, 'David Chen')
        self.assertContains(response, 'Emma Wilson')

        # 1. Sarah evaluates Alex
        res1 = self.client.post(reverse('evaluations:evaluation_rate', args=[self.evaluation.id, self.staff2.id]), {
            f'rating_{self.q1.id}': '5',
            f'rating_{self.q2.id}': '4',
            f'rating_{self.q3.id}': '5',
            'feedback': 'Great clinical teamwork from Alex.',
        })
        self.assertEqual(res1.status_code, 302)

        # 2. Sarah evaluates Maria
        res2 = self.client.post(reverse('evaluations:evaluation_rate', args=[self.evaluation.id, self.staff3.id]), {
            f'rating_{self.q1.id}': '4',
            f'rating_{self.q2.id}': '4',
            f'rating_{self.q3.id}': '4',
            'feedback': 'Prompt response to alarms.',
        })
        self.assertEqual(res2.status_code, 302)

        # 3. Sarah evaluates David
        res3 = self.client.post(reverse('evaluations:evaluation_rate', args=[self.evaluation.id, self.staff4.id]), {
            f'rating_{self.q1.id}': '3',
            f'rating_{self.q2.id}': '4',
            f'rating_{self.q3.id}': '5',
            'feedback': 'Excellent documentation.',
        })
        self.assertEqual(res3.status_code, 302)

        # 4. Sarah evaluates Emma
        res4 = self.client.post(reverse('evaluations:evaluation_rate', args=[self.evaluation.id, self.staff5.id]), {
            f'rating_{self.q1.id}': '5',
            f'rating_{self.q2.id}': '5',
            f'rating_{self.q3.id}': '5',
            'feedback': 'Outstanding care and hygiene standards.',
        })
        self.assertEqual(res4.status_code, 302)

        # Verify Sarah has submitted 4 peer evaluations
        sarah_submissions = EvaluationSubmission.objects.filter(evaluator=self.staff1, evaluation=self.evaluation)
        self.assertEqual(sarah_submissions.count(), 4)

        # Verify evaluatees are staff2, staff3, staff4, staff5
        evaluatee_ids = set(sarah_submissions.values_list('evaluatee_id', flat=True))
        self.assertEqual(evaluatee_ids, {self.staff2.id, self.staff3.id, self.staff4.id, self.staff5.id})

        # Sarah cannot evaluate herself
        self_res = self.client.post(reverse('evaluations:evaluation_rate', args=[self.evaluation.id, self.staff1.id]), {
            f'rating_{self.q1.id}': '5',
        })
        self.assertEqual(self_res.status_code, 302)

        # Sarah cannot evaluate Alex twice
        alex_twice_res = self.client.get(reverse('evaluations:evaluation_rate', args=[self.evaluation.id, self.staff2.id]))
        self.assertEqual(alex_twice_res.status_code, 302)

        # History records all 4 submissions
        history_res = self.client.get(reverse('evaluations:user_history'))
        self.assertEqual(history_res.status_code, 200)
        self.assertContains(history_res, 'Alex Smith')
        self.assertContains(history_res, 'Maria Garcia')
        self.assertContains(history_res, 'David Chen')
        self.assertContains(history_res, 'Emma Wilson')

    def test_user_cannot_view_other_users_submission_detail(self):
        # Submission by staff1 for staff2
        submission = EvaluationSubmission.objects.create(
            evaluation=self.evaluation,
            evaluator=self.staff1,
            evaluatee=self.staff2,
            unit=self.unit_sunrise,
            feedback='Confidential feedback'
        )
        Rating.objects.create(submission=submission, question=self.q1, score=5)

        # Login as staff3 (different user)
        self.client.login(username='carer_maria', password='Password123!')
        res = self.client.get(reverse('evaluations:user_history_detail', args=[submission.id]))
        self.assertEqual(res.status_code, 404)  # Cannot see another user's submission

        # Admin CAN see submission
        self.client.login(username='superadmin', password='Password123!')
        admin_res = self.client.get(reverse('evaluations:admin_submission_detail', args=[submission.id]))
        self.assertEqual(admin_res.status_code, 200)
        self.assertContains(admin_res, 'Confidential feedback')

    def test_dynamic_rating_labels_per_question(self):
        custom_q = Question.objects.create(
            template=self.template,
            question_text='Audit Frequency Compliance',
            order=4,
            label_0='Never Done',
            label_1='Rarely (<1/mo)',
            label_2='Monthly',
            label_3='Bi-Weekly',
            label_4='Weekly',
            label_5='Daily Completed'
        )

        choices = custom_q.choices
        self.assertEqual(len(choices), 6)
        self.assertEqual(choices[0], (0, 'Never Done'))
        self.assertEqual(choices[5], (5, 'Daily Completed'))

        custom_q2 = Question.objects.create(
            template=self.template,
            question_text='Hygiene Protocol Adherence',
            order=5,
            label_0='Critical Non-Compliance',
            label_1='Major Deficiencies',
            label_2='Minor Issues',
            label_3='Satisfactory',
            label_4='High Standard',
            label_5='Exemplary Standards'
        )

        submission = EvaluationSubmission.objects.create(
            evaluation=self.evaluation,
            evaluator=self.staff1,
            evaluatee=self.staff2,
            unit=self.unit_sunrise
        )
        r0 = Rating.objects.create(submission=submission, question=custom_q, score=0)
        r5 = Rating.objects.create(submission=submission, question=custom_q2, score=5)

        self.assertEqual(r0.score_label, 'Never Done')
        self.assertEqual(r5.score_label, 'Exemplary Standards')
