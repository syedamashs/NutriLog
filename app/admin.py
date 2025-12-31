from django.contrib import admin

# Register your models here.
from .models import MealLog, Profile, Recipe, Nutrition

admin.site.register(MealLog)
admin.site.register(Recipe)
admin.site.register(Nutrition)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'sex', 'age', 'height_cm', 'weight_kg', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
