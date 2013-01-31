#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 capiscuas@gmail.com
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from django.template import RequestContext

from pootle_app.models import Suggestion
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_statistics.models import Submission
from pootle_translationproject.models import TranslationProject


def view(request):
    """Render the content of translators.html created 
       in a cron job(time consuming,used to send automated mails)
    """
    HtmlContent = open("/home/pootle/HTML/translators.html").read()
    data = {
    'HtmlContent':HtmlContent
    }
    return render_to_response('about/memberstatus.html', data,
                              context_instance=RequestContext(request))
