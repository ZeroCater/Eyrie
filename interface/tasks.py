from django.apps import apps


def process_wiki(repo_id):
    Repo = apps.get_model('interface.Repo')
    try:
        repo = Repo.objects.get(id=repo_id)
    except Repo.DoesNotExist:
        return 'Invalid Repo ID'

    auth = repo.user.get_auth()
    try:
        repo.clone(auth)
        repo.parse_fs()
        repo.clean_directory()
        return 'Processing finished'
    except Exception as e:
        print(e)
        return 'Build Failed'
