from django.urls import include, path
from django.urls import re_path as url
#from django.conf.urls import url, include
from rest_framework import routers
from django.contrib import admin

from django.conf.urls.static import static
from m import settings
from rest_framework.authtoken.views import obtain_auth_token
#from rest_framework.authtoken import views
from django.contrib.auth import views as auth_views
#from n import views
#from n.views import ChangePasswordView
from . router import router

from django.views.decorators.csrf import csrf_exempt
from strawberry.django.views import AsyncGraphQLView
from .async_schema import async_schema

urlpatterns = [
    path('admin/', admin.site.urls),
    path("graphql/async/", csrf_exempt(AsyncGraphQLView.as_view(schema=async_schema))),
]
'''
urlpatterns = [
path('executive_leaders/',include('executive_leaders.urls')),
path('function-store/', include('function_store_app.urls')),
path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
# Swagger UI:
path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
# Redoc UI:
path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
path('r/',include(router.urls)),
path('flags/', include('flags.urls')),
path('loksabha/', include('loksabha.urls')),
path('rajyasabha/', include('rajyasabha.urls')),
path('assembly/', include('assembly.urls')),
path('council/', include('council.urls')),
path('party/', include('party.urls')),
path('auth/', obtain_auth_token),
url('authenticate/', views.CustomObtainAuthToken.as_view()),
 path('api/change-password/', ChangePasswordView.as_view(), name='change-password'),
 path('api/password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    path('admin/',admin.site.urls),
path('', include(router.urls)),
    path('n/',include('n.urls')),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    #path('login/', views.user_login, name='login'),
    path('p/', views.p, name='p'),
    path('partylogin/', views.party_login, name='partylogin'),
    path('profile/', views.profile, name='profile'),
    path('partyprofile/', views.partyprofile, name='partyprofile'),
    #path('password_mla/', views.passwordcreatetwo, name='mlapassword'),
    path('password_success/', views.passwordsuccess, name='success'),
    #url(r'^password_mla/(?P<party>)/$',views.passwordcreation,name='mlapassword'),
    #url(r'^password_mla/(?P<party>\w+)/(?P<MLA_name>)/$', views.passwordcreation, name='mlapassword'),
    path('postuserinfo/', views.model_form_upload, name='postuserinfo'),
    path('updateuserinfo/', views.update_user_info, name='updateuserinfo'),
    path('', views.user_logout, name='logout'),
    path('partylogout/', views.party_logout, name='partylogout'),
    path('change_password/', views.user_change_password, name='changepassword'),
    path('forgot_password/', views.user_forgot_password, name='forgotpassword'),

    path('reset_password/',
         auth_views.PasswordResetView.as_view(template_name= "n/password_reset.html"),
         name="reset_password"),

    path('reset_password_sent/',
         auth_views.PasswordResetDoneView.as_view(template_name="n/password_reset_sent.html"),
         name="password_reset_done"),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name="n/password_reset_form.html"),
         name="password_reset_confirm"),

    path('reset_password_complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name="n/password_reset_done.html"),
         name="password_reset_complete"),
]
'''


if settings.DEBUG:
    import debug_toolbar
    urlpatterns +=path('__debug__/',include(debug_toolbar.urls)),
    urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)
