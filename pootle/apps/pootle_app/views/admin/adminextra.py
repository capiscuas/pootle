#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Zeitgeist Movement, Ivan <capiscuas@gmail.com>
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

#added (r'^/filters.html$', 'filterusers.view'), to /home/pootle/pootle2/Pootle/local_apps/pootle_app/views/admin/urls.py
#added     <a href='{{ "/admin/filters.html"|l }}' class="adminusers" title="{% trans 'Filter users' %}">{% trans "Filters" %}</a>
#to /home/pootle/pootle2/Pootle/templates/admin_profile_menu.html


import locale

from django.http import HttpResponse
from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template import loader, Context


from django.contrib.auth.models import User
from pootle_app.views.admin import util
from pootle_app.models import Directory
from pootle_project.models import Project
from pootle.scripts.pootlelinks import get_username_link,get_username_mailto_link,get_project_stats_link,get_project_admin_link,get_language_admin_link,get_projectlanguage_admin_link,get_pootle_link

@util.user_is_admin
def view(request):
  html = """<ul><li><a href='/admin/extra/users-preferences.html'>User Preferences</a></li>
           <li><a href='/admin/extra/users-permissions.html'>Users waiting for permissions approval</a></li>
           <li><a href='/admin/extra/users-waiting-removal-permissions.html'>Users waiting for permissions removal</a></li>
           <li><a href='/admin/extra/translation-projects-completed.html'>Projects 100% completed</a></li>
           </ul>"""

  template_vars = {
    'html': html,
    }

  return render_to_response("admin/admin_general_extra.html", template_vars, context_instance=RequestContext(request))  


@util.user_is_admin
def usersPermissions(request):
  template_vars = {
    'html': file('/home/pootle/private/translators.admin.html').read(),
    }
  return render_to_response("admin/admin_general_extra.html", template_vars, context_instance=RequestContext(request))

@util.user_is_admin
def usersPreferencesView(request):
    #Dump of the user preferences and details in a html file (for admin)
    html = u'<b>USERS PREFERENCES</b>:<ul>'
    for user in User.objects.all():
      username = user.username
      html += '<li><b>%s</b>' % username
      userprofile = user.pootleprofile
      html += '<br>Projects selected:'
      for proj in userprofile.projects.all():
        html += '%s ,' % get_project_admin_link('',proj.code)
        
      html += '<br>Languages selected:'
      for lang in userprofile.languages.all():
        html +='%s ,' % get_language_admin_link(lang.code,lang.name)
      
      html += '<br>First Name: %s' %user.first_name
      html += '<br>Last Name: %s' %user.last_name
      html += '<br>Last Login: %s' %user.last_login
      html += '<br>Date Joined: %s' %user.date_joined
      html += '<br>Email: %s' %user.email
      html += '</li><br>'
    
    html += '</ul>'
    
    template_vars = {
    'html': html,
    }
    return render_to_response("admin/admin_general_extra.html", template_vars, context_instance=RequestContext(request))

@util.user_is_admin
def usersWaitingForRemovalPermissions(request):
    html = u'<h3 class="title">Users waiting for permissions removal</h3><div class="info"><p><ul>'
  
    #find those users that deleted some preferences projects or langs with already assigned permissions
    
    user_waiting = 0
    for user in User.objects.all():
      username = user.username
      email = user.email
      if username != 'default' and username != 'nobody':
          #usersPrefs.write('<li class="info"><b>%s</b>' % username)
          userprofile = user.pootleprofile
          selected_languages = userprofile.languages.all()
          selected_projects = userprofile.projects.all()
          permissions = userprofile.permissionset_set.all()
          for permission in permissions:
            directory = permission.directory
            lang = proj = None
            if directory.is_translationproject():
                  print directory
                  if directory.is_translationproject():
                    try:
                      proj = directory.translationproject.project
                      lang = directory.translationproject.language
                      if lang not in selected_languages or proj not in selected_projects:
                        user_waiting += 1
                        html += '<li class="info"><b>%s</b>: (%s, %s)</li>' %(get_username_mailto_link(username,email),lang.name,get_project_admin_link(lang.code,proj.code))
                    except:
                      print 'Directory %r cannot retrieve translationproject' %directory
            elif directory.is_language():
                  lang = directory.language
                  if lang not in selected_languages:
                     user_waiting += 1
                     html += '<li class="info"><b>%s</b>: %s</li>' %(get_username_mailto_link(username,email),get_language_admin_link(lang.code,lang.name))
            elif directory.is_project():
                  proj = directory.project
                  if proj not in selected_projects:
                      user_waiting += 1
                      html += '<li class="info"><b>%s</b>: %s</li>' %(get_username_mailto_link(username,email),get_project_admin_link('',proj.code))
        
    if not user_waiting:
        html +='<li class="info">No translators waiting.</li>'
        
    html += u"</ul></p>"    
    template_vars = {'html': html,}
    return render_to_response("admin/admin_general_extra.html", template_vars, context_instance=RequestContext(request))
    
@util.user_is_admin
def translationProjectsCompleted(request):
      html = u'<h3 class="title">100% translated projects (including Fuzzy)</h3><div class="info"><p><ul>'
      for project in Project.objects.all():
        if project.code != 'pootle':
          project_stats = {}
          project_path = project.pootle_path[len('/projects/'):-1] #to remove the /projects/ at the beggining of the path
          for translationproject in project.translationproject_set.all():
            directory = translationproject.directory
            stats = translationproject.getquickstats()
            proj = translationproject.project
            lang = translationproject.language
            subdirs = directory.child_dirs.all()

            if subdirs: #if this project has subfolders, like tzm_newsletters
              for subdir in subdirs:
                subdir_path = subdir.pootle_path[len(lang.code)+2:-1] #to remove the /<langcode>/ at the beggining of the path
                if project_stats.has_key(subdir_path):
                    project_stats[subdir_path][lang.code] = subdir.getquickstats()
                else: 
                    project_stats[subdir_path] = {lang.code: subdir.getquickstats()}

            else:
                if project_stats.has_key(project_path):
                  project_stats[project_path][lang.code] = directory.getquickstats()
                else: 
                  project_stats[project_path] = {lang.code: directory.getquickstats()}

          for path,lang_stats in project_stats.items():
            path_parent = path.split('/')[0]
            html +="<li class='info'><b>%s</b>:<br>" %(get_pootle_link('projects/'+path_parent+'/permissions.html',path))
            langcodes = lang_stats.keys()
            langcodes.sort()
            for langcode in langcodes:
              stats = lang_stats[langcode]
              if stats['translated'] + stats['fuzzy'] ==  stats['total'] and stats['total']!= 0:
                if langcode != 'templates':
                    lang_link = get_projectlanguage_admin_link(project.code,langcode,langcode)
                    if  stats['fuzzy'] == 0:
                         html +="%s, " %(lang_link)
                    else:
                         html +="%s(%sw), " %(lang_link,stats['fuzzysourcewords'])
            
            html +="</li>"
            
      html += u"</ul></p>"    
      template_vars = {'html': html,}
      return render_to_response("admin/admin_general_extra.html", template_vars, context_instance=RequestContext(request))