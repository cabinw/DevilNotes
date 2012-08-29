#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path
import re
import time
import datetime

#import pygments
#import pygments.lexers
#import pygments.formatters
import misaka as md
import PyRSS2Gen

class blog:
    
    @staticmethod
    def readIndex(sets, page = 1):
        paged = sets['paged']
        index = []
        li = sorted(os.listdir(sets['folder_blog']))
        tmp = []
        for i in li:
            if re.match(r'^\d+\.txt|\d+\.md$', i):
                tmp.append(i)
        if (page != -1): #-1 means all
            li = tmp[paged*(int(page)-1):paged*(int(page)-1)+3]
        for i in reversed(li):
            now = sets['folder_blog'] + i
            if os.path.isfile(now):
                title = ''
                content = ''
                #Wordpress blog articles
                if re.match(r'^\d+\.txt$', i):
                    id = i.replace('.txt', '')
                    f = open(now)
                    html = f.readlines()
                    f.close()
                    count = 0
                    for j in html:
                        count += 1
                        if re.match(r'<!--more-->', j):
                            break
                        if count == 1:
                            title += '<a href="/p/' + id + '">' + j + '</a>'
                        elif count > 2:
                            content += '<p>' + j.replace('<img', '<img style="display:none;"') + '</p>'
                    index.append({'id': id,'title': title, 'content': content})
                #Markdown
                elif re.match(r'^\d+\.md$', i):
                    id = i.replace('.md', '')
                    f = open(now)
                    html = f.readlines()
                    f.close()
                    count = 0
                    for j in html:
                        count += 1
                        if count == 1:
                            title += '<a href="p/' + id + '">' + j + '</a>'
                            #title += j
                        elif count > 2:
                            content += j
                    content = md.html(unicode(content, 'utf-8'), extensions=md.EXT_STRIKETHROUGH)
                    index.append({'id': id, 'title': title, 'content': content})    
        return {'index': index, 'isPagedEnough': len(tmp)>page*paged}
        
    @staticmethod
    def readArticle(cu, id):
        article = {'id': 0, 'title': '', 'content': ''}
        txt = cu + id + '.txt'
        mkd = cu + id + '.md'
        #Wordpress blog articles
        article['id'] = id
        if os.path.isfile(txt):
            f = open(txt)
            html = f.readlines()
            f.close()
            count = 0
            hasPre = False
            for i in html:
                count += 1
                if count == 1:
                    article['title'] += '<a href="p/' + str(id) + '">' + i + '</a>'
                elif count > 2:
                    if re.match(r'</pre>', i):
                        isPre = False
                        #code = pygments.highlight(tmp, pygments.lexers.PythonLexer(), pygments.formatters.HtmlFormatter())
                        #article['content'] += code.encode('utf-8') #unicode(code, 'utf-8')
                    article['content'] += '<p>' + i + '</p>'
                    if re.match(r'<pre', i):
                        hasPre = True
                #if hasPre:
                #    article['content'] += '<style>' + pygments.formatters.HtmlFormatter().get_style_defs('.highlight') + '</style>'
        #Markdown
        elif os.path.isfile(mkd):
            f = open(mkd)
            html = f.readlines()
            f.close()
            count = 0
            for i in html:
                count += 1
                if count == 1:
                    article['title'] += '<a href="p/' + str(id) + '">' + i + '</a>'
                    #title += i
                elif count > 2:
                    article['content'] += i
            article['content'] = md.html(unicode(article['content'], 'utf-8'), extensions=md.EXT_STRIKETHROUGH)
        return article

    @classmethod
    def outputRSS(cls, sets):
        tmp = cls.readIndex(sets, -1)
        articles = tmp['index']
        items = []
        for article in articles:
            url = sets['url'] + 'p/' + article['id']
            items.append(PyRSS2Gen.RSSItem(
                title = article['title'],
                link = url,
                description = article['content'],
                guid = PyRSS2Gen.Guid(url),
                pubDate = datetime.datetime.fromtimestamp(float(article['id'])),
            ))
        rss = PyRSS2Gen.RSS2(
            title = sets['title'],
            link = sets['url'],
            description = sets['desc'],
            lastBuildDate = datetime.datetime.now(),
            items = items
        ).to_xml()
        return rss
            