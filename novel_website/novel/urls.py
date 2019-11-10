from django.urls import path
from . import views

app_name = 'novel'

urlpatterns = [
    path('',views.index,name = 'index'),
    path('search/',views.search,name = 'search'),
    path('home/',views.home,name = 'home'),
    path('search/<int:book_pk>/<int:book_id>/',views.book,name = 'book'),
    path('home/<int:book_pk>/<int:book_id>/',views.book,name = 'book'),
    path('search/<int:book_pk>/<int:book_id>/<int:chapter_id>.html/',
         views.chapter,name='chapter'),
    path('search/<int:book_pk>/<int:book_id>/download/',views.download,name = 'download'),
    path('home/<int:book_pk>/<int:book_id>/download/',views.download,name = 'download'),
    path('home/<int:book_pk>/<int:book_id>/<int:chapter_id>.html/',
         views.chapter,name='chapter'),
]





