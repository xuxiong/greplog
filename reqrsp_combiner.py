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
                             'request':url, 'duration':data.iloc[j].Time - time, \
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

def plot(df, title=u'HTTP请求响应时间分析', figsize=(10,15), interval=None):
    ax = df[['time', 'duration']].plot.barh(stacked=True, \
           colormap='Paired', \
           figsize=figsize, \
           xlim=(df.iloc[0].time, df.iloc[-1].time+df.iloc[-1].duration), \
           grid=True)
    ax.set_title(title)
    ax.set_ylabel(u'请求序号')
    ax.set_xlabel(u'时间(秒)')
    ax.xaxis.set_ticks_position('both')
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
rtt = pd.concat([df1.iRTT, df2.iRTT, df3.iRTT, df4.iRTT, df5.iRTT, df6.iRTT, df7.iRTT, df8.iRTT, df9.iRTT, df10.iRTT, df11.iRTT, df12.iRTT], axis=1, keys=['dhcp1','dhcp2', 'dhcp3', 'dhcp4', 'dhcp5', 'dhcp6', 'ppoe1', 'ppoe2', 'ppoe3', 'ppoe4', 'ppoe5', 'ppoe6'])
ax = rtt.boxplot()
ax.set_title(u'网络往返时间分布')
'''
