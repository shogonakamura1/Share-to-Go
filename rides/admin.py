from django.contrib import admin
from .models import RidePlan, Participation, Group, GroupMembership

# Register your models here.

@admin.register(RidePlan)
class RidePlanAdmin(admin.ModelAdmin):
    list_display = ['title', 'creator', 'departure_location', 'destination', 'departure_time', 'max_participants', 'status', 'created_at']
    list_filter = ['status', 'departure_time', 'created_at']
    search_fields = ['title', 'description', 'departure_location', 'destination']
    date_hierarchy = 'departure_time'
    
    fieldsets = (
        ('基本情報', {
            'fields': ('creator', 'title', 'description')
        }),
        ('行程情報', {
            'fields': ('departure_location', 'destination', 'departure_time')
        }),
        ('設定', {
            'fields': ('max_participants', 'price_per_person', 'status')
        }),
        ('日時', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at']

@admin.register(Participation)
class ParticipationAdmin(admin.ModelAdmin):
    list_display = ['user', 'ride_plan', 'pickup_location_name', 'dropoff_location_name', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'ride_plan__title', 'pickup_location_name', 'dropoff_location_name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('参加情報', {
            'fields': ('user', 'ride_plan', 'status')
        }),
        ('乗車場所', {
            'fields': ('pickup_location_name', 'pickup_latitude', 'pickup_longitude')
        }),
        ('降車場所', {
            'fields': ('dropoff_location_name', 'dropoff_latitude', 'dropoff_longitude')
        }),
        ('日時', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'creator', 'created_at']
    list_filter = ['created_at']
    search_fields = ['display_name', 'name', 'creator__username']
    readonly_fields = ['name', 'password', 'created_at']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('display_name', 'creator')
        }),
        ('自動生成情報', {
            'fields': ('name', 'password'),
            'classes': ('collapse',)
        }),
        ('日時', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'group', 'joined_at']
    list_filter = ['joined_at', 'group']
    search_fields = ['user__username', 'group__display_name']
    readonly_fields = ['joined_at']
