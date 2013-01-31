#!/usr/bin/env python
# coding: utf-8

'''Author: Ivan Garcia <capiscuas@gmail.com> 
   Author: Ray / Gman <gman@thezeitgeistmovement.com> 
Copyright: (C) 2010 Linguistic Team International
Permission is granted to redistribute this file under the GPLv3 or later'''

css_path = '/html'

import os
import os.path
import sys
import types
import logging
import codecs
import traceback
from optparse import OptionParser
from time import gmtime, strftime

from pootle import settings, syspath_override
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

#from django.core.management import execute_manager

from django.contrib.auth.models import User
from pootle_project.models import Project
from pootle_language.models import Language
from pootle_app.models import Directory
from pootle_app.models.permissions import check_profile_permission,get_pootle_permission,get_permissions_by_username

from pootle_profile.models import PootleProfile

from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives

from pootle.scripts.pootlelinks import get_username_link,get_username_mailto_link,get_project_stats_link,get_project_admin_link,get_language_admin_link,get_projectlanguage_admin_link
from pootle.scripts import list_users




if len(sys.argv) == 2 and sys.argv[1] == 'email':
    EMAIL_COORDS = True
else:
    EMAIL_COORDS = False


assigned_users = {}
assigned_usernames = set()

assigned_languages = {}
language_names = {}

def get_coordinators_language(lang_code):
  coords = []
  lang = Language.objects.get(code=lang_code)
  #print lang_code
  for userprofile in lang.user_languages.all():
      user = userprofile.user
      d = Directory.objects.get(pootle_path='/%s/' %(lang_code))
      if check_profile_permission(userprofile,'administrate',d):
          if not user.is_superuser:
            coords.append(user)
            
  return coords

def add_unassigned_permissions(assigned_languages,lang,user,proj):
          username = user.username
          email = user.email
          proj_code = proj.code
          lang_code = lang.code
          if assigned_languages[lang.code].has_key(username):
                assigned_languages[lang.code][username][1].append('%s'  %(proj_code))
          else:
                assigned_languages[lang.code][username] = [email,['%s'  %(proj_code)]]

