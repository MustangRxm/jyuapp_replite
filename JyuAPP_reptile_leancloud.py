# -*_coding:utf8-*-
import urllib
from multiprocessing import pool
import chardet
from time import sleep

import demjson as demjson
from bs4 import BeautifulSoup
from multiprocessing.pool import ThreadPool
import schedule
from lxml import etree
import time
import requests, json
import re, string
import sys
from sqlalchemy.sql import func
import sqlite3
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import os
import leancloud



class reptile(object):
    headers = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8;",
                 "Upgrade-Insecure-Requests": "1",
                 "Referer": "http://www.jyu.edu.cn/",
                 "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36"
                 }

    def getResourceBody(self, url):
        html = requests.get(url,headers=self.headers)
        html.encoding = 'utf-8'
        return html.text

    def GetRootLink(self, url):
        # 这里返回每页的新闻链接list
        text =self.getResourceBody(url)
        soup = BeautifulSoup(text, 'lxml')
        # 获取link资料
        link_list = []
        for link in soup.ul.find_all('li'):
            link_list.append(link.a['href'].strip())
        return link_list
        # 开多线程处理
    def saveTolean(self, jn):
        jn.save()

    def ParseRootLink(self, url):
        headers = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8;",
                   "Upgrade-Insecure-Requests": "1",
                   "Referer": "http://www.jyu.edu.cn/",
                   "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36"
                   }
        RootHref = url
        html = requests.get(url, headers=headers)
        html.encoding = 'utf-8'
        soup = BeautifulSoup(html.text, 'lxml')
        RootTitle=''
        for each in soup.find_all("td", class_="biaoti"):
            RootTitle = each.get_text().strip()  # 获得标题
        p_list = soup.find_all("p")
        NewsContent = p_list[0].get_text().strip()  # 获得正文内容
        From=''
        for each in soup.find_all("p", align="right"):
            From = each.get_text().strip()  # 获得正文来源
        img_list = []
        for each in (soup.find_all("p", align="center")):
            try:
                img_list.append(each.a.img['src'].strip())
            except:
                pass
        NewsImage = img_list
        Author=''
        for each in (soup.find_all("font", color="#999999")):
            st = each.get_text().replace(" ","")
            Author=st.strip()#获得作者
        Date=''
        DateID=''
        for each in soup.find_all("td",height="15",align="right",class_="black"):
            string = each.p.get_text()
            list =re.findall(r"\d{4}-\d+-\d+",string)
            Date =list[0].strip()
            DateID = time.mktime(time.strptime(list[0].strip(), '%Y-%m-%d'))
        todo = leancloud.Object.extend('JyuNews')
        jn = todo()
        jn.set('RootHref',RootHref)
        jn.set('RootTitle',RootTitle)
        jn.set('NewsContent',NewsContent)
        jn.set('NewsImage',NewsImage)
        jn.set('Date',Date)
        jn.set('DateID',DateID)
        jn.set('Author',Author)
        jn.set('From',From)
        return jn

    def make_Page_list(self,Num):
        PL = []
        p_l = [2]#只取综合要闻
        for pn in p_l:
            for i in range(1, int(Num) + 1):
                if i == 1:
                    pass
                    # url = 'http://www.jyu.edu.cn/news/index_2.html'
                    # url = 'http://www.jyu.edu.cn/news/index_' + str(pn) + '.html'
                    # PL.append(url)
                elif i > 1:
                    url = 'http://www.jyu.edu.cn/news/index_' + str(pn) + '_1.html'
                    rule_bef = 'index_' + str(pn) + '_(\d+).html'
                    rule_af = 'index_' + str(pn) + '_%s.html'
                    url = re.sub(rule_bef, rule_af % (i - 1), url, re.S)
                    PL.append(url)
        return PL
class reptile_sub():
    headers = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8;",
                 "Upgrade-Insecure-Requests": "1",
                 "Referer": "http://www.jyu.edu.cn/",
                 "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36"
                 }
    def ParseRootLink(self,each_):
        url=each_['subRssSrc']
        subfindid=each_['objectId']
        subName = each_['subName']
        Head_portraitSrc = each_['Head_portraitSrc']
        html = requests.get(url, headers=reptile_sub.headers)
        html.encoding = 'utf-8'
        soup = BeautifulSoup(html.text, 'xml')
        for each in soup.find_all('item'):
            todo = leancloud.Object.extend('JyuSubscription')
            jsb = todo()
            jsb.set('channel_title',subName)
            jsb.set('Root_link',url)
            jsb.set('channel_icon',Head_portraitSrc)
            jsb.set('subFindID',subfindid)
            jsb.set('pubDate',each.pubDate.get_text())
            jsb.set('Title',each.title.get_text())
            jsb.set('Link',each.link.get_text())
            tmp_date = each.pubDate.get_text().split('+')
            TimeId = time.mktime(time.strptime(tmp_date[0].strip(), '%a, %d %b %Y %H:%M:%S'))
            jsb.set('TimeID',TimeId)
            jsb.set('guid',each.guid.get_text())
            self.savetolean(jsb)

    def savetolean(self,jsb):
        print 'save one'
        jsb.save()


