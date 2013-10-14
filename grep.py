#coding=utf-8
import os, re, sys
import cStringIO

class grep:
  def __init__(self, filename):
    self.filename = filename
    
  def greplines(self, offset=0, pattern=None, limit=10, before=0, after=0, forward=True):
    with open(self.filename) as file:
      size = os.path.getsize(self.filename)
      lines = []
      p = None
      if pattern:
        p = re.compile(pattern)
      if forward:
        file.seek(min(size, offset))
        lines = self.grephead(file, limit, p, before, after)
        offset = file.tell()      
      else:
        file.seek(max(size, offset))
        offset, rlines = self.greptail(file, limit, p, before, after)
        lines = rlines[::-1]
      return offset, lines
  
  def grephead(self, file, limit, p, before, after):
    lines = []
    linesbefore = []
    i = 0
    while i < limit:
      line = file.readline()
      if line == '': break
      if before > 0:
        if len(linesbefore) > before: linesbefore.pop(0)
        linesbefore.append(line)
      if p is None or re.search(p, line): 
        match = line
        i += 1
        linesafter = []
        for j in xrange(after):
          line = file.readline()
          if line != '':
            linesafter.append(line)
        lines.append([linesbefore[:-1], match, linesafter])	
        linesbefore = []		
    return lines    
  
  def greptail(self, file, limit, p, before, after):
    lines = []
    linesafter = []
    i = 0
    rlines = reversed_lines(file)
    try:
      for offset, line in rlines:
        if i >= limit: break
        if after > 0:
          if len(linesafter) > after: linesafter.pop(0)
          linesafter.append(line)
        if p is None or re.search(p, line): 
          match = line		
          i += 1
          linesbefore = []
          try:		  
            for j in xrange(before):			
              offset, line = rlines.next()
              linesbefore.append(line)
          except StopIteration:
            pass		  
          lines.append([linesbefore[::-1], match, linesafter[:-1][::-1]])	
          linesafter = []		
    except StopIteration:
      pass	
    return offset, lines    
'''
credit goes to http://stackoverflow.com/questions/260273/most-efficient-way-to-search-the-last-x-lines-of-a-file-in-python/260433#260433
'''  
def reversed_lines(file):
    "Generate the lines of file in reverse order."
    part = ''
    for offset, block in reversed_blocks(file):
        for c in reversed(block):
            if c == '\n' and part:
                yield offset, part[::-1]
                part = ''
            part += c
    if part: yield offset, part[::-1]

def reversed_blocks(file, blocksize=4096):
    "Generate blocks of file's contents in reverse order."
    here = file.tell()
    while 0 < here:
        delta = min(blocksize, here)
        here -= delta
        file.seek(here, os.SEEK_SET)
        yield file.tell(), file.read(delta)
        
import web
import datetime
import json

urls = ('/grep', 'grepHandler', '/ls', 'lsHandler')
render = web.template.render('templates/', cache=False)

class grepHandler:
  def GET(self):
    req = web.input(pattern=None, offset='0', limit='10', before='0', after='0', forward='true')
    if req.filename.find('/') < 0:
      g = grep(logdir+req.filename)
      result = g.greplines(offset=int(req.offset), pattern=req.pattern, limit=int(req.limit), before=int(req.before), after=int(req.after), forward=req.forward.lower()=='true')
      return render.match(result, req)

class lsHandler:
  def GET(self):
    result = []
    for f in os.listdir(logdir):
      path = logdir + f	
      if os.path.isfile(path):
        stat = os.stat(path)
        result.append((f, stat[6], datetime.datetime.fromtimestamp(stat[8]).strftime('%Y-%m-%d %H:%M:%S')))
    result = sorted(result, key=lambda result:result[2], reverse=True)		
    return render.list(result)
          
app = web.application(urls, globals())

logdir = './log/'

if __name__ == "__main__":
  if not os.path.exists(logdir):
    print 'no logdir defined'
    exit(-1)  
  app.run()
  
  g = grep(logdir+'grep.txt')
  #offset, lines = g.greplines(offset=-1, pattern='', limit=5)
  #print offset, len(lines), lines
  offset, lines = g.greplines(offset=-1, pattern='^:2', limit=4, before=2, after=2)
  print offset, len(lines), lines  
