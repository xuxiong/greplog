import os, pyinotify, sys
import urllib2
import re
import logging
from logging import config
import fnmatch
import time, datetime
import threading

logging.config.fileConfig('logging.conf')

logger = logging.getLogger()

class EventHandler(pyinotify.ProcessEvent):

  def __init__(self, pathpattern=[],  filters=None, maxidle=0,  *args, **kwargs):
    super(EventHandler, self).__init__(*args, **kwargs)
    self.filters = filters
    self.files = {}
    self.pathpattern = pathpattern
    self.pathtimestamp = {}
    if maxidle > 0:
      self.maxidle = maxidle
      self.t = threading.Thread(target=self.check)
      self.t.daemon = True
      self.t.start()

  def check(self):
    wait = self.maxidle
    while True:
      time.sleep(wait)
      lastupdate = 0
      current = time.time()
      for path,ts in self.pathtimestamp.items():
        if ts > lastupdate: lastupdate = ts
      if current-lastupdate > self.maxidle:
        logger.error('Lastupdate: %s path:%s' % (datetime.datetime.fromtimestamp(lastupdate).strftime('%Y-%m-%d %H:%M:%S'), self.pathpattern))
        wait *= 2
      else:
        wait = self.maxidle

  def match_path_pattern(self, path):
    for pattern in self.pathpattern:
      if fnmatch.fnmatchcase(path, pattern):
        self.pathtimestamp[pattern] = time.time()
        return True
    return False
  
  def process_IN_MODIFY(self, event):
    pathname = event.pathname
    logger.debug(pathname)
    try:
      if self.match_path_pattern(pathname):
        if pathname not in self.files:
          self.files[pathname] = {}
          self.files[pathname]['file'] = file = open(pathname)
          self.files[pathname]['position'] = position = os.path.getsize(pathname)
          file.seek(position) 
          logger.info('open %s' % pathname)
        self.scan_lines(pathname)
    except Exception,e:
      logger.warn(e)

  def process_default(self, event): 
    pathname = event.pathname
    try:
      if pathname in self.files and event.mask & (pyinotify.IN_DELETE | pyinotify.IN_CLOSE_WRITE):
        f = self.files.pop(pathname)
        f['file'].close()
        logger.info('close %s' % pathname)
    except Exception,e:
      logger.warn(e)

  def scan_lines(self, pathname):
    new_lines = self.files[pathname]['file'].read()
    last_n = new_lines.rfind('\n')
    if last_n >= 0:
      self.files[pathname]['position'] += last_n + 1
      for line in new_lines[:last_n].split('\n'):
        for filter in self.filters:
          try:
            filter.process(line) 
          except Exception, e:
            logger.warn(line)
            logger.warn(e)
            pass
    self.files[pathname]['file'].seek(self.files[pathname]['position'])


import ConfigParser

def my_import(name):
    """Helper function for walking import calls when searching for classes by
    string names.
    """
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

def safe_str_to_class(s):
    """Helper function to map string class names to module classes."""
    lst = s.split(".")
    klass = lst[-1]
    mod_list = lst[:-1]
    module = ".".join(mod_list)
    mod = my_import(module)
    if hasattr(mod, klass):
        return getattr(mod, klass)
    else:
        raise ImportError('')

def str_to_class(s):
    """Alternate helper function to map string class names to module classes."""
    lst = s.split(".")
    klass = lst[-1]
    mod_list = lst[:-1]
    module = ".".join(mod_list)
    try:
        mod = __import__(module)
        if hasattr(mod, klass):
            return getattr(mod, klass)
        else:
            return None
    except ImportError:
        return None

def setup(file):
  conf = ConfigParser.SafeConfigParser()
  conf.read(file)
  paths = conf.get('files', 'pattern').split()
  keys = [s.strip()for s in conf.get('filters', 'keys').split(',')]
  filters = []
  for key in keys:
    cls = safe_str_to_class(conf.get('filter_%s' % key, 'class'))
    args = eval(conf.get('filter_%s' % key, 'args'))
    filters.append(cls(*args))
  try:
    maxidle = conf.getint('handler', 'maxidle')
  except Exception:
    maxidle = 0
  wm = pyinotify.WatchManager()
  handler = EventHandler(pathpattern=paths, filters=filters, maxidle=maxidle)
  notifier = pyinotify.Notifier(wm, handler)
  #wdd = wm.add_watch(paths, pyinotify.ALL_EVENTS, do_glob=True, auto_add=True)
  wdd = wm.add_watch(paths, pyinotify.IN_MODIFY | pyinotify.IN_DELETE | pyinotify.IN_CLOSE_WRITE, do_glob=True, auto_add=True)
  logger.info(wdd)
  notifier.loop()


if __name__ == '__main__':
  setup(sys.argv[1])
'''
  PATHS = sys.argv[1:]
  wm = pyinotify.WatchManager()
  handler = EventHandler(pathpattern=PATHS, filters=(SlowAlert(pattern='&PT=101&', url='http://183.62.12.21:8091/webapi/SlowReport'),))
  notifier = pyinotify.Notifier(wm, handler)
  wdd = wm.add_watch(PATHS, pyinotify.ALL_EVENTS, do_glob=True, auto_add=True)
  logger.info(wdd)
  notifier.loop()
'''
