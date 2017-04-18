from django_rq import job
from django.apps import apps

import os
import shutil
import subprocess
import re
from pathlib import Path

import dateutil.parser

from interface.path_processor import PathProcessor


@job
def process_wiki(repo_id, file_change=None):
    file_change = file_change or {}

    Repo = apps.get_model('interface.Repo')
    repo = get_repo(repo_id)

    if not repo:
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
    parse_dir(path, repo.id, repo.full_name, file_change)


def parse_dir(dir_path, repo_id, repo_name, file_change):
    for sub_path in dir_path.iterdir():
        if re.match('.*/\.git', str(sub_path)):
            continue

        if sub_path.is_dir():
            parse_dir(sub_path, repo_id, repo_name, file_change)
            continue

        path_processor = PathProcessor(repo_name, str(sub_path))

        git_style_path = path_processor.git_style_path
        full_path = path_processor.full_path

        if not file_change.get('modified', None) or git_style_path in file_change['modified']:
            process_file_as_document(full_path, repo_name, repo_id)


def process_file_as_document(full_path, repo_name, repo_id):
    Document = apps.get_model('documents.Document')

    path_processor = PathProcessor(repo_name, str(full_path))

    filename = path_processor.filename
    directory = path_processor.directory

    ext = ''
    if '.' in filename:
        _, ext = filename.rsplit('.', maxsplit=1)

    if not ext in Document.FILE_TYPES:
        return

    repo_disk_path = path_processor.repo_disk_path
    disk_path = path_processor.disk_path

    with Path(disk_path).open() as f:
        body = f.read()
        # TODO: Add support for very large files (chunking?)

    tmp_file_path = '{}/{}'.format(os.getcwd(), disk_path)

    git_commit_date = subprocess.check_output([
        'git', '--git-dir=%s/.git' % repo_disk_path, '--work-tree=%s' % repo_disk_path,
        'log', '-1', '--format=%cd', tmp_file_path
    ])
    commit_date = dateutil.parser.parse(git_commit_date)

    document = Document.objects.filter(repo_id=repo_id, path=directory, filename=filename).first()
    document = document or Document(repo_id=repo_id, path=directory, filename=filename)

    document.body = body
    document.commit_date = commit_date
    document.full_clean()
    document.save()


def get_repo(repo_id):
    Repo = apps.get_model('interface.Repo')
    return Repo.objects.filter(id=repo_id).first()


def delete_removed_files(repo_id, file_change):
    if not file_change.get('removed', None):
        return

    repo = get_repo(repo_id)

    if not repo:
        return

    Document = apps.get_model('documents.Document')

    for file_path in file_change['removed']:
        path_processor = PathProcessor(repo.full_name, file_path)
        filename = path_processor.filename
        path = path_processor.directory
        Document.objects.filter(repo_id=repo_id, path=path, filename=filename).delete()


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
