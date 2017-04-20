from django.contrib.auth.models import User
from model_mommy.recipe import Recipe

from documents.models import Document
from interface.models import Repo

document = Recipe(Document)
repo = Recipe(Repo)
user = Recipe(User)
