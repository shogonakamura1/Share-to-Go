from django.urls import path
from . import views

app_name = 'rides'

urlpatterns = [
    # ホーム画面（マイページ機能付き）
    path('home/', views.home_view, name='home'),
    
    # 配車計画一覧画面
    path('index/', views.index_view, name='index'),
    
    # 配車計画詳細画面
    path('rides/<int:ride_id>/', views.ride_detail_view, name='ride_detail'),
    
    # 配車計画作成画面
    path('rides/create/', views.create_ride_view, name='create_ride'),
    
    # 配車計画編集画面
    path('rides/<int:ride_id>/edit/', views.edit_ride_view, name='edit_ride'),
    
    # 配車計画削除
    path('rides/<int:ride_id>/delete/', views.delete_ride_view, name='delete_ride'),
    
    # 予約画面
    path('rides/reservation/<int:ride_id>/', views.reservation_view, name='reservation'),
    
    # 予約キャンセル
    path('rides/<int:ride_id>/cancel/', views.cancel_reservation_view, name='cancel_reservation'),
    
    # 運転者モード一覧
    path('driver-mode/', views.driver_mode_list_view, name='driver_mode_list'),
    
    # 運転者モード
    path('rides/<int:ride_id>/driver/', views.driver_mode_view, name='driver_mode'),
    
    # 遅延情報更新API
    path('rides/<int:ride_id>/update-delay/', views.update_delay_view, name='update_delay'),
    
    # 遅延可能性更新API
    path('rides/<int:ride_id>/update-delay-possibility/', views.update_delay_possibility_view, name='update_delay_possibility'),
    
    # 遅延状況統合更新API
    path('rides/<int:ride_id>/update-delay-status/', views.update_delay_status_view, name='update_delay_status'),
    
    # 履歴画面
    path('history/', views.history_view, name='history'),
    
    # ユーザー登録画面
    path('signup/', views.signup_view, name='signup'),
    
    # ログイン画面
    path('login/', views.login_view, name='login'),
    
    # ログアウト
    path('logout/', views.logout_view, name='logout'),
    
    # プロフィール画面
    path('profile/', views.profile_view, name='profile'),
    
    # グループ作成画面
    path('groups/create/', views.create_group_view, name='create_group'),
    
    # グループ参加画面
    path('groups/join/', views.join_group_view, name='join_group'),
] 