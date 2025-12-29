from django.db import models
from django.contrib.auth.models import User

class MealLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meal_name = models.CharField(max_length=100)
    meal_type = models.CharField(max_length=20, default='Other')

    calories = models.FloatField()
    protein_g = models.FloatField()
    fat_g = models.FloatField()
    carbs_g = models.FloatField()
    fiber_g = models.FloatField()

    # JSON blob of items: [{"food":..., "grams":..., "nutrition":{...}}, ...]
    items_json = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.meal_name} - {self.created_at}"
