from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import RidePlan, Participation, Group, GroupMembership
from django.db import models
from .forms import RidePlanForm, ParticipationForm, GroupCreateForm, GroupJoinForm
from django.http import Http404, JsonResponse
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
            return redirect('rides:login')
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
    
    # 参加詳細情報も取得
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
    
    # 参加しているグループ一覧
    user_groups = Group.objects.filter(groupmembership__user=request.user).order_by('-created_at')
    
    context = {
        'created_rides': created_rides,
        'participating_rides': participating_rides,
        'participating_participations': participating_participations,
        'past_rides': past_rides,
        'past_participations': past_participations,
        'user_groups': user_groups,
    }
    
    return render(request, 'rides/profile.html', context)

@login_required
def home_view(request):
    """ホーム画面（配車計画一覧 + 予約したものも当日中は表示）"""
    # ユーザーが参加しているグループを取得
    user_groups = Group.objects.filter(groupmembership__user=request.user)
    
    # 選択されたグループを取得（デフォルトは最初のグループ）
    selected_group_id = request.GET.get('group')
    if selected_group_id:
        selected_group = get_object_or_404(Group, id=selected_group_id, groupmembership__user=request.user)
    elif user_groups.exists():
        selected_group = user_groups.first()
    else:
        selected_group = None
    
    # グループが選択されている場合、そのグループの配車計画のみ表示
    if selected_group:
        rides = RidePlan.objects.filter(
            status='active',
            groups=selected_group
        ).select_related('creator').order_by('-created_at')
    else:
        # グループに参加していない場合は空のクエリセット
        rides = RidePlan.objects.none()
    
    # 締切時間が過ぎたものを除外（より緩やかな条件に変更）
    current_time = timezone.now()
    rides = rides.filter(
        models.Q(deadline_time__isnull=True, departure_time__gt=current_time) |
        models.Q(deadline_time__isnull=False, deadline_time__gt=current_time)
    )
    
    # ユーザーが予約した配車計画も当日中は表示
    user_reservations = Participation.objects.filter(
        user=request.user,
        status='confirmed'
    ).select_related('ride_plan', 'ride_plan__creator')
    
    # 当日中の予約した配車計画を取得
    today = timezone.now().date()
    today_reservations = []
    for reservation in user_reservations:
        if reservation.ride_plan.departure_time.date() == today:
            today_reservations.append(reservation.ride_plan)
    
    # 予約した配車計画を一覧に追加（重複を避ける）
    existing_ride_ids = set(rides.values_list('id', flat=True))
    for ride in today_reservations:
        if ride.id not in existing_ride_ids:
            rides = list(rides) + [ride]
    
    # 検索機能
    search_query = request.GET.get('search', '')
    if search_query:
        rides = [ride for ride in rides if (
            search_query.lower() in ride.title.lower() or
            search_query.lower() in (ride.description or '').lower() or
            search_query.lower() in ride.departure_location.lower() or
            search_query.lower() in ride.destination.lower()
        )]
    
    # フィルター機能
    departure_filter = request.GET.get('departure', '')
    if departure_filter:
        rides = [ride for ride in rides if departure_filter.lower() in ride.departure_location.lower()]
    
    destination_filter = request.GET.get('destination', '')
    if destination_filter:
        rides = [ride for ride in rides if destination_filter.lower() in ride.destination.lower()]
    
    # 日時フィルター
    date_filter = request.GET.get('date', '')
    if date_filter:
        rides = [ride for ride in rides if ride.departure_time.date().isoformat() == date_filter]
    
    # 価格フィルター
    max_price = request.GET.get('max_price', '')
    if max_price:
        rides = [ride for ride in rides if ride.price_per_person and ride.price_per_person <= int(max_price)]
    
    # 参加者数フィルター
    min_participants = request.GET.get('min_participants', '')
    if min_participants:
        rides = [ride for ride in rides if ride.max_participants >= int(min_participants)]
    
    context = {
        'rides': rides,
        'user_groups': user_groups,
        'selected_group': selected_group,
        'search_query': search_query,
        'departure_filter': departure_filter,
        'destination_filter': destination_filter,
        'date_filter': date_filter,
        'max_price': max_price,
        'min_participants': min_participants,
    }
    
    return render(request, 'rides/home.html', context)

