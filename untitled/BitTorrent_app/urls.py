from django.urls import path, include
from BitTorrent_app import views

urlpatterns = [
    path('home/', views.home, name = 'home'),
    path('get_address_autom/', views.get_address_autom, name = 'get_address_autom'),
    path('files/', views.all_files, name = 'files'),
    path('dwns/', views.downloads, name = 'downloads'),
    path('uplds/', views.uploads, name = 'uploads'),
    path('updatepb/', views.update_progress_bar),
    path('', views.get_address),
    path('dt/<str:filename>/', views.download_torrent,name = 'download_torrent'),
    path('df/<str:filename>/', views.download_file,name = 'download_file'),
    path('pause/<int:dwn_id>/', views.pause_download,name = 'pause_download'),
    path('restore/<int:dwn_id>/', views.restore_download,name = 'restore_download'),
]