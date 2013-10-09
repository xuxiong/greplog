#coding=utf-8
import os, re
import cStringIO

class grep:
  def __init__(self, filename):
    self.filename = filename
    
  def greplines(self, offset=0, pattern=None, limit=10, before=0, after=0):
    with open(self.filename) as file:
      size = os.path.getsize(self.filename)
      lines = []
      p = None
      if pattern:
        p = re.compile(pattern)
      if offset >= 0:
        file.seek(min(size, offset))
        lines = self.grephead(file, limit, p, before, after)      
        here = file.tell()      
      else:
        file.seek(max(-size, offset), 2)
        here = file.tell()
        lines = self.greptail(file, limit, p, before, after)      
      return here, lines
  
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
        if len(linesbefore) > 1: 
          lines.append(linesbefore[:-1])
          linesbefore = []
        lines.append((i, line))
        i += 1
        for j in xrange(after):
          line = file.readline()
          lines.append(line)
    return lines    
  
  def greptail(self, file, limit, p, before, after):
    lines = []
    linesbefore = []
    i = 0
    rlines = reversed_lines(file)
    try:
      for line in rlines:
        if i >= limit: break
        if before > 0:
          if len(linesbefore) > before: linesbefore.pop(0)
          linesbefore.append(line)
        if p is None or re.search(p, line): 
          if len(linesbefore) > 1: 
            lines.append(linesbefore[:-1])
            linesbefore = []
          lines.append((i, line))
          i += 1
          linesafter = []
          try:		  
            for j in xrange(after):
              line = rlines.next()
              linesafter.append(line)
          except StopIteration:
            pass		  
          if len(linesafter) > 0: lines.append(linesafter)	
    except StopIteration:
      pass	
    return lines    
'''
credit goes to http://stackoverflow.com/questions/260273/most-efficient-way-to-search-the-last-x-lines-of-a-file-in-python/260433#260433
'''  
def reversed_lines(file):
    "Generate the lines of file in reverse order."
    part = ''
    for block in reversed_blocks(file):
        for c in reversed(block):
            if c == '\n' and part:
                yield part[::-1]
                part = ''
            part += c
    if part: yield part[::-1]

def reversed_blocks(file, blocksize=4096):
    "Generate blocks of file's contents in reverse order."
    here = file.tell()
    while 0 < here:
        delta = min(blocksize, here)
        here -= delta
        file.seek(here, os.SEEK_SET)
        yield file.read(delta)
        
import web

urls = ('/grep', 'grepHandler')

class grepHandler:
  def GET(self):
    req = web.input(pattern=None, offset='0', limit='10', before='0', after='0')
    g = grep(req.filename)
    return g.greplines(offset=int(req.offset), pattern=req.pattern, limit=int(req.limit), after=int(req.after))
    
app = web.application(urls, globals())

if __name__ == "__main__":
  app.run()
  '''
  g = grep('grep.txt')
  offset, lines = g.greplines(offset=-1, pattern='', limit=5)
  print offset, len(lines), lines
  offset, lines = g.greplines(offset=0, pattern='', limit=5)
  print offset, len(lines), lines  
  '''