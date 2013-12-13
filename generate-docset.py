#!/usr/bin/env python
'''Tool to build a Dash docset from puppet-doc sources.

Requirements:

 1. Python markdown package (run: easy_install markdown)

 2. Recursively clone the dash-puppet-docset github repo:
    git clone --recursive git://github.com/jsipprell/dash-puppet-docset.git

 3. Specify the global version numbers to generate below or set PUPPET=3 and PUPPET_REFERENCE=3.1.4 env vars.
'''

import sys,os,codecs,os.path,re,atexit,markdown
from glob import glob

OUTPUT=u'puppet_2.docset/Contents/Resources/Documents'
SQL_OUTPUT=u'regen.sql'
PUPPET=u'2.7'
PUPPET_REFERENCE=u'2.7.21'

class SQLOutput(object):
  _singleton = None
  def __new__(cls,*args,**kwargs):
    if not isinstance(cls._singleton,cls):
      cls._singleton = super(SQLOutput,cls).__new__(cls,*args,**kwargs)
    return cls._singleton

  def __init__(self,filename=None):
    if filename:
      self.filename = filename
      self.output = codecs.open(self.filename,'w','utf-8')
      atexit.register(self.close)

  def __call__(self,name,path,type='Section'):
    path = os.path.basename(path)
    print >>self.output,"INSERT OR IGNORE INTO searchIndex(name,path,type) VALUES ('%s','%s','%s');" % (name,path,type)

  def close(self):
    if self.output:
      try:
        self.output.close()
      finally:
        self.output = None

class LayoutTemplates(object):
  layout_dir = 'layout'

  def __init__(self,layout_dir=None):
    self.layout_dir = layout_dir or self.layout_dir
    self.templates = self.load_templates(dict())

  def load_templates(self,templates):
    template_r = re.compile(ur'''(.+)-([a-z]+).html''')
    for d in glob(os.path.join(self.layout_dir,u'*.html')):
      if not os.path.isfile(d):
        continue
      m = template_r.match(os.path.basename(d))
      if not m:
        continue
      ttype = m.group(2)
      template = templates.setdefault(m.group(1),dict())
      if not template.has_key(ttype):
        with codecs.open(d,'r','utf-8') as f:
          template[ttype] = unicode(f.read())
    return templates

  def clear(self):
    self.templates.clear()

  def reload(self):
    self.templates.clear()
    self.load_templates(self.templates)

  def get(self,name,template_type):
    return self.templates[name][template_type]

  def interpolate(self,name,template_type,data):
    #print 'interpolate name=%s,template_type=%s,data=%s' % (name,template_type,data)
    return self.get(name,template_type) % data

  def has_layout(self,name):
    return self.templates.has_key(name)

  def has_template(self,name,template_type):
    return self.templates.has_key(name) and self.templates[name].has_key(template_type)

class Processor(object):
  line_filters = (re.compile(ur'^{% .+ %}$',re.IGNORECASE),)

  options = {'tab_length':2,
             'extensions':['headerid(level=1)','extra'],
            }
  stylesheet_root = os.path.join('.',u'stylesheets')

  def __init__(self,**options):
    self.mdclass = options.pop(u'MarkdownClass',markdown.Markdown)
    self.output_dir = options.pop(u'output_dir',OUTPUT)
    self.templates = options.pop(u'templates',None)
    self.stylesheet_root = options.pop(u'stylesheet_root',self.stylesheet_root)
    self.options = self.options.copy()
    self.options.update(options)

    for k,v in self.options.items():
      if v is None:
        del self.options[k]

    self.markdown = self.mdclass(**self.options)

  def filter_line(self,line):
    for r in self.line_filters:
      if r.match(line):
        return True
    return False

  def parse_metadata(self,lines,md=None):
    if md is None:
      md = dict()
    first_line = lines[0].rstrip()
    if first_line == ('-' * len(first_line)):
      marker = first_line
      lines.pop(0)
      while lines:
        line = lines.pop(0).rstrip()
        if line == marker:
          break
        kv = line.split(':',1)
        if len(kv) == 2:
          key,val = kv[0].strip(),kv[1].strip()
          if len(val) > 1 and val[0] in ("'",'"') and val[-1] in ("'",'"'):
            md[key.lower()] = val[1:len(val)-1]
          else:
            md[key.lower()] = unicode(val)
    return md

  def process_one(self,input_filename,markdown=None,templates=None,version='??'):
    if markdown is None:
      markdown = self.markdown
      markdown.reset()
    if templates is None:
      templates = self.templates
    output = []
    filter = self.filter_line
    with codecs.open(input_filename,'r','utf-8') as f:
      lines = [l for l in unicode(f.read()).splitlines() if not filter(l)]
      if lines:
        md = self.parse_metadata(lines)
      output.append(markdown.convert(u'\n'.join(lines)))
      del lines[::]

    root,_ = os.path.splitext(os.path.basename(input_filename))
    output_filename = os.path.join(self.output_dir,root+'.html')
    md.setdefault(u'stylesheets',self.stylesheet_root)
    md.setdefault(u'canonical',root+'.html')
    md.setdefault(u'version',version)
    for k,v in md.items():
      if isinstance(v,(list,tuple)) and len(v) == 1:
        md[k] = v[0]

    full_title = md.get('title',u'Puppet '+root)
    if not full_title.lower().startswith(u'puppet'):
      full_title = u'Puppet %s' % (full_title,)
    md.setdefault(u'full_title',full_title)
    output.insert(0,templates.interpolate(md[u'layout'],u'header',md))
    output.append(templates.interpolate(md[u'layout'],u'footer',md))
    with codecs.open(output_filename,'w','utf-8') as f:
      f.write(u'\n'.join(output))
      if root.startswith('lang_'):
        root = root[5:]
      SQLOutput()(root,output_filename)

  def process_glob(self,filespec,**options):
    for filename in glob(filespec):
      if os.path.isfile(filename):
        print 'processing:',filename
        self.process_one(filename,**options)

  def process_globs(self,*filespecs,**options):
    [self.process_glob(spec,**options) for spec in filespecs]

def main(src,major,version):
  kwargs = dict(version=unicode(version))
  templates = LayoutTemplates()
  processor = Processor(templates=templates)

  SQLOutput(SQL_OUTPUT)
  processor.process_glob(os.path.join(src,'source','puppet',str(major),'reference','lang_*.markdown'),**kwargs)

if __name__ == '__main__':
  puppet_docs = os.environ.get('PUPPET_DOCS','puppet-docs')
  if not os.path.isdir(puppet_docs):
    print >>sys.stderr,"'git clone git://github.com/puppetlabs/puppet-docs.git' or set PUPPET_DOCS env var"
    sys.exit(1)

  main(puppet_docs,os.environ.get('PUPPET',PUPPET),os.environ.get('PUPPET_REFERENCE',PUPPET_REFERENCE))
