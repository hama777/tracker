#!/usr/bin/python
# -*- coding: utf-8 -*-
#   インスタデータ分析

import os
import csv
import datetime
from ftplib import FTP_TLS

#  25/09/04 v0.02 バグ修正
version = "0.02"       

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
    global hist_date,hist_follow
    hist_date = []
    hist_follow = []
    with open(datafile,encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            date_str = row[0]
            acctid = row[1]
            follow = row[3]
            if acctid != "runa.chocolat.dog" :
                continue 
            hist_date.append(date_str)
            hist_follow.append(follow)

def number_of_followers() :
    for dt , fo in zip(hist_date,hist_follow) :
        out.write(f"['{dt}',{fo}],")

def parse_template() :
    global out 
    f = open(templatefile , 'r', encoding='utf-8')
    out = open(resultfile,'w' ,  encoding='utf-8')
    for line in f :
        if "%follower_graph%" in line :
            number_of_followers()
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

def date_settings():
    global  today_date
    today_date = datetime.date.today()

# ----------------------------------------------------------
main_proc()
