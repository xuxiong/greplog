#coding=utf-8
import os, re
import cStringIO

class grep:
  def __init__(self, filename):
    self.part2 = None
    self.filename = filename
    
  def greplines(self, offset=0, pattern=None, limit=10, before=0, after=0):
    with open(self.filename) as file:
      size = os.path.getsize(self.filename)
      if abs(offset) < size:
        lines = []
        p = None
        if pattern:
          p = re.compile(pattern)
        if offset >= 0:
          file.seek(offset)
          lines = self.grephead(file, limit, p, before, after)      
          here = file.tell()      
        else:
          file.seek(0, 2)
          delta = 0
          allread = False
          while len(lines) < limit:
            if offset+file.tell() < 0: offset = -1*file.tell()
            file.seek(offset, 1)
            here = file.tell()
            if here == 0:
              allread = True
            str = file.read(abs(offset+delta))
            strio = cStringIO.StringIO(str)
            lines = self.greptail(strio, limit-len(lines), p, before, after, allread) + lines          
            if allread:
              break
            delta = len(str)
            if len(lines) > 0: offset *= limit/len(lines)
            else: offset *= limit
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
        lines.append(line)
        i += 1
        for j in xrange(after):
          line = file.readline()
          lines.append(line)
    return lines    
    
  def greptail(self, strio, limit, p, before, after, allread):
    part0, part1 = None, None
    lines = []
    linesbefore = []
    i = 0
    eob = False
    while i < limit:
      line = strio.readline()
      if line == '':#已到末尾
        eob = True
        if part1 is not None and self.part2 is not None:#存在跨缓冲区的行
          if part1[-1] == '\n':#最后一行是完整的，无需再处理，同时可知上一个缓冲区的第一行也是完整，需要补充处理
            line = self.part2
            self.part2 = part0
          elif part0 == part1:#缓冲区中没有发现一行
            self.part2 = part0 + self.part2
            if allread:#所有数据已经读完，可识别出第一行，进行处理
              line = self.part2
            else:#当前缓冲区已处理完，继续返回上层继续读取数据
              break
          else:
            line = part1 + self.part2 #缓冲区最后的数据与上个缓冲区的开始数据组成一行，进行处理
            self.part2 = part0 #记录当前缓冲区的开始数据，供后续处理
        else: #本缓冲区开头数据留待与下一个缓冲区一起处理
          self.part2 = part0
          break
      elif part0 is None:#缓冲区的开始
        part0, part1 = line, line
        if not allread: #如果本缓冲区以外还存在为读数据，则缓冲区的开始数据暂时不做处理
          continue
        
      part1 = line
      if line and line[-1] == '\n':#若是完整的一行
        if before > 0:
          if len(linesbefore) > before: linesbefore.pop(0)
          linesbefore.append(line)
        if p is None or re.search(p, line): 
          if len(linesbefore) > 1: 
            lines.append(linesbefore[:-1])
            linesbefore = []
          lines.append(line)
          i += 1
          for j in xrange(after):
            line = strio.readline()
            lines.append(line)
      if eob:#当前缓冲区已经处理完
        break
    return lines    

  
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