if __name__ == '__main__':
    leancloud.init('', '')
    def checkUpdate_JyuNews():
        #检查是否有更新
        rep= reptile()
        rssUrl = 'http://feed43.com/3160128438708337.xml'
        html = requests.get(rssUrl, headers=reptile.headers)
        html.encoding='utf-8'
        #利用rss的guiid来判断
        soup = BeautifulSoup(html.text, 'xml')
        for each in soup.find_all('item'):
            guid =each.guid.get_text()
            #查询guid,然后比较
            jn_todo = leancloud.Object.extend('JyuNews')
            jn_query = jn_todo.query
            query_list = jn_query.contains('guid',guid).find()
            if len(query_list)==0:
                u =rep.ParseRootLink(each.link.get_text())
                u.set('guid',guid)
                print guid
                rep.saveTolean(u)
            else:
                print 'pass'


    def mission_JyuNews():
        rep = reptile()
        pl = rep.make_Page_list(10)
        #注意！！！爬取的地址不能有空格！
        link_list=[]
        for each in pl:
            link_list.extend(rep.GetRootLink(each))
        print link_list
        for each in link_list:
            u1=rep.ParseRootLink(each)
            rep.saveTolean(u1)
        del rep
    def mission_subscription():
        todo = leancloud.Object.extend('SubscriptionFind')
        query = todo.query
        query_list = query.find()
        rep_sub =reptile_sub()
        for each in query_list:
            obj_dirt= each.dump()
            rep_sub.ParseRootLink(obj_dirt)

    def checkUpdate_subscription():
        #1.获得所有订阅链接
        todo = leancloud.Object.extend('SubscriptionFind')
        query = todo.query
        query_list = query.find()
        for each in query_list:
            each_dirt= each.dump()
            print each_dirt
        #2.爬进去，读取item
            html = requests.get(each.get('subRssSrc'), headers=reptile_sub.headers)
            html.encoding = 'utf-8'
            soup = BeautifulSoup(html.text, 'xml')
            for each2 in soup.find_all('item'):
                # 3.检查guid
                guid = each2.guid.get_text()
                print guid
                jsp_todo = leancloud.Object.extend('JyuSubscription')
                jsp_query = jsp_todo.query
                query_list = jsp_query.contains('guid', guid).find()
                print len(query_list)
                if len(query_list) == 0:
                    #4.更新
                    url = each_dirt['subRssSrc']
                    subfindid = each_dirt['objectId']
                    subName = each_dirt['subName']
                    Head_portraitSrc = each_dirt['Head_portraitSrc']
                    todo = leancloud.Object.extend('JyuSubscription')
                    jsb = todo()
                    jsb.set('channel_title', subName)
                    jsb.set('Root_link', url)
                    jsb.set('channel_icon', Head_portraitSrc)
                    jsb.set('subFindID', subfindid)
                    jsb.set('pubDate', each2.pubDate.get_text())
                    jsb.set('Title', each2.title.get_text())
                    jsb.set('Link', each2.link.get_text())
                    tmp_date = each2.pubDate.get_text().split('+')
                    TimeId = time.mktime(time.strptime(tmp_date[0].strip(), '%a, %d %b %Y %H:%M:%S'))
                    jsb.set('TimeID', TimeId)
                    jsb.set('guid', each2.guid.get_text())
                    jsb.save()
            #         rep = reptile_sub()
            #         rep.ParseRootLink(each_dirt)
            #         sleep(3)
                else:
                    print 'pass'
                    pass

        #匹配就跳过，不匹配就增加
        pass
    def checkUpdate_sub_choice():
        pass
    def mission_sub_choice():
        #读取订阅id表,获得ID表
        #将JyuSubscription中，每个ID,今天的条目的前10条选出来，将JyuSubChoice清空，再将选中的数据存入
        todo = leancloud.Object.extend('SubscriptionFind')
        query = todo.query
        query_list = query.select('objectId').find()
        for each in query_list:
            each_dirt = each.dump()
            to2 = leancloud.Object.extend('JyuSubscription')
            qu= to2.query
            qu_list = qu.contains('subFindID',each_dirt['objectId']).add_descending('TimeID').limit(3).find()
            for ea in qu_list:
                ea_dirt = ea.dump()
                jsc_todo = leancloud.Object.extend('JyuSubChoice')
                jsc = jsc_todo()
                jsc.set('channel_title', ea_dirt['channel_title'])
                jsc.set('Root_link', ea_dirt['Root_link'])
                jsc.set('channel_icon', ea_dirt['channel_icon'])
                jsc.set('subFindID', ea_dirt['subFindID'])
                jsc.set('pubDate', ea_dirt['pubDate'])
                jsc.set('Title', ea_dirt['Title'])
                jsc.set('Link',ea_dirt['Link'])
                jsc.set('TimeID', ea_dirt['TimeID'])
                jsc.set('guid', ea_dirt['guid'])
                jsc.save()
    # schedule.every(6).hour.do(checkUpdate)
    # while True:
    #     schedule.run_pending()
    #     sleep(58*60*6)
    # mission_JyuNews()
    #     minutes.do(checkUpdate)
    # checkUpdate_JyuNews()
    # mission_subscription()
    # mission_sub_choice()
    # mission_sub_choice()
    checkUpdate_subscription()
    checkUpdate_JyuNews()
