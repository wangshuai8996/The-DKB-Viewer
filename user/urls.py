from django.urls import path
from user import views

urlpatterns = [
    # the page for logging, the start page
    path('start/', views.start, name="start"),
    # after users input their information for logging in, use this to process the data input
    path('login_page/', views.login_page, name="login_page"),
    # after users input their information for signing up, use this to process the data input
    path('register/', views.register, name="register"),
    # if users login successfully, go to the home page
    path('home/', views.home, name="home"),
    # clicking a context node, and then enter a context page
    path('context/', views.context, name="context"),
    # clicking a concept node, and then enter a context page
    path('concept/', views.concept, name="concept"),
    # clicking the house icon on the top right, then go to the home page
    path('gohome/', views.gohome, name="gohome"),
    # to save a state
    path('save_state/', views.save_state, name="save_state"),
    # after selecting a state, go to the state page
    path('go_state/', views.go_state, name="go_state"),
    # delete a state
    path('del_state/', views.del_state, name="del_state"),
    # when clicking log out
    path('logout_user/', views.logout_user, name="logout_user")
]
