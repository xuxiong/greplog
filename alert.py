import urllib2
import time
import re
import logging
from logging import config

logging.config.fileConfig('logging.conf')

logger = logging.getLogger()

class Alert:
  def __init__(self, url=None, pattern=None, sep=None, fieldsIdx=None, quote=None):
    self.url = url
    self.pattern = pattern
    self.sep = sep
    self.fieldsIdx = fieldsIdx
    if quote and len(quote) == 1:
      quote += quote[0]
    self.quote = quote
    self.regx = (pattern and re.compile(pattern)) or None

  def process(self, line):
    if self.pattern and re.search(self.pattern, line) is None:
    #if self.regx and self.regx.search(line) is None:
      return
    self._process(line)

  def _process(self, line):
    fields = flds = line.split(self.sep)
    if self.quote:
      fields, stack = [], []
      for fld in flds:
        if fld.startswith(self.quote[0]):
          if fld.endswith(self.quote[1]):
            fields.append(fld)
          else:
            stack.append(fld)
        elif len(stack) == 0:
          fields.append(fld)
        elif len(stack) > 0:
          if fld.endswith(self.quote[1]):
            stack.append(fld)
            fields.append((self.sep or ' ').join(stack))
            stack = []
          else:
            stack.append(fld)
      if len(stack)>0: fields.append((self.sep or ' ').join(stack))
    self._my_process(line=line, fields=fields)

#  def _my_process(self, line, fields):
#    pass

class FrequencyAlert(Alert):
  def __init__(self, url=None, pattern=None, sep=None, fieldsIdx=None, timeformat='%Y-%m-%d %H:%M:%S,%f', match=None, duplicate=None, interval=1, threshold=1, quote=None, level=20):
    Alert.__init__(self, url, pattern, sep, fieldsIdx, quote)
    self.interval = interval
    self.threshold = threshold
    self.buffer = []
    self.timeformat = timeformat
    self.match = match
    self.level = level
    self.duplicate = duplicate

  def parsetime(self, fields):
    return  int(time.mktime(time.strptime(' '.join(fields[0:2]), self.timeformat)))

  def alert(self, fields, count):
    #logger.info('count=%d %s' % (count, fields))
    logger.log(self.level, 'count=%d in %d seconds %s' % (count, self.interval, fields))

  def _my_process(self, line, fields):
    if self.duplicateInBuffer(fields):
      return
    interval = self.interval
    time = self.parsetime(fields)
    buflen = len(self.buffer)
    if buflen == 0:
      self.buffer.append([time, [line], [fields]])
      return
    for i in xrange(1, interval+1):
      if i > buflen: break
      if self.buffer[-i][0] < time:
        if i == 1:
          self.buffer.append([time, [line], [fields]])
        else:
          self.buffer.insert(-i+1, [time, [line], [fields]])
        break
      elif self.buffer[-i][0] == time:
        self.buffer[-i][1].append(line)
        self.buffer[-i][2].append(fields)
        break
      elif time+interval < self.buffer[-1][0]: 
        logger.info('out of range: %d+%d < %d, %s' % (time, interval, self.buffer[-1][0], line))
        return
    self.buffer = self.buffer[-interval:]
    count = self.matchInBuffer(fields)
    if count > self.threshold:
      self.alert(fields, count)
      self.buffer = [[buf[0], buf[1], filter(lambda x: not self.match(x, fields), buf[2])] for buf in self.buffer if buf[0]+interval > self.buffer[-1][0]] #remove duplicates
  
  def matchInBuffer(self, fields):
    count = 0
    for buf in self.buffer:
      if buf[0]+self.interval > self.buffer[-1][0]:
        for flds in buf[2]:
          if self.match(flds, fields):
            count += 1
    return count
  
  def duplicateInBuffer(self, fields):
    if not self.duplicate:
      return False
    for buf in self.buffer:
      for flds in buf[2]:
        if self.duplicate(flds, fields):
          return True
    return False
  
class HTTPCodeAlert(Alert):
  def __init__(self, url=None, pattern=None, sep=None, fieldsIdx=None, threshold=404, quote='""'):
    Alert.__init__(self, url, pattern, sep, fieldsIdx, quote)
    self.threshold = threshold
    self.fieldsIdx = fieldsIdx or (6,5)

  def _my_process(self, line=None, fields=None):
    code = 0
    try:
      code = int(fields[self.fieldsIdx[0]])
    except Exception, e:
      logger.warn(e)
    if code >= self.threshold:
      logger.info(line)
      logger.info('%d:%s' % (code, fields[self.fieldsIdx[1]]))