@login_required
def index_view(request):
    """配車計画一覧画面"""
    # ユーザーが参加しているグループを取得
    user_groups = Group.objects.filter(groupmembership__user=request.user)
    
    # 選択されたグループを取得（デフォルトは最初のグループ）
    selected_group_id = request.GET.get('group')
    if selected_group_id:
        selected_group = get_object_or_404(Group, id=selected_group_id, groupmembership__user=request.user)
    elif user_groups.exists():
        selected_group = user_groups.first()
    else:
        selected_group = None
    
    # グループが選択されている場合、そのグループの配車計画のみ表示
    if selected_group:
        rides = RidePlan.objects.filter(
            status='active',
            groups=selected_group
        ).select_related('creator').order_by('-created_at')
    else:
        # グループに参加していない場合は空のクエリセット
        rides = RidePlan.objects.none()
    
    # 締切時間が過ぎたものを除外（より緩やかな条件に変更）
    current_time = timezone.now()
    rides = rides.filter(
        models.Q(deadline_time__isnull=True, departure_time__gt=current_time) |
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
        'user_groups': user_groups,
        'selected_group': selected_group,
        'search_query': search_query,
        'departure_filter': departure_filter,
        'destination_filter': destination_filter,
        'date_filter': date_filter,
        'max_price': max_price,
        'min_participants': min_participants,
    }
    
    return render(request, 'rides/index.html', context)

@login_required
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
    # ユーザーが参加しているグループを取得
    user_groups = Group.objects.filter(groupmembership__user=request.user)
    
    # グループに参加していない場合はエラー
    if not user_groups.exists():
        messages.error(request, '配車計画を作成するには、まずグループに参加する必要があります。')
        return redirect('rides:profile')
    
    if request.method == 'POST':
        form = RidePlanForm(request.POST)
        # フォームのグループ選択肢をユーザーのグループに制限
        form.fields['selected_groups'].queryset = user_groups
        
        if form.is_valid():
            ride_plan = form.save(commit=False)
            ride_plan.creator = request.user
            ride_plan.save()
            
            # 選択されたグループを関連付け
            selected_groups = form.cleaned_data['selected_groups']
            ride_plan.groups.set(selected_groups)
            
            messages.success(request, '配車計画を作成しました！')
            return redirect('rides:home')
        else:
            messages.error(request, '入力内容にエラーがあります。修正してください。')
    else:
        form = RidePlanForm()
        # フォームのグループ選択肢をユーザーのグループに制限
        form.fields['selected_groups'].queryset = user_groups
    
    context = {
        'form': form,
        'user_groups': user_groups,
        'title': '配車計画作成'
    }
    
    return render(request, 'rides/create_ride.html', context)

