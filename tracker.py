#!/usr/bin/python
# -*- coding: utf-8 -*-

from ast import If
import os
import csv
import datetime
import pandas as pd
import requests
import locale
import shutil
from ftplib import FTP_TLS
from datetime import date,timedelta

version = "0.00"       # 24/01/31
debug = 0     #  1 ... debug
appdir = os.path.dirname(os.path.abspath(__file__))

datafile = appdir + "./data.csv"
templatefile = appdir + "./template.htm"
resultfile = appdir + "./walk.htm"
conffile = appdir + "\\walk.conf"
logfile = appdir + "\\walk.log"

#  統計情報  {キー  yymm  : 値   辞書   キー max min ave  maxdate mindate}
statinfo = {}
allinfo = {}

datelist = []
steplist = []
yymm_list = []
ave_list = []
max_list = []
min_list = []
ftp_host = ftp_user = ftp_pass = ftp_url =  ""
df = ""
out = ""
logf = ""
pixela_url = ""
pixela_token = ""
end_year = 2024  #  データが存在する最終年

lastdate = ""    #  最終データ日付
allrank = ""     #  歩数ランキング
monrank = ""     #  歩数ランキング  今月
dailyindex = []  #  毎日のグラフ日付
dailystep  = []  #  毎日のグラフ歩数
lasthh = 0       #  何時までのデータか
yearinfo = {}    #  年ごとの平均

def main_proc():
    global  datafile,logf
    locale.setlocale(locale.LC_TIME, '')
    #logf = open(logfile,'a',encoding='utf-8')
    #logf.write("\n=== start %s === \n" % datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    
    #read_config()
    read_data()
    #logf.write("\n=== end   %s === \n" % datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    #logf.close()

def read_data():
    global datelist,steplist,lasthh

    f = open("test.txt",'w',encoding='utf-8')
    df = pd.read_csv(datafile,names=['task', 'start', 'end', 'dur','durtime','memo','tag'])
    for index,row in df.iterrows() :
        f.write(row['dur'] + "\n")
        print(row['task'],row['start'],row['end'])
    f.close()



def parse_template() :
    global out 
    f = open(templatefile , 'r', encoding='utf-8')
    out = open(resultfile,'w' ,  encoding='utf-8')
    for line in f :
        if "%lastdate%" in line :
            curdate(line)
            continue
        if "%version%" in line :
            s = line.replace("%version%",version)
            out.write(s)
            continue
        out.write(line)

    f.close()
    out.close()


def read_config() : 
    global ftp_host,ftp_user,ftp_pass,ftp_url,debug,datafile,pixela_url,pixela_token
    if not os.path.isfile(conffile) :
        debug = 1 
        return

    conf = open(conffile,'r', encoding='utf-8')
    ftp_host = conf.readline().strip()
    ftp_user = conf.readline().strip()
    ftp_pass = conf.readline().strip()
    ftp_url = conf.readline().strip()
    datafile = conf.readline().strip()
    pixela_url = conf.readline().strip()
    pixela_token = conf.readline().strip()
    conf.close()

def ftp_upload() : 
    if debug == 1 :
        return 
    with FTP_TLS(host=ftp_host, user=ftp_user, passwd=ftp_pass) as ftp:
        ftp.storbinary('STOR {}'.format(ftp_url), open(resultfile, 'rb'))

def today(s):
    d = datetime.datetime.today().strftime("%m/%d %H:%M")
    s = s.replace("%today%",d)
    out.write(s)

def curdate(s) :
    d = f'{lastdate} {lasthh}時'
    s = s.replace("%lastdate%",d)
    out.write(s)

# ----------------------------------------------------------
main_proc()

