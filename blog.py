import os.path
import re
import time
import datetime

#import pygments
#import pygments.lexers
#import pygments.formatters

import misaka as md

class blog:
    
    @staticmethod
    def readIndex(cu):
        index = []
        li = os.listdir(cu)
        for i in li:
            now = cu + i
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
                            title += '<a href="p/' + id + '">' + j + '</a>'
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
                        elif count > 2:
                            content += j
                    content = md.html(unicode(content, 'utf-8'), extensions=md.EXT_STRIKETHROUGH)
                    index.append({'id': id, 'title': title, 'content': content})    
        return index
    
    @staticmethod
    def readArticle(cu, id):
        article = {'title': '', 'content': ''}
        txt = cu + id + '.txt'
        md = cu + id + '.md'
        #Wordpress blog articles
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
        elif os.path.isfile(md):
            f = open(md)
            #index += f.read()
            f.close()
        return article
