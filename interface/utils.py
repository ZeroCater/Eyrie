from github import Github
from social.apps.django_app.default.models import UserSocialAuth


def get_github(user):
    if user.is_authenticated():
        try:
            data = UserSocialAuth.objects.filter(user=user).values_list('extra_data')[0][0]
            username = data['login']
            password = data['access_token']

            return Github(username, password)
        except:
            pass

    return Github()
