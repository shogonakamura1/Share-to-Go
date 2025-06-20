from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import RidePlan, Participation
from django.db import models
from .forms import RidePlanForm, ParticipationForm
from django.http import Http404
from django.conf import settings
from django.utils import timezone

# Create your views here.

def signup_view(request):
    """ユーザー登録画面"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 自動ログインを削除
            messages.success(request, 'アカウントが正常に作成されました！ログインしてください。')
            return redirect('login')
        else:
            messages.error(request, '登録に失敗しました。入力内容を確認してください。')
    else:
        form = UserCreationForm()
    
    return render(request, 'rides/signup.html', {'form': form})

@login_required
def profile_view(request):
    """プロフィール画面（作成・参加予定の配車計画一覧）"""
    # 作成した配車計画（最新順）
    created_rides = RidePlan.objects.filter(
        creator=request.user
    ).order_by('-created_at')
    
    # 参加予定の配車計画（最新順）
    participating_rides = RidePlan.objects.filter(
        participation__user=request.user,
        participation__status='confirmed'
    ).order_by('-departure_time')
    
    # 参加情報も取得
    participating_participations = Participation.objects.filter(
        user=request.user,
        status='confirmed'
    ).select_related('ride_plan').order_by('-created_at')
    
    # 過去の配車計画（完了・キャンセル）
    past_rides = RidePlan.objects.filter(
        creator=request.user,
        status__in=['completed', 'cancelled']
    ).order_by('-departure_time')
    
    # 過去に参加した配車計画
    past_participations = RidePlan.objects.filter(
        participation__user=request.user,
        participation__status='confirmed',
        status__in=['completed', 'cancelled']
    ).order_by('-departure_time')
    
    context = {
        'created_rides': created_rides,
        'participating_rides': participating_rides,
        'participating_participations': participating_participations,
        'past_rides': past_rides,
        'past_participations': past_participations,
    }
    
    return render(request, 'rides/profile.html', context)

@login_required
def home_view(request):
    """ホーム画面（マイページ機能付き）"""
    # 現在のユーザーが作成した配車計画（募集中・進行中）
    my_rides = RidePlan.objects.filter(
        creator=request.user,
        status__in=['active', 'completed']
    ).order_by('-created_at')
    
    # 現在のユーザーが予約した配車計画（承認待ち・承認済み）
    my_reservations = Participation.objects.filter(
        user=request.user,
        status__in=['pending', 'approved']
    ).select_related('ride_plan').order_by('-created_at')
    
    # 過去の配車計画・予約（完了・キャンセル）
    past_rides = RidePlan.objects.filter(
        creator=request.user,
        status='completed'
    ).order_by('-departure_time')
    
    past_reservations = Participation.objects.filter(
        user=request.user,
        status__in=['rejected', 'cancelled']
    ).select_related('ride_plan').order_by('-created_at')
    
    context = {
        'my_rides': my_rides,
        'my_reservations': my_reservations,
        'past_rides': past_rides,
        'past_reservations': past_reservations,
    }
    
    return render(request, 'rides/home.html', context)

def index_view(request):
    """配車計画一覧画面"""
    # 募集中の配車計画を取得（最新順）
    # 締切時間が過ぎていないもののみ表示
    rides = RidePlan.objects.filter(
        status='active'
    ).select_related('creator').order_by('-created_at')
    
    # 締切時間が過ぎたものを除外
    current_time = timezone.now()
    rides = rides.filter(
        models.Q(deadline_time__isnull=True, departure_time__gt=current_time + timezone.timedelta(hours=1)) |
        models.Q(deadline_time__isnull=False, deadline_time__gt=current_time)
    )
    
    # 検索機能
    search_query = request.GET.get('search', '')
    if search_query:
        rides = rides.filter(
            models.Q(title__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(departure_location__icontains=search_query) |
            models.Q(destination__icontains=search_query)
        )
    
    # フィルター機能
    departure_filter = request.GET.get('departure', '')
    if departure_filter:
        rides = rides.filter(departure_location__icontains=departure_filter)
    
    destination_filter = request.GET.get('destination', '')
    if destination_filter:
        rides = rides.filter(destination__icontains=destination_filter)
    
    # 日時フィルター
    date_filter = request.GET.get('date', '')
    if date_filter:
        rides = rides.filter(departure_time__date=date_filter)
    
    # 価格フィルター
    max_price = request.GET.get('max_price', '')
    if max_price:
        rides = rides.filter(price_per_person__lte=max_price)
    
    # 参加者数フィルター
    min_participants = request.GET.get('min_participants', '')
    if min_participants:
        rides = rides.filter(max_participants__gte=min_participants)
    
    context = {
        'rides': rides,
        'search_query': search_query,
        'departure_filter': departure_filter,
        'destination_filter': destination_filter,
        'date_filter': date_filter,
        'max_price': max_price,
        'min_participants': min_participants,
    }
    
    return render(request, 'rides/index.html', context)

def ride_detail_view(request, ride_id):
    """配車計画詳細画面"""
    ride = get_object_or_404(RidePlan, id=ride_id)
    
    # 参加者一覧を取得
    participants = Participation.objects.filter(
        ride_plan=ride, 
        status='confirmed'
    ).select_related('user')
    
    # 現在のユーザーが参加しているかチェック
    user_participation = None
    if request.user.is_authenticated:
        user_participation = Participation.objects.filter(
            ride_plan=ride,
            user=request.user
        ).first()
    
    context = {
        'ride': ride,
        'participants': participants,
        'user_participation': user_participation,
    }
    
    return render(request, 'rides/ride_detail.html', context)

@login_required
def create_ride_view(request):
    """配車計画作成画面"""
    if request.method == 'POST':
        form = RidePlanForm(request.POST)
        if form.is_valid():
            ride_plan = form.save(commit=False)
            ride_plan.creator = request.user
            ride_plan.save()
            
            messages.success(request, '配車計画を作成しました！')
            return redirect('rides:index')
        else:
            messages.error(request, '入力内容にエラーがあります。修正してください。')
    else:
        form = RidePlanForm()
    
    context = {
        'form': form,
        'title': '配車計画作成'
    }
    
    return render(request, 'rides/create_ride.html', context)

@login_required
def edit_ride_view(request, ride_id):
    """配車計画編集画面"""
    ride = get_object_or_404(RidePlan, id=ride_id)
    
    # 作成者以外は編集不可
    if ride.creator != request.user:
        messages.error(request, 'この配車計画を編集する権限がありません。')
        return redirect('rides:ride_detail', ride_id=ride_id)
    
    # 参加者がいる場合は編集不可
    if ride.current_participants > 0:
        messages.error(request, '参加者がいる配車計画は編集できません。')
        return redirect('rides:ride_detail', ride_id=ride_id)
    
    if request.method == 'POST':
        form = RidePlanForm(request.POST, instance=ride)
        if form.is_valid():
            form.save()
            messages.success(request, '配車計画を更新しました！')
            return redirect('rides:ride_detail', ride_id=ride_id)
        else:
            messages.error(request, '入力内容にエラーがあります。修正してください。')
    else:
        form = RidePlanForm(instance=ride)
    
    context = {
        'form': form,
        'ride': ride,
        'title': '配車計画編集'
    }
    
    return render(request, 'rides/edit_ride.html', context)

@login_required
def delete_ride_view(request, ride_id):
    """配車計画削除"""
    ride = get_object_or_404(RidePlan, id=ride_id)
    
    # 作成者以外は削除不可
    if ride.creator != request.user:
        messages.error(request, 'この配車計画を削除する権限がありません。')
        return redirect('rides:ride_detail', ride_id=ride_id)
    
    if request.method == 'POST':
        # 参加者がいる場合は削除不可
        if ride.current_participants > 0:
            messages.error(request, '参加者がいる配車計画は削除できません。')
            return redirect('rides:ride_detail', ride_id=ride_id)
        
        ride.delete()
        messages.success(request, '配車計画を削除しました。')
        return redirect('rides:index')
    
    context = {
        'ride': ride,
    }
    
    return render(request, 'rides/delete_ride.html', context)

@login_required
def reservation_view(request, ride_id):
    """予約画面"""
    ride = get_object_or_404(RidePlan, id=ride_id)
    
    # 既に参加している場合は詳細画面にリダイレクト
    existing_participation = Participation.objects.filter(
        ride_plan=ride,
        user=request.user
    ).first()
    
    if existing_participation:
        if existing_participation.status == 'confirmed':
            messages.info(request, '既にこの配車計画に参加しています。')
        elif existing_participation.status == 'pending':
            messages.info(request, '既にこの配車計画に参加申し込み済みです。')
        return redirect('rides:ride_detail', ride_id=ride_id)
    
    # 作成者は予約できない
    if ride.creator == request.user:
        messages.error(request, '自分が作成した配車計画には参加できません。')
        return redirect('rides:ride_detail', ride_id=ride_id)
    
    # 予約上限に達している場合
    if ride.is_full:
        messages.error(request, 'この配車計画は定員に達しています。')
        return redirect('rides:ride_detail', ride_id=ride_id)
    
    # 期限切れの場合
    if ride.is_expired:
        messages.error(request, 'この配車計画は期限切れです。')
        return redirect('rides:ride_detail', ride_id=ride_id)
    
    if request.method == 'POST':
        form = ParticipationForm(request.POST)
        if form.is_valid():
            # 予約処理
            participation = form.save(commit=False)
            participation.ride_plan = ride
            participation.user = request.user
            participation.status = 'confirmed'  # 直接確定
            participation.save()
            
            messages.success(request, '配車計画に参加しました！')
            return redirect('rides:ride_detail', ride_id=ride_id)
        else:
            # バリデーションエラーの詳細を表示
            error_messages = []
            for field, errors in form.errors.items():
                field_name = form.fields[field].label if field in form.fields else field
                for error in errors:
                    error_messages.append(f'{field_name}: {error}')
            
            if error_messages:
                messages.error(request, '入力内容にエラーがあります：\n' + '\n'.join(error_messages))
            else:
                messages.error(request, '入力内容にエラーがあります。修正してください。')
    else:
        form = ParticipationForm()
    
    context = {
        'ride': ride,
        'form': form,
        'google_maps_api_key': getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
        'google_maps_enabled': getattr(settings, 'GOOGLE_MAPS_ENABLED', False),
    }
    
    return render(request, 'rides/reservation.html', context)

@login_required
def cancel_reservation_view(request, ride_id):
    """予約キャンセル"""
    ride = get_object_or_404(RidePlan, id=ride_id)
    
    participation = Participation.objects.filter(
        ride_plan=ride,
        user=request.user
    ).first()
    
    if not participation:
        messages.error(request, '参加していない配車計画です。')
        return redirect('rides:ride_detail', ride_id=ride_id)
    
    if request.method == 'POST':
        participation.delete()
        messages.success(request, '参加をキャンセルしました。')
        return redirect('rides:ride_detail', ride_id=ride_id)
    
    context = {
        'ride': ride,
        'participation': participation,
    }
    
    return render(request, 'rides/cancel_reservation.html', context)

def history_view(request):
    """履歴画面（過去の配車計画一覧）"""
    if not request.user.is_authenticated:
        messages.error(request, 'ログインが必要です。')
        return redirect('rides:login')
    
    # 完了・キャンセルされた配車計画、または締切時間が過ぎた配車計画（最新順）
    current_time = timezone.now()
    deadline_passed = models.Q(
        models.Q(deadline_time__isnull=True, departure_time__lte=current_time + timezone.timedelta(hours=1)) |
        models.Q(deadline_time__isnull=False, deadline_time__lte=current_time)
    )
    completed_rides = RidePlan.objects.filter(
        models.Q(status__in=['completed', 'cancelled']) |
        models.Q(status='active') & deadline_passed
    ).select_related('creator').order_by('-departure_time')
    
    # 検索機能
    search_query = request.GET.get('search', '')
    if search_query:
        completed_rides = completed_rides.filter(
            models.Q(title__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(departure_location__icontains=search_query) |
            models.Q(destination__icontains=search_query)
        )
    
    # フィルター機能
    status_filter = request.GET.get('status', '')
    if status_filter:
        completed_rides = completed_rides.filter(status=status_filter)
    
    date_filter = request.GET.get('date', '')
    if date_filter:
        completed_rides = completed_rides.filter(departure_time__date=date_filter)
    
    # 自分の配車計画のみ表示するフィルター
    my_rides_only = request.GET.get('my_rides', '')
    if my_rides_only:
        completed_rides = completed_rides.filter(creator=request.user)
    
    context = {
        'rides': completed_rides,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'my_rides_only': my_rides_only,
    }
    
    return render(request, 'rides/history.html', context)

def login_view(request):
    """ログインビュー"""
    if request.user.is_authenticated:
        return redirect('rides:home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'{user.username}さん、ようこそ！')
            return redirect('rides:home')
        else:
            messages.error(request, 'ユーザー名またはパスワードが正しくありません。')
    
    return render(request, 'rides/login.html')

def logout_view(request):
    """ログアウトビュー（ログインページにリダイレクト）"""
    logout(request)
    messages.success(request, 'ログアウトしました。')
    return redirect('rides:login')
