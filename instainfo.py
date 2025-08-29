#!/usr/bin/python
# -*- coding: utf-8 -*-

import instaloader
import os
import csv
import datetime

#  25/08/29 v0.02
version = "0.02"       

debug = 0     #  1 ... debug
appdir = os.path.dirname(os.path.abspath(__file__))

conffile = appdir + "/insta.conf"
acctdata = appdir + "/acct.txt"
resultfile = appdir + "/instares.txt"
instance = ""
acctinfo = {}

def main_proc():
    global instance
    #read_config() 
    date_settings()
    read_acctdata()

    # Instaloader インスタンス作成
    instance = instaloader.Instaloader()
    get_all_acctinfo() 

def get_all_acctinfo() :
    out = open(resultfile,'a' ,  encoding='utf-8')
    date_str = today_date.strftime("%y/%m/%d")
    for  acct,v in acctinfo.items() :
        post,follow = get_acctinfo(acct)
        print(acct,post,follow)
        out.write(f'{date_str}\t{acct}\t{post}\t{follow}\n')
    out.close()

def get_acctinfo(acct) :

    # プロフィール取得
    profile = instaloader.Profile.from_username(instance.context, acct)

    # 投稿数、フォロワー数を取得
    post_count = profile.mediacount
    follower_count = profile.followers
    return post_count,follower_count

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

def date_settings():
    global  today_date
    today_date = datetime.date.today()

# ----------------------------------------------------------
main_proc()
