#!/usr/bin/env python
#-*- coding: utf8 -*-
'''
Copyright (c) 2012, lodevil/Du Jiong
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the <organization> nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

import urllib
import urllib2
import re


class JWC(object):
    def __init__(self, url='http://jwc.swust.edu.cn'):
        if not url.startswith('http://'):
            url = 'http://' + url
        self.url = self.base_url = url
        self.links = {}
        self._cookie = None

    def open(self):
        rep = urllib2.urlopen(self.url)
        self.url = rep.geturl()
        self._cookie = re.search(r'(\([a-zA-Z0-9]+\))', self.url).groups()[0]
        self._cookieurl = '/'.join(rep.geturl().split('/')[:-1]) + '/'
        return rep.read()

    @staticmethod
    def _get_view_state(data):
        r = re.search(r'name="__VIEWSTATE" value="([^"]+)"', data)
        if r:
            return r.groups()[0]

    def cookie_url(self, u):
        return self._cookieurl + u

    def _page(self, page_name, get_args=None, post_args=None):
        url = self.cookie_url(self.links[page_name])
        if get_args is not None:
            url = '%s?%s' % (url, urllib.urlencode(get_args))
        if post_args:
            req = urllib2.Request(url, urllib.urlencode(post_args),
                {'Referer': self._main_url})
        else:
            req = urllib2.Request(url, None,
                {'Referer': self._main_url})
        return urllib2.urlopen(req)

    def get_page(self, page_name, **kwargs):
        return self._page(page_name, get_args=kwargs)

    def post_page(self, page_name, **kwargs):
        return self._page(page_name, post_args=kwargs)

    def login(self, username, password):
        data = self.open()
        post = urllib.urlencode({
            '__VIEWSTATE': self._get_view_state(data),
            'TextBox1': username,
            'TextBox2': password,
            'RadioButtonList1': u'学生'.encode('gbk'),
            'Button1': '',
            'lbLanguage': ''
            })
        rep = urllib2.urlopen(self.url, post)
        if 'xs_main.aspx' in rep.geturl():
            self._main_url = rep.geturl()
            data = rep.read().decode('gbk')
            links = re.findall(r'<a href="([^"]+)"[^>]*>([^<]+)</a>', data)
            for link, name in links:
                link = list(link.encode('gbk'))
                for i, c in enumerate(link):
                    if ord(c) > 127:
                        link[i] = urllib.quote(c)
                self.links[name] = ''.join(link)
            urllib2.urlopen(self._cookieurl + 'content.aspx')
            return True
        return False

    def get_scores(self, school_year='', term=''):
        data = self.get_page(u'个人成绩查询').read()
        post = {'__VIEWSTATE': self._get_view_state(data),
            'ddlXN': school_year, 'ddlXQ': term}
        if not school_year:
            post['Button2'] = urllib.quote(u'在校学习成绩查询'.encode('gbk'))
        elif not term:
            post['Button5'] = urllib.quote(u'按学年查询'.encode('gbk'))
        else:
            post['Button1'] = urllib.quote(u'按学期查询'.encode('gbk'))
        rep = self.post_page(u'个人成绩查询', **post)
        data = rep.read().decode('gbk')
        table = data[data.find('<table'): data.find('</table>')]
        trs = table.split('<tr')[2:]
        scores = []
        for tr in trs:
            cols = re.findall(r'<td>([^<]*)</td>', tr)
            scores.append({
                'name': cols[3],
                'credit': cols[6],
                'grade_point': cols[7],
                'score': cols[8]
                })
        avg_i = data.find(u'平均学分绩点：') + len(u'平均学分绩点：')
        avg = data[avg_i: data.find('</b>', avg_i)]
        return {'scores': scores, 'avg': float(avg)}

if __name__ == '__main__':
    jwc = JWC('202.115.175.161')
    username = raw_input(u'username: ')
    password = raw_input(u'password: ')
    if jwc.login(username, password):
        scores = jwc.get_scores('2011-2012', '2')
        for score in scores['scores']:
            print score['name'], score['credit'], score['grade_point'], score['score']
        print u'平均学分绩点:', scores['avg']
