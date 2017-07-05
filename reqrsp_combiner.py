# -*- coding: utf-8 -*-
"""
Created on Wed Jun 21 15:35:48 2017

@author: xux
"""
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif']=['SimHei'] #用来正常显示中文标签
plt.rcParams['axes.unicode_minus']=False #用来正常显示负号
#有中文出现的情况，需要u'内容'
import pandas as pd

def combine(filename, clientips=[]):      
    data = pd.read_csv(filename)
    
    reqs = []
    i, j = 0, 0
    n = len(data)
    clientips = set(clientips)
    while i < n:
        if len(clientips) == 0:
            if data.iloc[i].info.startswith('GET ') or data.iloc[i].info.startswith('POST '):
                clientips.add(data.iloc[i].Source)
        if data.iloc[i].Source in clientips:
            time, url, srcport, source = data.iloc[i].Time, data.iloc[i].info, data.iloc[i].srcport, data.iloc[i].Source
            dest, destport = data.iloc[i].Destination, data.iloc[i].destport
            j = i + 1
            while j < n and \
            not (data.iloc[j].Source == dest and \
                 data.iloc[j].srcport == destport and \
                 data.iloc[j].Destination == source and \
                 data.iloc[j].destport == srcport):
                j += 1
            if j < n:
                reqs.append({'time':time, \
                             'host': '%s:%d' % (dest, destport), \
                             'iRTT': data.iloc[j].iRTT, \
                             'length': data.iloc[j].ContentLength, \
                             'request':url, \
                             'duration':data.iloc[j].Time - time, \
                             'resptime':data.iloc[j].responseTime, \
                             'status':data.iloc[j].info})
            while j+1 < n and \
                data.iloc[j+1].Source == data.iloc[j].Source and \
                data.iloc[j+1].Destination == data.iloc[j].Destination and \
                data.iloc[j+1].destport == data.iloc[j].destport:
                j += 1
        i += 1
    
    df = pd.DataFrame(reqs)
    df['end'] = df.time + df.duration
    return df

def plot(df, title=u'HTTP请求响应时间分析', figsize=(10,15), interval=None, labels=None):
    ax = df[['time', 'duration']].plot.barh(stacked=True, \
           #colormap='Paired', \
           color=['w','r'], \
           figsize=figsize, \
           xlim=(df.iloc[0].time, df.iloc[-1].time+df.iloc[-1].duration), \
           grid=True)
    ax.set_title(title)
    ax.set_ylabel(u'请求序号')
    ax.set_xlabel(u'时间(秒)')
    ax.xaxis.set_ticks_position('both')
    if labels:
        ax.legend(labels=labels)
    if interval:
        i, N = 0, len(df)
        facecolor = 'g'
        while i+1 < N:
            if df.iloc[i+1].time - df.iloc[i].time > interval:
                facecolor = 'b' if facecolor == 'g' else 'g'
                ax.axvspan(df.iloc[i].time, df.iloc[i+1].time, facecolor=facecolor, edgecolor='none', alpha=.1)
            i += 1
    return ax

if __name__ == '__main__':
    df = combine('stbpcap')
    df.to_csv('client.access.csv')

#df = df.iloc[::-1]
#df[['time', 'duration']].plot.barh(stacked=True, colormap='Paired', figsize=(10,15), xlim=(df.iloc[0].time, df.iloc[-1].time+df.iloc[-1].duration))

'''
df1 = reqrsp.combine(u'越秀南抓包测试/点播-电影/1.csv')
df2 = reqrsp.combine(u'越秀南抓包测试/点播-电影/2.csv')
df3 = reqrsp.combine(u'越秀南抓包测试/点播-电影/3.csv')
df4 = reqrsp.combine(u'越秀南抓包测试/推荐-直播-点播-精品/1.csv')
df5 = reqrsp.combine(u'越秀南抓包测试/推荐-直播-点播-精品/2.csv')
df6 = reqrsp.combine(u'越秀南抓包测试/推荐-直播-点播-精品/3.csv')
df10 = reqrsp.combine(u'越秀南抓包测试/ppoe_20170629/ppoe1.csv')
df11 = reqrsp.combine(u'越秀南抓包测试/ppoe_20170629/ppoe2.csv')
df12 = reqrsp.combine(u'越秀南抓包测试/ppoe_20170629/ppoe3.csv')

dhcp = pd.concat([df1, df2, df3, df4, df5, df6])
ppoe = pd.concat([df10, df11, df12])

ppoetime = pd.read_csv(u'越秀南抓包测试/ppoe_20170629/ppoe1.csv', usecols=[7,9])
ppoetime = ppoetime.append(pd.read_csv(u'越秀南抓包测试/ppoe_20170629/ppoe2.csv', usecols=[7,9]), ignore_index=True)
ppoetime = ppoetime.append(pd.read_csv(u'越秀南抓包测试/ppoe_20170629/ppoe3.csv', usecols=[7,9]), ignore_index=True)
ppoetime.describe()

responsetime = pd.concat([dhcptime, ppoetime], keys=['DHCP', 'PPPoE'], axis=1)
'''