def get_html_members_waiting_status_approval(EMAIL_COORDS):
    output_html = ''
    output_admin_html = ''

    for lang in Language.objects.all(): #range(1,Language.objects.count()+1):
        if lang.code != 'templates':
              language_names[lang.name] = lang.code
              assigned_languages[lang.code] = {}

    print 'Start users loop'
    print strftime("%Y-%m-%d %H:%M:%S", gmtime())
    for user in User.objects.all():
      username = user.username
      if not user.is_superuser:
          #print username
          userprofile = user.pootleprofile
          for proj in userprofile.projects.all():
            if proj.code != 'test' and  proj.code != 'pootle' and proj.code != 'terminology': #We exclude those projects
              for lang in userprofile.languages.all():
                if lang.code == 'templates':
                      continue
                if (proj.code != 'english_proofreading' and lang.code == 'en'):
                      continue
                if(proj.code == 'english_proofreading' and lang.code != 'en'):
                      continue
                
                #print '/%s/%s/' %(lang.code,proj.code)
                try:
                  d = Directory.objects.get(pootle_path='/%s/%s/' %(lang.code,proj.code))
                  #print 'Existe','/%s/%s/' %(lang.code,proj.code)
                  user_permissions = get_permissions_by_username(username,d)
                  if check_profile_permission(userprofile,'suggest',d) or user_permissions is not None and 'view' in user_permissions:
                          if not assigned_users.has_key(lang.code):
                              assigned_users[lang.code] = set()
                          assigned_users[lang.code].add(username.lower())
                          assigned_usernames.add(username)
                  else:
                      add_unassigned_permissions(assigned_languages,lang,user,proj)
                        
                except:
                  print 'exception','/%s/%s/' %(lang.code,proj.code)
                  traceback.print_exc()
                  #add_unassigned_permissions(assigned_languages,lang,user,proj)

    print 'Stop users loop'
    print strftime("%Y-%m-%d %H:%M:%S", gmtime())

    
    #css_fix = """<style  TYPE="text/css">li.info{padding-left: 20px; !important; list-style:square !important;} </style>"""

    
    
    output_html += '<h3 class="title">Waiting for rights assignment:</h3><br><div class="info"><ul>'
    output_admin_html += '<h3 class="title">Waiting for rights assignment:</h3><br><div class="info"><ul>'


    #1. Members Awaiting Translation Rights (name and selected language(s) only)

    lnames = language_names.keys()
    lnames.sort()

    empty = True
    for language in lnames:
      lang_code = language_names[language]
      email_content = u''
      
      if len(assigned_languages[lang_code]):
          empty = False
          output_html += '<li class="info">%s : '% language
          output_admin_html += '<li class="info">%s<ul>'% language
          usernames = assigned_languages[lang_code].keys()
          email_content += """<html><body>
This is an auto-generated email from the LTI Pootle server.  Any replies to it will be directed to the Pootle admin.<br><br>
The following members are now waiting for project permissions in Pootle. 
The email addresses provided below are confidential and must not be shared without the person's advanced consent.
<br><br><ul>"""
          usernames.sort()
          for username in usernames:
            output_html += '%s, ' % get_username_link(username)
            #email = User.objects.get(username=username).email
            #email = 'test'
            
            [email,projects] = assigned_languages[lang_code][username]
            email_content += '<li class="info">%s: <ul>' % get_username_mailto_link(username,email)
            output_admin_html += '<li class="info">%s: <ul>' % get_username_mailto_link(username,email)
            for project in projects:
                  email_content += '<li class="info">%s </li>' %(get_project_admin_link(lang_code,project))
                  output_admin_html += '<li class="info">%s </li>' %(get_project_admin_link(lang_code,project))
                  
            email_content += '</ul></li>'
            output_admin_html +=  '</ul></li>'
            #for username,projects in assigned_languages[lang_code].items():
                
          output_html += '</li>'
          email_content += '</ul></body></html>'
          output_admin_html +=  '</ul></li>'
          
          if EMAIL_COORDS:
            #Find out the lang coordinators email_text
            coords = get_coordinators_language(lang_code)
            if coords:
              coords_email = [coord.email for coord in coords]
            else:
              coords_email = ['pootle-admin@thezeitgeistmovement.com']
            
            email_subject = u"Pootle: %s - Members are waiting for project permissions." %language
            print 'Sending mail language',language,' to ',coords_email
            # create the email, and attach the HTML version as well.
            msg = EmailMultiAlternatives(email_subject, '', 'pootle-admin@thezeitgeistmovement.com', coords_email)
            msg.attach_alternative(email_content, "text/html")
            msg.send()

    if empty:
      output_html += '<li class="info">All members are currently assigned.</li>'
      output_admin_html +=  '<li class="info">All members are currently assigned.</li>'
      
    output_html +=  '</ul></div><br>'
    output_admin_html +=  '</ul></div><br>'

    return output_html,output_admin_html


