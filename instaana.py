#!/usr/bin/python
# -*- coding: utf-8 -*-
#   インスタデータ分析

import os
import csv
import datetime
from ftplib import FTP_TLS

#  25/09/09 v0.03 フォロワー数比較グラフ追加  
version = "0.03"       

debug = 0     #  1 ... debug
appdir = os.path.dirname(os.path.abspath(__file__))

acctdata = appdir + "/instaacct.txt"
datafile = appdir + "/instadata.txt"
templatefile = appdir + "/insta_templ.htm"
resultfile = appdir + "/insta.htm"
conffile = appdir + "/tracker.conf"

acctinfo = {}    #  キー  アカウントID  値  辞書  キー  acctname アカウント名   start 記録開始日付

def main_proc():
    global ftp_url
    read_config() 
    if debug == 0 :
        ftp_url = ftp_url.replace("index.htm","insta.htm")
    date_settings()
    read_acctdata()
    read_resdata()
    parse_template()
    ftp_upload()

def read_acctdata() :
    global acctinfo
    with open(acctdata,encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            acct = row[0]
            info = {}
            info['acctname'] = row[1]
            info['start'] = row[2]
            acctinfo[acct] = info
    #print(acctinfo)

def read_resdata() :
    global hist_date,hist_follow,insta_info
    hist_date = []
    hist_follow = []
    insta_info = {}
    with open(datafile,encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            date_str = row[0]
            acctid = row[1]
            post = row[2]
            follow = row[3]
            acct_val = {}
            acct_val['follow'] = follow
            acct_val['post'] = post
            insta_info[acctid] = acct_val
            
            if acctid != "runa.chocolat.dog" :
                continue 
            hist_date.append(date_str)
            hist_follow.append(follow)
    #print(acct_info)

def number_of_followers() :
    for dt , fo in zip(hist_date,hist_follow) :
        date_str = dt[3:]
        out.write(f"['{date_str}',{fo}],")

def compare_follower() :
    bar_color_list = ['#32a89d', '#f39c12', '#3498db', '#e74c3c']
    n= 0 
    for accid,v in insta_info.items() :
        follow = v['follow']
        act = acctinfo[accid]
        actname = act['acctname']
        out.write(f"['{actname}',{follow},'{bar_color_list[n]}'],")
        n += 1


def date_settings():
    global  today_date,today_mm,today_dd,today_yy,lastdate,today_datetime
    today_datetime = datetime.datetime.today()
    today_date = datetime.date.today()
    today_mm = today_date.month
    today_dd = today_date.day
    today_yy = today_date.year

def today(s):
    global today_date
    d = today_datetime.strftime("%m/%d %H:%M")
    s = s.replace("%today%",d)
    out.write(s)

def parse_template() :
    global out 
    f = open(templatefile , 'r', encoding='utf-8')
    out = open(resultfile,'w' ,  encoding='utf-8')
    for line in f :
        if "%follower_graph%" in line :
            number_of_followers()
            continue
        if "%compare_follower_graph%" in line :
            compare_follower()
            continue
        if "%version%" in line :
            s = line.replace("%version%",version)
            out.write(s)
            continue
        if "%today%" in line :
            today(line)
            continue

        out.write(line)

    f.close()
    out.close()

def ftp_upload() : 
    if debug == 1 :
        return 
    with FTP_TLS(host=ftp_host, user=ftp_user, passwd=ftp_pass) as ftp:
        ftp.storbinary('STOR {}'.format(ftp_url), open(resultfile, 'rb'))
    print("ftp " + ftp_url)

def read_config() : 
    global ftp_host,ftp_user,ftp_pass,ftp_url,debug,datadir,pixela_url,pixela_token
    if not os.path.isfile(conffile) :
        debug = 1 
        return

    conf = open(conffile,'r', encoding='utf-8')
    ftp_host = conf.readline().strip()
    ftp_user = conf.readline().strip()
    ftp_pass = conf.readline().strip()
    ftp_url = conf.readline().strip()
    datadir = conf.readline().strip()
    pixela_url = conf.readline().strip()
    pixela_token = conf.readline().strip()
    debug = int(conf.readline().strip())
    conf.close()
    print(ftp_url)

# ----------------------------------------------------------
main_proc()
