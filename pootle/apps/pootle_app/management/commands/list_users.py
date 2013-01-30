#!/usr/bin/env python
# -*- coding: utf-8 -*-
# coding: utf-8

'''Author: Ivan Garcia <ivan@movimientozeitgeist.org> 
   Author: Ray / Gman <gman@thezeitgeistmovement.com> 
Copyright: (C) 2010 The Zeitgeist Movement
Permission is granted to redistribute this file under the GPLv3 or later'''

# try:
#     import syspath_override
# except ImportError:
#     pass

import os
import codecs
import os.path

import sys
# sys.path.insert(0,"/home/pootle/pootle2")
#sys.path.insert(0,"/var/www/vhosts/pootle.linguisticteam.org/src")
# sys.path.append("/home/pootle/pootle2/Django/")
#sys.path.append("/var/www/vhosts/pootle.linguisticteam.org/src/pootle/apps")
# sys.path.append("/home/pootle/pootle2/Pootle/external_apps/")
#print sys.path

#os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

#from django.db import transaction

#from django.contrib.auth.models import User
from pootle_language.models import Language

from pootle_project.models import Project
from pootle_profile.models import PootleProfile

from pootle_misc.siteconfig import load_site_config
#from pootle.legacy.jToolkit import prefs


import types
import logging
from pootle_profile.models import User
from optparse import OptionParser
from django.core.mail import send_mail


def main():
    #OPTIONAL PARAMETERS CONFIGURATION
    parser = OptionParser()
    parser.add_option("-m", "--mail", dest="mail_filename",
          help="filename with the content of the mail", metavar="FILENAME")

    parser.add_option("-s", "--subject", dest="mail_subject",
          help="email's subject", metavar="SUBJECT")

    parser.add_option("-l", "--language", help="language parameter", metavar="LANG_CODE")

    parser.add_option("-p", "--project", help="project parameter", metavar="PROJECT_NAME")
    parser.add_option("-d", "--dir", help="directory parameter", metavar="DIRECTORY")


    parser.add_option("-u", "--username", dest="username",
          help="username parameter", metavar="USERNAME")

    (options, args) = parser.parse_args()
    #print options
    
    if len(args) < 1:
        print "Usage: python %s number_script [options]" % (sys.argv[0])
        print "Example: python %s 1 -m email.txt -s 'Activate your pootle account'" % (sys.argv[0])
        return

    else:
      if options.mail_filename and not options.mail_subject:
          print 'You have forgot to add the subject parameter to send the email.'
          return

      if options.mail_filename:
          if not os.path.exists(options.mail_filename):
              print 'The file %s does not exists' % options.mail_filename
              return
          else:
              email_text_template = codecs.open(options.mail_filename, "r", "utf-8" ).read()
    

      script_num = args[0]
      if script_num == '0':
          #Filter 0: Get the user with the specified username
          print options.username
          users = User.objects.filter(username=options.username)
          print users
          print User.objects.filter(username='capiscuas')
      elif script_num == '1':
          #Filter 1: Users who have not yet activated
          users = get_inactive_users()
      elif script_num == '2':
          users = get_no_project_no_language_users()
      elif script_num == '3':
          users = get_no_language_users()
      elif script_num == '4':
          users = get_no_project_users()
      elif script_num == '5':
          if options.language == 'all':
              if not options.dir:
                  print 'You need to provide the -dir parameter for outputing the languages .txt'
              else:
                  get_users_per_language(options.dir)
              return
          else:
              if not options.project and options.language:
                  users = get_users_by_language(options.language)
              elif not options.language and options.project:
                  users = get_users_by_project(options.project)
              else:
                  users = get_users_by_language_project(options.language,options.project)
      elif script_num == '6':
          users = get_users_no_translatable_projects()
      elif script_num == '7':
          users = get_users_english_not_initial_proofreading()
      elif script_num == '8':
          users = get_users_not_english_initial_proofreading()
      elif script_num == '9':
          users = get_users_two_non_english_languages()
      elif script_num == '10':
          users = get_all_users()
      else:
         print 'Script number can be from 0 to 10'
         return

      #Printing user details
      print 'username\temail\tdate_joined\tlast_login'
      print '--------\t-----\t-----------\t----------'
                  
      total_users = 0
      for user in users:
        #Excluding admin users
        if not user.is_superuser or script_num == '0' or script_num == '10': #if the filter is 0 or 10, no need to exclude admin
          total_users += 1
          print user.username,'\t',user.email,'\t',user.date_joined,'\t',user.last_login
          if script_num == '5' or script_num == '8':
            print user.username,'projects:',user.pootleprofile.projects.all()
          if script_num == '6' or script_num == '11':
            print user.username,'languages:',user.pootleprofile.languages.all()

          if options.mail_filename and user.email:
                  #Sending customized emails to each user
                email_text = email_text_template % {'username':user.username, 'email':user.email}
                send_mail(options.mail_subject, email_text,'pootle-admin@thezeitgeistmovement.com',[user.email], fail_silently=False)
                print 'Sent email to',user.email

      print 'Total users found:',total_users
  

def get_all_users():
      #Filter 12: Get all users
      return User.objects.all().exclude(username__in=('nobody', 'default'))

def get_inactive_users():
      #Filter 1: Users who have not yet activated
      users_no_active = []
      for user in User.objects.filter(is_active=False):
          users_no_active.append(user)

      return users_no_active

