from django_rq import job
from django.apps import apps

import os
import shutil
import subprocess
from pathlib import Path

import dateutil.parser


@job
def process_wiki(repo_id, file_change=None):
    file_change = file_change or {}

    Repo = apps.get_model('interface.Repo')
    try:
        repo = Repo.objects.get(id=repo_id)
    except Repo.DoesNotExist:
        return 'Invalid Repo ID'

    auth = repo.user.get_auth()

    try:
        delete_removed_files(repo_id, file_change)
        clone(repo.clone_url, repo.wiki_branch, repo.directory, auth)
        parse_fs(repo, file_change)
        clean_directory(repo.directory)
    except Exception as e:
        print(e)
        raise
        return 'Build Failed'


def parse_fs(repo, file_change):
    # Walk through each file in the filesystem
    # Create/Delete/Update Documents
    path = Path(repo.directory)
    parse_dir(path, repo.id, repo.directory, file_change)


def parse_dir(dir, repo_id, repo_directory, file_change):
    for sub_path in dir.iterdir():

        full_path = str(sub_path).split('/', maxsplit=1)[1]
        path, filename = full_path.rsplit('/', maxsplit=1)

        file_path = full_path.replace(repo_directory.replace('tmp/', ''), '')

        if filename == '.git':
            continue
        if sub_path.is_dir():
            parse_dir(sub_path, repo_id, repo_directory, file_change)
        elif not file_change.get('modified', None) or file_path in file_change['modified']:
            path = path.replace(repo_directory.replace('tmp/', ''), '') + '/'
            process_file_as_document(sub_path, full_path, repo_id, repo_directory)


def process_file_as_document(file_directory, file_path, repo_id, repo_directory):
    Document = apps.get_model('documents.Document')

    path, filename = file_path.rsplit('/', maxsplit=1)

    ext = ''
    if '.' in filename:
        _, ext = filename.rsplit('.', maxsplit=1)

    if not ext in Document.FILE_TYPES:
        return

    with file_directory.open() as f:
        body = f.read()
        # TODO: Add support for very large files (chunking?)

    tmp_file_path = '{0}/tmp/{1}'.format(os.getcwd(), file_path)

    git_commit_date = subprocess.check_output([
        'git', '--git-dir=%s/.git' % repo_directory, '--work-tree=%s' % repo_directory,
        'log', '-1', '--format=%cd', tmp_file_path
    ])
    commit_date = dateutil.parser.parse(git_commit_date)

    path = path.replace(repo_directory.replace('tmp/', ''), '') + '/'

    document = Document.objects.filter(repo_id=repo_id, path=path, filename=filename).first()
    document = document or Document(repo_id=repo_id, path=path, filename=filename)

    document.body = body
    document.commit_date = commit_date
    document.full_clean()
    document.save()


def delete_removed_files(repo_id, file_change):
    if not file_change.get('removed', None):
        return

    Document = apps.get_model('documents.Document')

    for file_path in file_change['removed']:
        path, filename = file_path.rsplit('/', maxsplit=1)
        Document.objects.filter(repo_id=repo_id, path="{}/".format(path), filename=filename).delete()


def clone(clone_url, branch, repo_directory, auth):
    clone_url = clone_url.replace('github.com', '{}:{}@github.com'.format(*auth))
    if not os.path.exists('tmp'):
        os.makedirs('tmp')

    clean_directory(repo_directory)

    subprocess.call([
        'git', 'clone', clone_url, repo_directory
    ])
    subprocess.call([
        'git', '--git-dir=%s/.git' % repo_directory, '--work-tree=%s' % repo_directory, 'fetch', clone_url
    ])
    subprocess.call([
        'git', '--git-dir=%s/.git' % repo_directory, '--work-tree=%s' % repo_directory, 'checkout', branch
    ])


def clean_directory(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)
