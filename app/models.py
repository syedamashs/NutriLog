from django.db import models
from django.contrib.auth.models import User

# MealLog_Model
class MealLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meal_name = models.CharField(max_length=100)
    meal_type = models.CharField(max_length=20, default='Other')

    calories = models.FloatField()
    protein_g = models.FloatField()
    fat_g = models.FloatField()
    carbs_g = models.FloatField()
    fiber_g = models.FloatField()
    items_json = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    running_calories = models.FloatField(default=0)
    day_goal_achieved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.meal_name} - {self.created_at}"


# Profile_Model
class Profile(models.Model):
    SEX_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    height_cm = models.FloatField(null=True, blank=True)
    weight_kg = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def bmi(self):
        """Return BMI rounded to 1 decimal place or None if insufficient data."""
        if self.height_cm and self.weight_kg:
            h = self.height_cm / 100.0
            try:
                return round(self.weight_kg / (h * h), 1)
            except Exception:
                return None
        return None

    @property
    def bmi_category(self):
        b = self.bmi()
        if b is None:
            return None
        if b < 18.5:
            return 'Underweight'
        if b < 25:
            return 'Normal'
        if b < 30:
            return 'Overweight'
        return 'Obese'

    def ideal_weight_kg(self, target_bmi=22.0):
        """Return ideal weight for the given target BMI (default 22)."""
        if not self.height_cm:
            return None
        h = self.height_cm / 100.0
        return round(target_bmi * (h * h), 1)

    def bmr(self):
        """Estimate BMR using Mifflin-St Jeor formula. Returns int or None."""
        if not (self.age and self.height_cm and self.weight_kg):
            return None
        try:
            w = self.weight_kg
            h = self.height_cm
            a = self.age
            if self.sex == 'M':
                val = 10*w + 6.25*h - 5*a + 5
            elif self.sex == 'F':
                val = 10*w + 6.25*h - 5*a - 161
            else:
                # If sex unknown/other, return average of Male and Female formulas
                v_m = 10*w + 6.25*h - 5*a + 5
                v_f = 10*w + 6.25*h - 5*a - 161
                val = (v_m + v_f) / 2.0
            return int(round(val))
        except Exception:
            return None

    def __str__(self):
        return f"{self.user.username} Profile"


# Ensure a Profile exists for every User
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        Profile.objects.get_or_create(user=instance)
