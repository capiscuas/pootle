def get_username_link(username):
  return u'<a target="_parent" href="/accounts/%s/">%s</a>'%(username,username)

def get_username_mailto_link(username,email):
  return u'<a href="mailto:%s">%s</a>'%(email,username)
  
def get_project_stats_link(lang_code,project):
      if lang_code and project:
	return u'<a target="_parent" href="/%s/%s">%s</a>'%(lang_code,project,project)
      else:
	return u'<a target="_parent" href="/projects/%s/">%s</a>'%(project,project)
  
def get_project_admin_link(lang_code,project):
      if lang_code and project:
	  return u'<a target="_parent" href="/%s/%s/admin_permissions.html">%s</a>'%(lang_code,project,project)
      elif project:
	return u'<a target="_parent" href="/projects/%s/permissions.html">%s</a>'%(project,project)
      elif lang_code:
	return u'<a target="_parent" href="/%s/admin.html">%s</a>'%(lang_code,lang_code)
      else:
	return ''
    
def get_language_admin_link(lang_code,lang_name):
  return u'<a target="_parent" href="/%s/admin.html">%s</a>'%(lang_code,lang_name)
  
def get_projectlanguage_admin_link(project_code,lang_code,lang_name):
    return u'<a href="/%s/%s/">%s</a>'%(lang_code,project_code,lang_code)
    
def get_pootle_link(relative_path,name):
  return u'<a target="_parent" href="/%s">%s</a>'%(relative_path,name)