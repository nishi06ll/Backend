from django.urls import path
from bookingapi import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
   path('signup', views.signup, name='signup_api'),
    path('login', views.login, name='login_api'),
    path('api/logout/', views.logout, name='api-logout'),
    path('create', views.create, name='create_api'),
    path('list', views.list, name='list_api'),
    # path('<int:pk>/change', views.change, name='updateproductapi'),
    # path('<int:pk>/delete', views.delete, name='deleteproductapi'),
    path('admin/login/', views.admin),
    path('admin/', admin.site.urls),
    path('movies/<int:pk>/disable/', views.disable, name='disable_movie'),
    path('view/<int:pk>/', views.view, name='movie_detail'),
    path('shows/<str:date>/', views.shows, name='shows_on_date'),
    path('product/pdf/<int:pk>/', views.generate_pdf, name='product_pdf'),
    path('start-payment/<int:pk>/', views.start_payment, name='start_payment'),
    path('handle-payment-success/', views.handle_payment_success, name='handle_payment_success'),
    path('my-bookings/', views.my_bookings_api, name='my_bookings_api'),



]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
