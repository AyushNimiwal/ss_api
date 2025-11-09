from django.urls import path
from .views import MovieAgentViewSet, GoogleAuthViewSet
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [

    # testing
    path("hello/", MovieAgentViewSet.as_view({
        'get': 'hello'}), name="hello"),

    # auth urls
    path("google/start", GoogleAuthViewSet.as_view({
        'get': 'start'}), name="start"),

    path("ssplanner/oauth2callback/", GoogleAuthViewSet.as_view({
        'get': 'google_callback'}), name="google_callback"),

    path("google/exchange", GoogleAuthViewSet.as_view({
        'post': 'exchange'}), name="exchange"),

    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # main urls
    path("handle_onboarding_suggestions/",MovieAgentViewSet.as_view({
        'get': 'handle_onboarding_suggestions'}), name="get_raw_suggestions"),

    path("suggestions_by_query/", MovieAgentViewSet.as_view({
        'get': 'suggestions_by_query'}), name="suggestions_by_query"),

    path("update_usr_cnt_feedback/<int:id>/", MovieAgentViewSet.as_view({
        'post': 'update_usr_cnt_feedback'}), name="update_usr_cnt_feedback"),
]
