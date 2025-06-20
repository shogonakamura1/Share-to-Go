from django import forms
from .models import RidePlan, Participation
from django.utils import timezone

class RidePlanForm(forms.ModelForm):
    """配車計画作成・編集フォーム"""
    
    class Meta:
        model = RidePlan
        fields = [
            'title', 
            'description', 
            'departure_location', 
            'destination', 
            'departure_time', 
            'deadline_time',
            'max_participants', 
            'price_per_person'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例：東京駅から横浜駅まで'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '配車計画の詳細を入力してください（任意）'
            }),
            'departure_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例：東京駅'
            }),
            'destination': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例：横浜駅'
            }),
            'departure_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'deadline_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'max_participants': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10
            }),
            'price_per_person': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '例：1000（任意）'
            })
        }
        labels = {
            'title': 'タイトル',
            'description': '説明',
            'departure_location': '出発地',
            'destination': '目的地',
            'departure_time': '出発日時',
            'deadline_time': '締切日時',
            'max_participants': '最大参加者数',
            'price_per_person': '一人あたりの料金（円）'
        }
        help_texts = {
            'title': '配車計画のタイトルを入力してください',
            'description': '配車計画の詳細や注意事項を入力してください（任意）',
            'departure_location': '出発地を入力してください',
            'destination': '目的地を入力してください',
            'departure_time': '出発日時を選択してください',
            'deadline_time': '締切日時を選択してください',
            'max_participants': '最大参加者数を設定してください（1-10人）',
            'price_per_person': '一人あたりの料金を設定してください（任意）'
        }
    
    def clean_departure_time(self):
        """出発時刻のバリデーション"""
        departure_time = self.cleaned_data.get('departure_time')
        
        if departure_time and departure_time <= timezone.now():
            raise forms.ValidationError('出発時刻は現在時刻より後の日時を選択してください。')
        
        return departure_time
    
    def clean_max_participants(self):
        """最大参加者数のバリデーション"""
        max_participants = self.cleaned_data.get('max_participants')
        
        if max_participants and (max_participants < 1 or max_participants > 10):
            raise forms.ValidationError('最大参加者数は1人から10人の間で設定してください。')
        
        return max_participants
    
    def clean_price_per_person(self):
        """料金のバリデーション"""
        price_per_person = self.cleaned_data.get('price_per_person')
        
        if price_per_person and price_per_person < 0:
            raise forms.ValidationError('料金は0円以上の値を入力してください。')
        
        return price_per_person

class ParticipationForm(forms.ModelForm):
    """参加予約フォーム"""
    
    class Meta:
        model = Participation
        fields = [
            'pickup_location_name',
            'pickup_latitude',
            'pickup_longitude',
            'dropoff_location_name',
            'dropoff_latitude',
            'dropoff_longitude'
        ]
        widgets = {
            'pickup_location_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例：渋谷駅東口',
                'id': 'pickup_location_name'
            }),
            'pickup_latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 'any',
                'id': 'pickup_latitude',
                'readonly': 'readonly'
            }),
            'pickup_longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 'any',
                'id': 'pickup_longitude',
                'readonly': 'readonly'
            }),
            'dropoff_location_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例：新宿駅南口',
                'id': 'dropoff_location_name'
            }),
            'dropoff_latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 'any',
                'id': 'dropoff_latitude',
                'readonly': 'readonly'
            }),
            'dropoff_longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 'any',
                'id': 'dropoff_longitude',
                'readonly': 'readonly'
            })
        }
        labels = {
            'pickup_location_name': '乗車場所',
            'pickup_latitude': '乗車場所緯度',
            'pickup_longitude': '乗車場所経度',
            'dropoff_location_name': '降車場所',
            'dropoff_latitude': '降車場所緯度',
            'dropoff_longitude': '降車場所経度'
        }
        help_texts = {
            'pickup_location_name': '乗車したい場所を入力してください',
            'dropoff_location_name': '降車したい場所を入力してください（任意）'
        }
    
    def clean(self):
        """フォーム全体のバリデーション"""
        cleaned_data = super().clean()
        pickup_location_name = cleaned_data.get('pickup_location_name')
        pickup_latitude = cleaned_data.get('pickup_latitude')
        pickup_longitude = cleaned_data.get('pickup_longitude')
        
        # 乗車場所は必須
        if not pickup_location_name:
            raise forms.ValidationError('乗車場所は必須です。')
        
        # 座標が入力されている場合は両方必要
        if pickup_latitude and not pickup_longitude:
            raise forms.ValidationError('乗車場所の座標が不完全です。')
        if pickup_longitude and not pickup_latitude:
            raise forms.ValidationError('乗車場所の座標が不完全です。')
        
        return cleaned_data 