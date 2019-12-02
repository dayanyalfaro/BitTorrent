from django.urls import path, include
from BitTorrent_app import views

urlpatterns = [
    path('home/', views.home, name = 'home'),
    path('files/', views.all_files, name = 'files'),
    path('dwns/', views.downloads, name = 'downloads'),
    path('uplds/', views.uploads, name = 'uploads'),
    path('upldfile/', views.upload_file, name = 'upload_file'),
    path('updatepb/', views.update_progress_bar),
    path('', views.get_address),
    path('dt/<str:filename>/', views.download_torrent,name = 'download_torrent'),
    path('df/<str:filename>/', views.download_file,name = 'download_file'),

]