if __name__ == "__main__":

    output_html,output_admin_html = get_html_members_waiting_status_approval(EMAIL_COORDS)

    output=codecs.open('/home/pootle/HTML/translators.html',  'w',  "utf-8")

    time_string = strftime("%Y-%m-%d %H:%M:%S", gmtime())

    html_begin =  """
    <p style="font-size: 0.8em; color: #555; text-align: right;">
    Generated: %s UTC. Update once every 8 hours</p>""" %(time_string)

    #generated_time_html = """<p>Generated: %s UTC. Update once every 8 hours</p>""" %(time_string)
    contact_link = '/contact/'

    html_members_not_listed_text = """<p 
    style="font-size: 0.9em; color: #555; text-align: right;">Members not listed on this page still need to configure their profiles.
    <br>If you did not receive the activation email within 30 minutes of your visit to the Registration page,
    <br>or have problems with logging in after following the activation email instructions,
    <br>please <a href="%s">e-mail the Pootle admin</a> with a full description of the issue.</p>
    """ %(contact_link)
    
    output.write(html_begin)
    output.write(html_members_not_listed_text)
    output.write(output_html)

    print 'Filters start'
    print strftime("%Y-%m-%d %H:%M:%S", gmtime())

    #2. Members Unable To Be Assigned (display horizontally)
    output.write( """<h3 class="title">Members Unable To Be Assigned:  </h3><div class="info"><p>""")
    no_project_no_language = list_users.get_no_project_no_language_users()
    no_project = list_users.get_no_project_users()
    no_language = list_users.get_no_language_users()
    no_translatable = list_users.get_users_no_translatable_projects()

    if len(no_language):
      output.write('<b>No Language Selected: (<font style="color: red;">%s</font>) </b><br>' %len(no_language))
      usernames = [user.username.lower() for user in no_language]
      usernames.sort()
      for user in usernames:
        output.write("%s, " % get_username_link(user))
      output.write('<br><br>')
        
    if len(no_project):
      output.write('<b>No Projects Selected:  (<font style="color: red;">%s</font>) </b><br>' %len(no_project))
      usernames = [user.username.lower() for user in no_project]
      usernames.sort()
      for user in usernames:
        output.write("%s, " % get_username_link(user))
      output.write('<br><br>')

    if len(no_project_no_language):
      output.write('<b>No Language nor Projects Selected: (<font style="color: red;">%s</font>) </b><br>' %len(no_project_no_language))
      usernames = [user.username.lower() for user in no_project_no_language]
      usernames.sort()
      for user in usernames:
        output.write("%s, " % get_username_link(user))
      output.write('<br><br>')
        
    if len(no_translatable):
      output.write('<b>Non-translatable Selected: (<font style="color: red;">%s</font>) </b><br>' %len(no_translatable))
      usernames = [user.username.lower() for user in no_translatable]
      usernames.sort()
      for user in usernames:
        output.write("%s, " % get_username_link(user))

    output.write( """</p></div>""")

    print 'Filters stop'
    print strftime("%Y-%m-%d %H:%M:%S", gmtime())

    ###3. English Initial Proofreading Project
    original_en_proofreaders = []

    eng_directory = Directory.objects.get(pootle_path='/en/')
    permissions = eng_directory.permission_sets.all()
    for permission in permissions:
      if get_pootle_permission('translate') in permission.positive_permissions.all():
        username = permission.profile.user.username
        original_en_proofreaders.append(username.lower())

    output.write( """<br><h3 class="title">Proofreaders of english original texts (<font style="color: red;">%s</font>):</h3>
                      <div class="info"><p>""" %len(original_en_proofreaders))

    original_en_proofreaders.sort()
    for username in original_en_proofreaders:
          output.write('%s, '%  get_username_link(username))

    output.write( """</p></div>""")

    ###4. Translators (separated by language)

    output.write( """<br><h3 class="title">Assigned members (<font style="color: red;">%s</font>):</h3>
                      <div class="info"><p><table class="translators-details">""" %len(assigned_usernames))

    lnames = language_names.keys()
    lnames.sort()

    for language in lnames:
      lang_code = language_names[language]
      if lang_code != 'templates' and lang_code != 'en':
            total_lang_users = 0
            total_lang_users_str = ''
            if assigned_users.has_key(lang_code):
                total_lang_users = len(assigned_users[lang_code])
                total_lang_users_str = '(%s)'% total_lang_users
            output.write( '<tr><td>%s</td><td><b><a href="/%s/">%s</a></b> %s</td>'%(language,lang_code,lang_code,total_lang_users_str))
            if total_lang_users: #If there are some users, show them
              output.write( '<td>')
              for username in sorted(assigned_users[lang_code]):
                output.write('%s, '%  get_username_link(username))
              output.write( '</td>')
            output.write( '</tr>')

    output.write( """</table></p></div>""")

    output.close()