@login_required
def edit_ride_view(request, ride_id):
    """配車計画編集画面"""
    ride = get_object_or_404(RidePlan, id=ride_id)
    user_groups = Group.objects.filter(groupmembership__user=request.user)
    
    # 作成者以外は編集不可
    if ride.creator != request.user:
        messages.error(request, 'この配車計画を編集する権限がありません。')
        return redirect('rides:ride_detail', ride_id=ride_id)
    
    # グループに参加していない場合はエラー
    if not user_groups.exists():
        messages.error(request, '配車計画を編集するには、まずグループに参加する必要があります。')
        return redirect('rides:profile')
    
    # 参加者がいる場合は編集不可
    if ride.current_participants > 0:
        messages.error(request, '参加者がいる配車計画は編集できません。')
        return redirect('rides:ride_detail', ride_id=ride_id)
    
    if request.method == 'POST':
        form = RidePlanForm(request.POST, instance=ride)
        form.fields['selected_groups'].queryset = user_groups
        if form.is_valid():
            ride_plan = form.save()
            # 選択されたグループを関連付け
            selected_groups = form.cleaned_data['selected_groups']
            ride_plan.groups.set(selected_groups)
            messages.success(request, '配車計画を更新しました！')
            return redirect('rides:home')
        else:
            messages.error(request, '入力内容にエラーがあります。修正してください。')
    else:
        form = RidePlanForm(instance=ride)
        form.fields['selected_groups'].queryset = user_groups
        form.initial['selected_groups'] = ride.groups.all()
    
    context = {
        'form': form,
        'ride': ride,
        'title': '配車計画編集',
        'user_groups': user_groups,
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
        return redirect('rides:home')
    
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

@login_required
def driver_mode_view(request, ride_id):
    """運転者モード画面"""
    ride = get_object_or_404(RidePlan, id=ride_id)
    
    # 作成者以外はアクセス不可
    if ride.creator != request.user:
        messages.error(request, 'この機能にアクセスする権限がありません。')
        return redirect('rides:ride_detail', ride_id=ride_id)
    
    # 運行中でない場合はアクセス不可
    if not ride.is_in_progress:
        messages.error(request, '運行中でない配車計画では運転者モードを使用できません。')
        return redirect('rides:ride_detail', ride_id=ride_id)
    
    context = {
        'ride': ride,
    }
    
    return render(request, 'rides/driver_mode.html', context)

@login_required
def update_delay_view(request, ride_id):
    """遅延情報更新API"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POSTメソッドのみ対応'}, status=405)
    
    ride = get_object_or_404(RidePlan, id=ride_id)
    
    # 作成者以外は更新不可
    if ride.creator != request.user:
        return JsonResponse({'error': '権限がありません'}, status=403)
    
    # 運行中でない場合は更新不可
    if not ride.is_in_progress:
        return JsonResponse({'error': '運行中でない配車計画では遅延情報を更新できません'}, status=400)
    
    try:
        delay_minutes = int(request.POST.get('delay_minutes', 0))
        if delay_minutes < 0:
            return JsonResponse({'error': '遅延時間は0分以上で指定してください'}, status=400)
        
        ride.update_delay(delay_minutes)
        
        return JsonResponse({
            'success': True,
            'delay_minutes': ride.delay_minutes,
            'is_delayed': ride.is_delayed,
            'message': f'遅延情報を更新しました（{delay_minutes}分遅れ）' if delay_minutes > 0 else '遅延情報をリセットしました'
        })
        
    except ValueError:
        return JsonResponse({'error': '無効な遅延時間です'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'更新に失敗しました: {str(e)}'}, status=500)

@login_required
def update_delay_possibility_view(request, ride_id):
    """遅延可能性更新API"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POSTメソッドのみ対応'}, status=405)
    
    ride = get_object_or_404(RidePlan, id=ride_id)
    
    # 作成者以外は更新不可
    if ride.creator != request.user:
        return JsonResponse({'error': '権限がありません'}, status=403)
    
    # 運行中でない場合は更新不可
    if not ride.is_in_progress:
        return JsonResponse({'error': '運行中でない配車計画では遅延可能性を更新できません'}, status=400)
    
    try:
        possibility = request.POST.get('possibility') == 'true'
        ride.update_delay_possibility(possibility)
        
        return JsonResponse({
            'success': True,
            'delay_possibility': ride.delay_possibility,
            'message': f'遅延可能性を更新しました（{"可能性あり" if possibility else "可能性なし"}）'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'更新に失敗しました: {str(e)}'}, status=500)

@login_required
def update_delay_status_view(request, ride_id):
    """遅延状況統合更新API"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POSTメソッドのみ対応'}, status=405)
    
    ride = get_object_or_404(RidePlan, id=ride_id)
    
    # 作成者以外は更新不可
    if ride.creator != request.user:
        return JsonResponse({'error': '権限がありません'}, status=403)
    
    # 運行中でない場合は更新不可
    if not ride.is_in_progress:
        return JsonResponse({'error': '運行中でない配車計画では遅延情報を更新できません'}, status=400)
    
    try:
        status_type = request.POST.get('status_type')
        
        if status_type == 'possibility':
            # 数分遅れる可能性あり
            ride.update_delay_possibility(True)
            ride.update_delay(0)  # 遅延時間はリセット
            message = '数分遅れる可能性ありに設定しました'
        elif status_type == '5min':
            # 5分遅れ
            ride.update_delay(5)
            ride.update_delay_possibility(False)  # 可能性はリセット
            message = '5分遅れに設定しました'
        elif status_type == '10min':
            # 10分遅れ
            ride.update_delay(10)
            ride.update_delay_possibility(False)  # 可能性はリセット
            message = '10分遅れに設定しました'
        elif status_type == '15min_plus':
            # 15分以上遅れ
            ride.update_delay(15)
            ride.update_delay_possibility(False)  # 可能性はリセット
            message = '15分以上遅れに設定しました'
        elif status_type == 'no_delay':
            # 遅れなし
            ride.update_delay(0)
            ride.update_delay_possibility(False)
            message = '遅れなしに設定しました'
        else:
            return JsonResponse({'error': '無効なステータスタイプです'}, status=400)
        
        return JsonResponse({
            'success': True,
            'delay_minutes': ride.delay_minutes,
            'is_delayed': ride.is_delayed,
            'delay_possibility': ride.delay_possibility,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({'error': f'更新に失敗しました: {str(e)}'}, status=500)

@login_required
def driver_mode_list_view(request):
    """運転者モード一覧画面"""
    # ユーザーが作成した配車計画で運行中のものを取得
    user_rides = RidePlan.objects.filter(
        creator=request.user
    ).order_by('-departure_time')
    
    # 運行中の配車計画を抽出（完了したものは除外）
    in_progress_rides = []
    for ride in user_rides:
        if ride.is_in_progress and ride.status != 'completed':
            in_progress_rides.append(ride)
    
    total_rides = user_rides.count()
    in_progress_count = len(in_progress_rides)
    completed_count = total_rides - in_progress_count
    
    context = {
        'in_progress_rides': in_progress_rides,
        'total_rides': total_rides,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
    }
    
    return render(request, 'rides/driver_mode_list.html', context)

@login_required
def create_group_view(request):
    """グループ作成画面"""
    if request.method == 'POST':
        form = GroupCreateForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.creator = request.user
            group.name = Group.generate_name()
            group.password = Group.generate_password()
            group.save()
            
            # 作成者を自動的にメンバーに追加
            GroupMembership.objects.create(user=request.user, group=group)
            
            messages.success(request, f'グループ「{group.display_name}」を作成しました！')
            messages.info(request, f'グループ名: {group.name} / パスワード: {group.password}')
            return redirect('rides:profile')
        else:
            messages.error(request, '入力内容にエラーがあります。修正してください。')
    else:
        form = GroupCreateForm()
    
    context = {
        'form': form,
        'title': 'グループ作成'
    }
    
    return render(request, 'rides/create_group.html', context)

@login_required
def join_group_view(request):
    """グループ参加画面"""
    if request.method == 'POST':
        form = GroupJoinForm(request.POST)
        if form.is_valid():
            group_name = form.cleaned_data['group_name']
            group = Group.objects.get(name=group_name)
            
            # 既にメンバーかチェック
            if GroupMembership.objects.filter(user=request.user, group=group).exists():
                messages.warning(request, '既にこのグループのメンバーです。')
                return redirect('rides:profile')
            
            # メンバーシップを作成
            GroupMembership.objects.create(user=request.user, group=group)
            
            messages.success(request, f'グループ「{group.display_name}」に参加しました！')
            return redirect('rides:profile')
        else:
            messages.error(request, '入力内容にエラーがあります。修正してください。')
    else:
        form = GroupJoinForm()
    
    context = {
        'form': form,
        'title': 'グループ参加'
    }
    
    return render(request, 'rides/join_group.html', context)

@login_required
def complete_ride_view(request, ride_id):
    """運転終了API"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POSTメソッドのみ対応'}, status=405)
    
    ride = get_object_or_404(RidePlan, id=ride_id)
    
    # 作成者以外は終了不可
    if ride.creator != request.user:
        return JsonResponse({'error': '権限がありません'}, status=403)
    
    # 運行中でない場合は終了不可
    if not ride.is_in_progress:
        return JsonResponse({'error': '運行中でない配車計画は終了できません'}, status=400)
    
    try:
        ride.complete_ride()
        
        return JsonResponse({
            'success': True,
            'message': '運転を終了しました'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'終了に失敗しました: {str(e)}'}, status=500)
