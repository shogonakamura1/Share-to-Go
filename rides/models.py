from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random
import string

# Create your models here.

class Group(models.Model):
    """グループモデル"""
    name = models.CharField(max_length=10, unique=True, verbose_name="グループ名（英数字）")
    display_name = models.CharField(max_length=50, verbose_name="表示名（日本語）")
    password = models.CharField(max_length=4, verbose_name="パスワード")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="作成者")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    
    class Meta:
        verbose_name = "グループ"
        verbose_name_plural = "グループ"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.display_name} ({self.name})"
    
    @classmethod
    def generate_name(cls):
        """英数字10文字のグループ名を生成"""
        while True:
            name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            if not cls.objects.filter(name=name).exists():
                return name
    
    @classmethod
    def generate_password(cls):
        """数字4桁のパスワードを生成"""
        return ''.join(random.choices(string.digits, k=4))


class GroupMembership(models.Model):
    """グループメンバーシップモデル"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ユーザー")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name="グループ")
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="参加日時")
    
    class Meta:
        verbose_name = "グループメンバーシップ"
        verbose_name_plural = "グループメンバーシップ"
        unique_together = ['user', 'group']
    
    def __str__(self):
        return f"{self.user.username} - {self.group.display_name}"


class RidePlan(models.Model):
    """配車計画モデル"""
    STATUS_CHOICES = [
        ('active', '募集中'),
        ('full', '定員満員'),
        ('cancelled', 'キャンセル'),
        ('completed', '完了'),
    ]
    
    creator = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="作成者")
    groups = models.ManyToManyField(Group, verbose_name="表示グループ", blank=True)
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
    # 遅延情報フィールド
    delay_minutes = models.PositiveIntegerField(default=0, verbose_name="遅延時間（分）")
    is_delayed = models.BooleanField(default=False, verbose_name="遅延中")
    delay_updated_at = models.DateTimeField(auto_now=True, verbose_name="遅延情報更新日時")
    # 遅延可能性フィールド
    delay_possibility = models.BooleanField(default=False, verbose_name="遅延の可能性あり")
    delay_possibility_updated_at = models.DateTimeField(auto_now=True, verbose_name="遅延可能性更新日時")
    
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

    @property
    def is_in_progress(self):
        """運行中かどうか（出発時刻から到着予定時刻まで）"""
        # 簡易的に出発時刻から2時間後までを運行中とする
        end_time = self.departure_time + timezone.timedelta(hours=2)
        return self.departure_time <= timezone.now() <= end_time

    @property
    def display_status(self):
        """表示用の動的ステータス"""
        if self.status == 'cancelled':
            return 'cancelled'
        elif self.status == 'completed':
            return 'completed'
        elif self.is_deadline_passed:
            return 'deadline_passed'
        elif self.is_full:
            return 'full'
        else:
            return 'active'

    @property
    def display_status_text(self):
        """表示用の動的ステータステキスト"""
        status_map = {
            'active': '募集中',
            'full': '定員満員',
            'cancelled': 'キャンセル',
            'completed': '完了',
            'deadline_passed': '締切済み'
        }
        return status_map.get(self.display_status, '募集中')

    @property
    def display_status_color(self):
        """表示用の動的ステータス色"""
        color_map = {
            'active': 'success',
            'full': 'warning',
            'cancelled': 'danger',
            'completed': 'primary',
            'deadline_passed': 'secondary'
        }
        return color_map.get(self.display_status, 'success')

    def update_delay(self, delay_minutes):
        """遅延情報を更新"""
        self.delay_minutes = delay_minutes
        self.is_delayed = delay_minutes > 0
        self.save()
    
    def update_delay_possibility(self, possibility):
        """遅延可能性を更新"""
        self.delay_possibility = possibility
        self.save()

    def complete_ride(self):
        """運転終了（配車計画を完了にする）"""
        self.status = 'completed'
        self.save()


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