class SlowAlert(Alert):
  def __init__(self, url=None, pattern=None, threshold=15000, sep=None, fieldsIdx=None, quote='""', parseURL=True):
    Alert.__init__(self, url, pattern, sep, fieldsIdx, quote)
    self.threshold = threshold
    self.fieldsIdx = fieldsIdx or (7, -1, 2, 5)
    self.parseURL = parseURL

  def _my_process(self, line=None, fields=None):
    size, time, ip  = int(fields[self.fieldsIdx[0]]), float(fields[self.fieldsIdx[1]]), fields[self.fieldsIdx[2]]
    if time > 1 and size/time < self.threshold:
      logger.info(line)
      if not self.parseURL: return
      m = re.search('UID=(\d+)', fields[self.fieldsIdx[3]])
      params = 'IP=%s' % ip
      if m:
        params = '%s&UID=%s' % (params, m.groups()[0])
      url = '%s?%s' % (self.url, params)
      logger.info(url)
      if self.url:
        try:
          f = urllib2.urlopen(url)
          f.read()
          f.close()
        except Exception,e:
          logger.warn(e)


class AdaptiveRangeAlert(Alert):
  def __init__(self, url, pattern, sep, fieldsIdx, quote, parsetime, thresholds, type=0):
    Alert.__init__(self, url, pattern, sep, fieldsIdx, quote)
    self.stats = AdaptiveRangeStats(thresholds, type)
    self.parsetime = parsetime

  def _my_process(self, line=None, fields=None):
    time = self.parsetime(fields)
    self.stats.check(time, 1)

class AdaptiveRangeStats:
  def __init__(self, thresholds, type=0):
    '''
    threshold = [(timeunit, value, change),(timeunit, value, change),]
    type: 0-FrequencyAlert, 1-PeakValueAlert
    '''
    #[(timeunit, value, change, begin, sum_or_max(buf[begin, -1])]
    self.thresholds = [x+[0,0,0] for x in thresholds]
    self.thresholds = sorted(self.thresholds, key=lambda x:x[0])
    self.maxunits = self.thresholds[-1][0]
    self.buf = []
    self.type = type
	
  def process(self, lines):
    for line in lines:
      t = line.split()
      time, value = float(t[0]), int(t[1])
      self.check(time, value)
    	 
  def check(self, timestamp, value):
    self.buf.append((timestamp, value))
    offset = 0
    type = self.type
    while timestamp-self.buf[offset][0] >= self.maxunits:
      offset += 1
    for threshold in self.thresholds:
      (timeunit, hist, change, begin, current, prev) = threshold	  
      if type==0:
        current += value
      while timestamp - self.buf[begin][0] >= timeunit:
        if type==0:
          current -= self.buf[begin][1]
        begin += 1
      #if type==0: current = sum([x[1] for x in self.buf[begin:]])
      if type==1:
        current = max([x[1] for x in self.buf[begin:]])
      threshold[3], threshold[4] = begin-offset, current
      if hist < current:
        if hist*(1+change) < current:
          #logger.warn('timeunit=%d,preMax=%d,current=%d' % (timeunit, hist, current))		  
          #print 'timeunit=%d,hist=%d,current=%d,prev=%d,time=%d,begin=%d,buflen=%d,offset=%d' % (timeunit, hist, current, prev, time, begin, len(self.buf), offset)
          print 'timeunit=%d,hist=%d,current=%d,prev=%d,time=%d,%s' % (timeunit, hist, current, prev, timestamp, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp)))
        threshold[1] = current		
      threshold[-1] = current
    del self.buf[:offset]
    
import sys

if __name__ == '__main__':
  handlers = []
  print logger.handlers
  for handler in logger.handlers:
    #if not isinstance(handler, logging.StreamHandler):
    #if type(handler) != logging.StreamHandler:
    if type(handler) is not logging.StreamHandler:
      handlers.append(handler)
  for handler in handlers:
    logger.removeHandler(handler)
  print logger.handlers
  logger.setLevel(logging.DEBUG)
  '''
  cls = locals()[sys.argv[1]]
  args = eval(sys.argv[2])
  print sys.argv[1], args
  obj = cls(*args)
  '''
  obj = eval(sys.argv[1])
  for line in sys.stdin:
    obj.process(line)
