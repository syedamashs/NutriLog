from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Profile, MealLog

class ProfileModelTests(TestCase):
    def test_bmi_bmr_and_ideal(self):
        u = User.objects.create_user(username='tuser', password='pw')
        p = Profile.objects.get(user=u)
        p.age = 30
        p.height_cm = 180.0
        p.weight_kg = 75.0
        p.sex = 'M'
        p.save()
        self.assertAlmostEqual(p.bmi(), 23.1)
        self.assertEqual(p.bmr(), 1730)
        self.assertAlmostEqual(p.ideal_weight_kg(), 71.3)

class RegistrationTests(TestCase):
    def test_registration_saves_profile_fields(self):
        url = reverse('register') if 'register' in [p.name for p in []] else '/register/'
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'pass1234',
            'password2': 'pass1234',
            'age': '28',
            'height_cm': '170',
            'weight_kg': '68.5',
            'sex': 'F'
        }
        resp = self.client.post('/register/', data)
        # registration should redirect to login
        self.assertEqual(resp.status_code, 302)
        u = User.objects.get(username='newuser')
        p = u.profile
        self.assertEqual(p.age, 28)
        self.assertEqual(p.sex, 'F')
        self.assertAlmostEqual(p.height_cm, 170.0)
        self.assertAlmostEqual(p.weight_kg, 68.5)

class ProfileUpdateTests(TestCase):
    def test_profile_update_saves_sex_and_values(self):
        u = User.objects.create_user(username='upuser', password='pw')
        # ensure profile created
        p = u.profile
        self.client.login(username='upuser', password='pw')
        data = {
            'username': 'upuser',
            'email': 'up@example.com',
            'age': '35',
            'height_cm': '165',
            'weight_kg': '60',
            'sex': 'F'
        }
        resp = self.client.post('/profile/', data)
        # redirect back to profile
        self.assertIn(resp.status_code, (302, 301))
        p.refresh_from_db()
        self.assertEqual(p.sex, 'F')
        self.assertEqual(p.age, 35)
        self.assertAlmostEqual(p.height_cm, 165.0)
        self.assertAlmostEqual(p.weight_kg, 60.0)

