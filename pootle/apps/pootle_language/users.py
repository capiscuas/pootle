#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Ivan Garcia capiscuas@gmail.com
# http://pootle.linguisticteam.org
#
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

from django.shortcuts import get_object_or_404, render_to_response
from django.utils.translation import ugettext as _
from django.template import RequestContext
from django.core.exceptions import PermissionDenied

from pootle_language.models import Language

from pootle_app.models.permissions import get_matching_permissions, check_permission
from pootle_profile.models import get_profile

from pootle.scripts import list_users
from pootle.scripts.pootlelinks import *
#from django.core.mail import send_mail,EmailMessage


def language_users(request, language_code):
    # Check if the user can access this view
    language = get_object_or_404(Language, code=language_code)
    request.permissions = get_matching_permissions(get_profile(request.user),
                                                   language.directory)
    if not check_permission('administrate', request):
        raise PermissionDenied(_("You do not have rights to administer this language."))

    error_message = ''
    users = list_users.get_users_by_language(language_code)
    total_users = 0
    
    html = '<table>'
    html += '<tr><th>Username</th><th>Email</th><th>Date Joined</th><th>Last Login</th><th>Projects selected</th></tr>'
      #print users
      
    for user in users:
      #Excluding admin users
        if not user.is_superuser: #if the filter is 0, no need to exclude admin
          total_users += 1
          user_projects = ''
          for proj in user.pootleprofile.projects.all():
              user_projects += '%s, ' %get_project_admin_link(language_code,proj.code)
              
          html += '<tr style="border:1px solid #000;"><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' \
          %(user.username,user.email,user.date_joined,user.last_login,user_projects)

    html += '</table>'
    html+='<b>Total users found: %s</b><br><br><br>' %total_users
      
      
    template_vars = {
        "language": language,
        "directory": language.directory,
        "feed_path": '%s/' % language.code,
        'html': html,
        'error_message': error_message,
        }
    return render_to_response("language/language_users.html", template_vars, context_instance=RequestContext(request))


