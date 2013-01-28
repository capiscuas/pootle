#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010 The Zeitgeist Movement , Ivan <capiscuas@gmail.com>
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
from django.core.cache import cache
from django.utils import simplejson

from django.contrib.auth.models import User

from pootle_app.views.admin.util import user_is_admin

from pootle_app.management.commands import list_users
from django.core.mail import send_mail
from pootle.scripts.pootlelinks import *
from pootle_project.models import Project
from pootle_language.models import Language    
from django.views.decorators.csrf import csrf_protect

@user_is_admin
@csrf_protect
def view(request):
    error_message = ''
    script_num = request.POST.get('filter_num','')
    filter_username = request.POST.get('filter_username','')
    filter_language = request.POST.get('filter_language','')
    filter_project  = request.POST.get('filter_project','')
    email_subject = request.POST.get('email_subject','')
    email_content = request.POST.get('email_content','')
    form_type = request.POST.get('formtype','filter')

    filters = ['Specific user or email','Inactive Users','Users with no projects and no languages','Users with no languages but projects',
              'Users with no projects but languages','Users with specific language or project','Users with no translatable projects',
              'Users with English and not Initial Proofreading','Users without Engish and Initial Proofreading',
              'Users without Engish and Initial Proofreading','Users with 2 or more non-English languages','All users']
    
    select_filters_options = ''
    for num,fil in enumerate(filters):
      if script_num == str(num):
    		select_filters_options += '<option value="%s" SELECTED>%s-%s</option>' %(num,num,fil)
      else:
    		select_filters_options += '<option value="%s" >%s-%s</option>' %(num,num,fil)
    
    select_language_options = '<option value="">----------</option>'
    for lang in Language.objects.all():
       if filter_language == lang.code:
      		select_language_options += '<option value="%s" SELECTED>%s-%s</option>' %(lang.code,lang.code,lang.name)
       else:
      		select_language_options += '<option value="%s">%s-%s</option>' %(lang.code,lang.code,lang.name)
      
    select_project_options = '<option value="">----------</option>'
    for proj in Project.objects.all():
       if filter_project == proj.code:
      		select_project_options += '<option value="%s" SELECTED>%s</option>' %(proj.code,proj.code)
       else:
      		select_project_options += '<option value="%s">%s</option>' %(proj.code,proj.code)
    
    html = """
    * Note: Only admins are shown in filter 0 and 10.<br>
    <form method=post action=filters.html >
     {%% csrf_token %%}
    Filter to apply: 
    <select style='display:inline !important' name=filter_num>%s
      </select>
      <br>(Filter 0) Username/email: <input type=text style='margin-bottom:3px; display:inline !important' value="%s" name=filter_username size=30>
      <br>(Filter 5) Language: <select style='display:inline !important' name=filter_language>%s</select>
      <br>(Filter 5) Project: <select style='display:inline !important' name=filter_project>%s</select>
      <br><br><INPUT value="Filter" type="submit">
    </form>
    
    """%(select_filters_options,filter_username,select_language_options,select_project_options)
    users = []

    if script_num == '0':
      #Filter 0: Get the user with the specified username
      if '@' in filter_username:
        users = User.objects.filter(email=filter_username)
      else:
        users = User.objects.filter(username=filter_username)
    elif script_num == '1':
      #Filter 1: Users who have not yet activated
      users = list_users.get_inactive_users()
    elif script_num == '2':
        users = list_users.get_no_project_no_language_users()
    elif script_num == '3':
        users = list_users.get_no_language_users()
    elif script_num == '4':
        users = list_users.get_no_project_users()
    elif script_num == '5':
        if filter_language == 'all':
          #if not options.dir:
              #print 'You need to provide the -dir parameter for outputing the languages .txt'
          #else:
              #get_users_per_language(options.dir)
          return
        else:
          if not filter_project and not filter_language:
            error_message= 'Language or Project not selected.'
          elif not filter_project and filter_language:
              users = list_users.get_users_by_language(filter_language)
          elif not filter_language and filter_project:
              users = list_users.get_users_by_project(filter_project)
          else:
              users = list_users.get_users_by_language_project(filter_language,filter_project)
    elif script_num == '6':
        users = list_users.get_users_no_translatable_projects()
    elif script_num == '7':
        users = list_users.get_users_english_not_initial_proofreading()
    elif script_num == '8':
        users = list_users.get_users_not_english_initial_proofreading()
    elif script_num == '9':
        users = list_users.get_users_two_non_english_languages()
    elif script_num == '10':
        users = list_users.get_all_users()
    else:
        error_message= 'Script number can be from 0 to 10'
    
    total_users = 0
    
    if form_type == 'email_send':
        if not email_subject or not email_content:
           error_message = 'Mail Subject or Content are empty'
        else:
          for user in users:
          #Excluding admin users
            if not user.is_superuser or script_num == '0' or script_num == '10':
              total_users += 1
              
              email_content_repl = email_content.replace('{username}',user.username)
              email_content_repl = email_content_repl.replace('{email}',user.email)
     
              email_subject_repl = email_subject.replace('{username}',user.username)
              email_subject_repl = email_subject_repl.replace('{email}',user.email)
              
              if user.email:
                send_mail(email_subject_repl, email_content_repl,'pootle-admin@thezeitgeistmovement.com',[user.email], fail_silently=False)
            
          error_message = 'Email sent to %s users.' %total_users
    else:
        html += '<br><br><br><table>'
        html += '<tr><th>Username</th><th>Email</th><th>Date Joined</th><th>Last Login</th></tr>'
        #print users
        for user in users:
        #Excluding admin users
          if not user.is_superuser or script_num == '0' or script_num == '10': #if the filter is 0, no need to exclude admin
            total_users += 1
            html += '<tr style="border:1px solid #000;"><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td></tr>'%(user.username,user.email,user.date_joined,user.last_login)
            if script_num == '5' and filter_language or script_num == '6' or script_num == '0':
              html += '<tr><td colspan=4>Projects selected: '
              for proj in user.pootleprofile.projects.all():
               html += '%s, ' %get_project_admin_link('',proj.code)
              html += '</td></tr>'
            if script_num == '5' and filter_project or script_num == '9' or script_num == '0':
               html += '<tr><td colspan=4>Languages selected: '
               for lang in user.pootleprofile.languages.all():
                  html +='%s ,' % get_language_admin_link(lang.code,lang.name)
          
        html += '</table>'
        html+='<b>Total users found: %s</b><br><br><br>' %total_users
        
        if total_users: 
          html += """<form method=post action=filters.html>

            <input type=hidden name="formtype" value="email_send">
            <input type=hidden name="filter_num" value="%s">
            <input type=hidden name="filter_username" value="%s">
            <input type=hidden name="filter_language" value="%s">
            <input type=hidden name="filter_project" value="%s">
            <input type=text name="email_subject" value='Email subject' size=70><br>
<TEXTAREA name="email_content" COLS=100 ROWS=20>Email content with replaceable variables:

{username} = to be replaced by the user's nickname
{email} = to be replaced by the user's mail address
</TEXTAREA>
            <br><INPUT value="Send Mass Email" type="submit">
        </form>
        """ %(script_num,filter_username,filter_language,filter_project)

    # t = Template(html)
    # c = RequestContext(request)
    # html = HttpResponse(t.render(c))
    # print html

    template_vars = {
        'html': html,
        'error_message': error_message,
        }
    print html

    print 
    return render_to_response("admin/admin_general_filters.html", template_vars, context_instance=RequestContext(request))