def get_no_project_no_language_users():
    #Filter 2: Those who still need to select a language & at least one project
    users_no_language_no_project = []
 
    for user in User.objects.filter(is_active=True):
      username = user.username
      if username != 'default' and username != 'nobody' and username != 'admin':
          profile = user.pootleprofile
          if profile.languages.count() == 0 and profile.projects.count() == 0 :
              users_no_language_no_project.append(user)

    return users_no_language_no_project

def get_no_language_users():
    #Filter 3: Those who still need to select a language
    users_no_language = []
 
    for user in User.objects.filter(is_active=True):
      username = user.username
      if username != 'default' and username != 'nobody' and username != 'admin':
          profile = user.pootleprofile
          if profile.projects.count() > 0 and profile.languages.count() == 0:
              users_no_language.append(user)

    return users_no_language

def get_no_project_users():
    #Filter 4: Those who still need to select at least one project
    users_no_project = []
 
    for user in User.objects.filter(is_active=True):
      username = user.username
      if username != 'default' and username != 'nobody' and username != 'admin':
          profile = user.pootleprofile
          if profile.languages.count() > 0 and profile.projects.count() == 0 :
              users_no_project.append(user)

    return users_no_project


def get_users_per_language(directory):
  for i in range(1,Language.objects.count()+1):
      lang = Language.objects.get(id=i)
      print lang
      if lang.code != 'templates':
          users = []
          output=codecs.open(os.path.join(directory,'%s.html' %lang.name), 'w',  "utf-8")
          output.write('<table><tr><th>Username</th><th>Email</th><th>Language UI</th><th>Date Joined</th><th>Last Login</th></tr>')
          for profile in lang.user_languages.all():
              user = profile.user
              if user.is_active and not user.is_staff:
                  users.append(user)
                  output.write('<tr><td>%s </td><td> %s </td><td> %s </td><td> %s </td><td> %s </td></tr>'%(user.username,user.email,profile.ui_lang,user.date_joined,user.last_login))
  output.write('\nTotal users %d\n'%len(users))
  output.write('</table>')
  output.close()

def get_users_by_language(language_id):
    # All users of a given language
    users = []
    lang = Language.objects.get(code=language_id)
    for user in User.objects.filter(is_active=True):
        profile = user.pootleprofile
        if lang in profile.languages.all():
            users.append(user)

    return users

def get_users_by_project(project_name):
    # All users on a given project, regardless of language
    users = []
    proj = Project.objects.get(code=project_name)
    for user in User.objects.filter(is_active=True):
        profile = user.pootleprofile
        if proj in profile.projects.all():
            users.append(user)

    return users

def get_users_by_language_project(language_id,project_name):
    #5. All users on a given project within a specific language
    users = []

    proj = Project.objects.get(code=project_name)
    lang = Language.objects.get(code=language_id)

    for user in User.objects.filter(is_active=True):
        profile = user.pootleprofile
        if proj in profile.projects.all() and lang in profile.languages.all():
            users.append(user)

    return users

def get_users_no_translatable_projects():
    #6. All users selecting only non-translatable projects, regardless of language
    users = []

    for user in User.objects.filter(is_active=True):
      username = user.username
      if username != 'default' and username != 'nobody' and username != 'admin':
          projects = user.pootleprofile.projects.all()

          projects_codes = []
          non_translatable_projects_counter = 0
          for project in projects:
              projects_codes.append(project.code)
              if project.code == 'test' or project.code == 'pootle' or project.code =='terminology':
                  non_translatable_projects_counter += 1

          if len(projects_codes) > 0 and len(projects_codes) == non_translatable_projects_counter:
            users.append(user)

    return users

def get_users_english_not_initial_proofreading():
    #7. All users who selected only English, but did not include Initial Proofreading in their project selections
    users = []
    proj_initial_proofreading = Project.objects.get(code='initial_proofreading')
    lang_english = Language.objects.get(code='en')

    for user in User.objects.filter(is_active=True):
      profile = user.pootleprofile
      if proj_initial_proofreading not in profile.projects.all():
          if profile.languages.count() == 1 and profile.languages.all()[0] == lang_english:
              users.append(user)

    return users

def get_users_not_english_initial_proofreading():
#Filter 8 is currently including ALL projects, as long as Initial Proofreading is one of them. 
#What's needed are those that have ONLY Initial Proofreading selected, but not English.   :D

    #8. All users who have not selected English, but only selected 'Initial Proofreading' in their project selections
    users = []
    proj_initial_proofreading = Project.objects.get(code='initial_proofreading')
    lang_english = Language.objects.get(code='en')

    for user in User.objects.filter(is_active=True):
      profile = user.pootleprofile
      if lang_english not in profile.languages.all():
          #print profile.projects.all()
          if profile.projects.count() == 1 and profile.projects.all()[0] == proj_initial_proofreading:
              users.append(user)

    return users

def get_users_two_non_english_languages():
    #9. Users who selected 2 or more non-English language (multi-lingual)
    users = []

    for user in User.objects.filter(is_active=True):
        languages = user.pootleprofile.languages.all()

        lang_codes = []
        for lang in languages:
            if lang.code != 'en': #We exclude English from the list
              lang_codes.append(lang.code)

        if len(lang_codes) >= 2: #If 2 or more non-english languages
            users.append(user)

    return users


if __name__ == '__main__':
    main()