class HistoryGoalTests(TestCase):
    def test_history_uses_profile_bmr_as_goal(self):
        u = User.objects.create_user(username='guser', password='pw')
        p = u.profile
        # set values to produce known BMR
        p.age = 40
        p.height_cm = 175
        p.weight_kg = 80
        p.sex = 'M'
        p.save()
        self.client.login(username='guser', password='pw')
        resp = self.client.get('/history/')
        self.assertEqual(resp.status_code, 200)
        # context goal should be present and equal to profile.bmr()
        self.assertIn('goal', resp.context)
        self.assertEqual(resp.context['goal'], int(p.bmr()))
        # profile BMR and TDEE suggestion propagated
        self.assertIn('profile_bmr', resp.context)
        self.assertEqual(resp.context['profile_bmr'], p.bmr())
        self.assertIn('tdee_suggestion', resp.context)
        self.assertEqual(resp.context['tdee_suggestion'], int(round(p.bmr() * 1.2)))

    def test_day_goal_flag_and_hit_rate(self):
        # user with BMR-based goal
        u = User.objects.create_user(username='achuser', password='pw')
        p = u.profile
        p.age = 30
        p.height_cm = 175
        p.weight_kg = 70
        p.sex = 'M'
        p.save()
        goal = int(p.bmr())

        from zoneinfo import ZoneInfo
        tz = ZoneInfo('Asia/Kolkata')
        from django.utils import timezone
        from datetime import timedelta
        # create logs for 7-day range (days 0..6 from today)
        today = timezone.localtime(timezone.now(), tz).date()
        # day indices: 0..6
        # hits on days 0,3,4
        def create_day_log(day_index, calories):
            d = today - timezone.timedelta(days=day_index)
            dt = timezone.datetime(d.year, d.month, d.day, 12, 0, 0, tzinfo=tz)
            m = MealLog.objects.create(user=u, meal_name=f'd{day_index}', meal_type='Other', calories=calories, protein_g=10, fat_g=10, carbs_g=10, fiber_g=1)
            # ensure created_at matches our intended local date (auto_now_add overrides on create), use update
            MealLog.objects.filter(pk=m.pk).update(created_at=dt)

        create_day_log(0, goal+50)
        create_day_log(1, goal-50)
        # day 2: no logs
        create_day_log(3, goal)
        create_day_log(4, goal+10)

        # recompute day flags for the affected days
        from .views import recompute_day_goal_for_date        # quick DB sanity check: ensure the created logs show up in per-day aggregation
        from django.db.models import Sum
        day_totals = {}
        for i in range(0,7):
            d = today - timezone.timedelta(days=i)
            day_start = timezone.datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=tz)
            day_end = day_start + timezone.timedelta(days=1)
            total = MealLog.objects.filter(user=u, created_at__gte=day_start, created_at__lt=day_end).aggregate(total=Sum('calories'))['total'] or 0
            day_totals[i] = total
        # check totals for days 0,3,4
        self.assertGreater(day_totals[0], 0)
        self.assertGreater(day_totals[3], 0)
        self.assertGreater(day_totals[4], 0)
        # recompute for last 7 days and validate the recompute is marking days correctly
        hits = []
        for i in range(0,7):
            d = today - timezone.timedelta(days=i)
            res = recompute_day_goal_for_date(u, d)
            hits.append((i, res))

        # expected hits at days 0,3,4
        hit_days = [i for i, ok in hits if ok]
        self.assertCountEqual(hit_days, [0,3,4])
    def test_running_calories_and_flag_propagation(self):
        u = User.objects.create_user(username='rcuser', password='pw')
        p = u.profile
        p.age = 30
        p.height_cm = 175
        p.weight_kg = 70
        p.sex = 'M'
        p.save()
        goal = int(p.bmr())

        from zoneinfo import ZoneInfo
        tz = ZoneInfo('Asia/Kolkata')
        from django.utils import timezone
        from datetime import timedelta
        today = timezone.localtime(timezone.now(), tz).date()
        # create two logs in same day: first below goal, second pushes over goal
        def make(dt_cal):
            m = MealLog.objects.create(user=u, meal_name='x', meal_type='Other', calories=dt_cal, protein_g=5, fat_g=5, carbs_g=5, fiber_g=1)
            return m
        # first log 100, second log goal
        m1 = make(100)
        MealLog.objects.filter(pk=m1.pk).update(created_at=timezone.datetime(today.year, today.month, today.day, 9, 0, 0, tzinfo=tz))
        m2 = make(goal)
        MealLog.objects.filter(pk=m2.pk).update(created_at=timezone.datetime(today.year, today.month, today.day, 12, 0, 0, tzinfo=tz))

        # recompute for today
        from .views import recompute_day_goal_for_date
        recompute_day_goal_for_date(u, today)

        m1.refresh_from_db()
        m2.refresh_from_db()
        self.assertEqual(m1.running_calories, 100)
        # second entry running total = 100 + goal, exceeds goal -> should be marked achieved
        self.assertAlmostEqual(m2.running_calories, round(100 + goal, 2))
        self.assertFalse(m1.day_goal_achieved)
        self.assertTrue(m2.day_goal_achieved)
        # now hit-rate should be 100% (days-with-data basis: only today's logged day is achieved)
        self.client.login(username='rcuser', password='pw')
        resp = self.client.get('/history/?days=7')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('goal_hit_rate', resp.context)
        self.assertAlmostEqual(resp.context['goal_hit_rate'], round(1/1*100,1))

    def test_history_view_triggers_recompute(self):
        u = User.objects.create_user(username='rtuser', password='pw')
        p = u.profile
        p.age = 30
        p.height_cm = 170
        p.weight_kg = 70
        p.sex = 'M'
        p.save()
        goal = int(p.bmr())

        from zoneinfo import ZoneInfo
        tz = ZoneInfo('Asia/Kolkata')
        from django.utils import timezone
        today = timezone.localtime(timezone.now(), tz).date()

        m1 = MealLog.objects.create(user=u, meal_name='a', meal_type='Other', calories=100, protein_g=5, fat_g=5, carbs_g=5, fiber_g=1)
        MealLog.objects.filter(pk=m1.pk).update(created_at=timezone.datetime(today.year, today.month, today.day, 9, 0, 0, tzinfo=tz))
        m2 = MealLog.objects.create(user=u, meal_name='b', meal_type='Other', calories=goal, protein_g=5, fat_g=5, carbs_g=5, fiber_g=1)
        MealLog.objects.filter(pk=m2.pk).update(created_at=timezone.datetime(today.year, today.month, today.day, 12, 0, 0, tzinfo=tz))

        # before viewing history the running_calories should still be the default 0 (no recompute happened)
        m1.refresh_from_db(); m2.refresh_from_db()
        self.assertEqual(m1.running_calories, 0)
        self.assertEqual(m2.running_calories, 0)

        # viewing history should trigger recompute for that date and update running_calories
        self.client.login(username='rtuser', password='pw')
        resp = self.client.get('/history/?days=7')
        self.assertEqual(resp.status_code, 200)
        m1.refresh_from_db(); m2.refresh_from_db()
        self.assertNotEqual(m1.running_calories, 0)
        self.assertNotEqual(m2.running_calories, 0)

