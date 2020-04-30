"""
Views for the web service
"""

import os
import json
import urllib.parse
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.urls import reverse

import requests

from webservice.github_util import parse_dependencies
from pkgpkr.settings import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, \
    GITHUB_OATH_AUTH_PATH, GITHUB_OATH_ACCESS_TOKEN_PATH, JAVASCRIPT, PYTHON, SUPPORTED_LANGUAGES
from . import github_util
from .recommender_service import RecommenderService

# Instantiate service class
RECOMMENDER_SERVICE = RecommenderService()

DEMO_REPO_INPUT_NAME = 'DEMO'


def index(request):
    """ Return landing page"""
    return render(request,
                  "webservice/index.html",
                  {'demo_input_repo_name': DEMO_REPO_INPUT_NAME,
                   'supported_languages': sorted([lang.capitalize() for lang in SUPPORTED_LANGUAGES.keys()])})


def about(request):
    """ Return about info"""
    return render(request, "webservice/about.html")


def login(request):
    """ Log user in using Github OAuth"""

    # Create keys if not yet there!
    if not request.session.get('github_token'):
        request.session['github_token'] = None  # To keep API token
        request.session['github_info'] = None  # To keep user infor (e.g. name, avatar url)

    # For Selenium testing
    if os.environ.get('SELENIUM_TEST') == '1':
        assert os.environ.get('GH_TOKEN'), "GH_TOKEN not set"
        request.session['github_token'] = os.environ.get('GH_TOKEN')
        request.session['github_info'] = github_util.get_user_info(request.session['github_token'])

        return HttpResponseRedirect(reverse('index'))

    # Redirect to attempt Github Auth
    return HttpResponseRedirect(GITHUB_OATH_AUTH_PATH)


def callback(request):
    """ Github redirect here, then retrieves token for API """

    # Get code supplied by github
    code = request.GET.get('code')

    # Payload to fetch
    payload = {'client_id': GITHUB_CLIENT_ID,
               'client_secret': GITHUB_CLIENT_SECRET,
               'code': code}

    headers = {"accept": "application/json"}

    # Call github to get token
    res = requests.post(GITHUB_OATH_ACCESS_TOKEN_PATH,
                        data=payload,
                        headers=headers)

    # Set token
    request.session['github_token'] = res.json()['access_token']

    # Call for user info and store in sessions (to be used for UI)
    request.session['github_info'] = github_util.get_user_info(request.session['github_token'])

    return HttpResponseRedirect(reverse('index'))


def logout(request):
    """ Logs user out but keep authorization ot OAuth Github"""
    # Flush the session
    request.session['github_token'] = None
    request.session['github_info'] = None

    return HttpResponseRedirect(reverse("index"))


def repositories(request):
    """ Get full list (up to 100) for the current user """
    # Assure login
    if not request.session.get('github_token'):
        return HttpResponseRedirect(reverse("index"))

    # Get all repos
    repos_per_language = github_util.get_repositories(request.session['github_token'])

    combined_repos = dict()

    for language, repos in repos_per_language.items():

        for repo in repos:

            # Skip if repo has no dependencies
            if not repo['object']:
                continue

            # Updated Date
            date_time = repo['updatedAt']

            # Convert time format e.g. 2020-03-16T13:03:34Z -> 2020-03-16
            date = date_time.split('T')[0]

            repo['date'] = date

            # Convert string to encoded URL e.g. hello/world -> hello%2world
            repo['nameWithOwnerEscaped'] = urllib.parse.quote_plus(repo['nameWithOwner'])

            repo['language'] = language

            # Get dependencies if any,  remember if at least some dependencies found
            if parse_dependencies(repo['object']['text'], language):
                combined_repos[repo['nameWithOwner']] = repo

    return render(request, "webservice/repositories.html", {
        'repos': combined_repos.values()
    })


def recommendations(request, name):
    """
    Get recomended pacakges for the repo
    :param request:
    :param name: repo name
    :return:
    """

    # Convert encoded URL back to string e.g. hello%2world -> hello/world
    repo_name = urllib.parse.unquote_plus(name)

    # Process for DEMO run
    if request.method == 'POST':
        language = request.POST.get('language')
        language = language.lower()

        dependencies = request.POST.get('dependencies')
        dependencies = dependencies.strip(',')

        if language not in SUPPORTED_LANGUAGES.keys():
            return HttpResponse(f'Demo language {language} not supported', status=404)

        if language == JAVASCRIPT:
            dependencies = f'{{ "dependencies" : {{ {dependencies} }} }}'

        request.session['dependencies'] = dependencies
        request.session['language'] = language

        branch_name = None
        branch_names = None

    # If GET it means it's not a DEMO POST call with manual dependencies inputs
    else:
        # Assure login
        if not request.session.get('github_token'):
            return HttpResponseRedirect(reverse("index"))

        # Fetch branch name out of HTTP GET Param
        branch_name = request.GET.get('branch', default='master')

        # Get branch names and language (ONLY) for the repo, no need for dependencies yet
        _, branch_names, language = github_util.get_dependencies(request.session['github_token'],
                                                       repo_name,
                                                       branch_name)

    return render(request, "webservice/recommendations.html", {
        'repository_name': repo_name,
        'recommendation_url': f"/recommendations/{urllib.parse.quote_plus(name)}?branch={branch_name}",
        'branch_names': branch_names,
        'current_branch': branch_name,
        'language': language
    })


def recommendations_json(request, name):
    """
    Get recommended pacakges for the repo in JSON format
    :param request:
    :param name: repo name
    :return:
    """

    # Convert encoded URL back to string e.g. hello%2world -> hello/world
    repo_name = urllib.parse.unquote_plus(name)

    if name == DEMO_REPO_INPUT_NAME:
        dependencies = github_util.parse_dependencies(request.session.get('dependencies'),
                                                      request.session.get('language'))

        # Set to none (will also allow for not showing branch selector
        branch_name = None

    else:
        if not request.session.get('github_token'):
            return HttpResponse('Unauthorized', status=401)

        # Fetch branch name out of HTTP GET Param
        branch_name = request.GET.get('branch', default='master')

        # Get depencies for current repo, and branch names for the repo
        dependencies, _, _ = github_util.get_dependencies(request.session['github_token'],
                                                       repo_name,
                                                       branch_name)

    # Get predictions
    recommended_dependencies = RECOMMENDER_SERVICE.get_recommendations(dependencies)

    # Setup data to be returned
    data = {
        'repository_name': repo_name,
        'current_branch': branch_name,
        'data': recommended_dependencies
    }
    return HttpResponse(json.dumps(data), content_type="application/json")
