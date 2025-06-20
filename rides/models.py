from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class RidePlan(models.Model):
    """配車計画モデル"""
    STATUS_CHOICES = [
        ('active', '募集中'),
        ('full', '定員満員'),
        ('cancelled', 'キャンセル'),
        ('completed', '完了'),
    ]
    
    creator = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="作成者")
    title = models.CharField(max_length=100, verbose_name="タイトル")
    description = models.TextField(blank=True, null=True, verbose_name="説明")
    departure_location = models.CharField(max_length=100, verbose_name="出発地")
    destination = models.CharField(max_length=100, verbose_name="目的地")
    departure_time = models.DateTimeField(verbose_name="出発日時")
    deadline_time = models.DateTimeField(verbose_name="締切日時", blank=True, null=True)
    max_participants = models.PositiveIntegerField(verbose_name="最大参加者数", default=4)
    price_per_person = models.PositiveIntegerField(blank=True, null=True, verbose_name="一人あたりの料金")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="ステータス"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        verbose_name = "配車計画"
        verbose_name_plural = "配車計画"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def current_participants(self):
        """現在の参加者数を取得"""
        return self.participation_set.filter(status='confirmed').count()

    @property
    def is_full(self):
        """予約上限に達しているかどうか"""
        return self.current_participants >= self.max_participants

    @property
    def is_expired(self):
        """期限切れかどうか（出発日時を過ぎているか）"""
        return timezone.now() > self.departure_time

    @property
    def is_deadline_passed(self):
        """締切時間が過ぎているかどうか（締切1時間後）"""
        if self.deadline_time:
            return timezone.now() > self.deadline_time
        else:
            # 締切時間が設定されていない場合は出発1時間前を締切とする
            deadline = self.departure_time - timezone.timedelta(hours=1)
            return timezone.now() > deadline

    @property
    def deadline_time_auto(self):
        """自動計算される締切時間（出発1時間前）"""
        return self.departure_time - timezone.timedelta(hours=1)

    @property
    def remaining_seats(self):
        """残り席数を取得"""
        return self.max_participants - self.current_participants


class Participation(models.Model):
    """参加情報モデル"""
    STATUS_CHOICES = [
        ('pending', '保留中'),
        ('confirmed', '確定'),
        ('cancelled', 'キャンセル'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ユーザー")
    ride_plan = models.ForeignKey(RidePlan, on_delete=models.CASCADE, verbose_name="配車計画")
    
    # 乗車場所情報（オプショナル）
    pickup_location_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="乗車場所名")
    pickup_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, verbose_name="乗車場所緯度")
    pickup_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, verbose_name="乗車場所経度")
    
    # 降車場所情報（オプショナル）
    dropoff_location_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="降車場所名")
    dropoff_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, verbose_name="降車場所緯度")
    dropoff_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, verbose_name="降車場所経度")
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="ステータス"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        verbose_name = "参加情報"
        verbose_name_plural = "参加情報"
        unique_together = ['user', 'ride_plan']  # 同じユーザーが同じ配車計画に重複参加できない

    def __str__(self):
        return f"{self.user.username} - {self.ride_plan.title}"
