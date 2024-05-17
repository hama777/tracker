#!/usr/bin/python
# -*- coding: utf-8 -*-

from ast import If
import os
import csv
import datetime
import pandas as pd
import locale
import shutil
from ftplib import FTP_TLS
from datetime import date,timedelta
import calendar

version = "0.04"       # 24/05/17

# TODO:  pixela

debug = 0     #  1 ... debug
appdir = os.path.dirname(os.path.abspath(__file__))

dataname = "/CSVFile.csv"
datafile = ""
backfile = appdir + "/save.txt"
datadir = appdir
templatefile = appdir + "/sleep_templ.htm"
resultfile = appdir + "/sleep.htm"
conffile = appdir + "/tracker.conf"
logfile = appdir + "\\tracker.log"
pastdata = appdir + "/pastdata.txt"
rawdata = appdir + "/rawdata.txt"
past_pf_dic = []   #  過去の月別時間 pf   辞書  キー  hhmm   値  分

ftp_host = ftp_user = ftp_pass = ftp_url =  ""
df = ""
out = ""
logf = ""
pixela_url = ""
pixela_token = ""

def main_proc():
    global  datafile,logf

    locale.setlocale(locale.LC_TIME, '')

    date_settings()
    read_config()
    read_data()
    parse_template()

    #ftp_upload()

def read_data():
    global df,datafile

    datafile = datadir + dataname
    date_start = []
    date_end = []
    process_list = []
    if debug == 1 :
        if not os.path.isfile(datafile) :
            datafile = backfile
    with open(datafile,encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] == "睡眠" :
                date_start.append(row[1])
                date_end.append(row[2])
                tt = row[3].replace("'","")
                tt = conv_hhmm_mm(tt) 
                process_list.append(tt)

    df = pd.DataFrame(list(zip(date_start,date_end,process_list)), columns = ['start','end','sleep'])
    df["start"] = pd.to_datetime(df["start"])
    df["end"] = pd.to_datetime(df["end"])
    #df = df.set_index("date")

    #print(df)

def daily_graph() :
    for _ , row in df.tail(30).iterrows() :    
        str_date = row['end'].strftime("%d")
        stime = int(row['sleep'])
        hh = int(stime / 60)
        mm = stime % 60

        out.write(f"['{str_date}',[{hh},{mm},0]],")
        #out.write(f"['{str_date}',{row['sleep']}],")

def start_time_graph() :
    for _ , row in df.tail(30).iterrows() :    
        str_date = row['end'].strftime("%d")
        hh  = row['start'].strftime("%H")
        mm  = row['start'].strftime("%M")
        #print(str_date,hh,mm)
        out.write(f"['{str_date}',[{hh},{mm},0]],")

def date_settings():
    global  today_date,today_mm,today_dd,today_yy,yesterday,today_datetime
    today_datetime = datetime.datetime.today()
    today_date = datetime.date.today()
    today_mm = today_date.month
    today_dd = today_date.day
    today_yy = today_date.year
    yesterday = today_date - timedelta(days=1)


def conv_hhmm_mm(hhmm) :
    if hhmm == "" :
        return 0
    hh,mm = hhmm.split(":")
    return int(hh) * 60 + int(mm)

#   yy/mm 形式の文字列を入力し int型の yymm を返す
def conv_yymm(yymm) :
    yy,mm = yymm.split("/")
    return int(yy) * 100 + int(mm)
    

def ftp_upload() : 
    if debug == 1 :
        return 
    with FTP_TLS(host=ftp_host, user=ftp_user, passwd=ftp_pass) as ftp:
        ftp.storbinary('STOR {}'.format(ftp_url), open(resultfile, 'rb'))

def today(s):
    d = today_datetime.strftime("%m/%d %H:%M")
    s = s.replace("%today%",d)
    out.write(s)

def parse_template() :
    global out 
    f = open(templatefile , 'r', encoding='utf-8')
    out = open(resultfile,'w' ,  encoding='utf-8')
    for line in f :
        if "%daily_graph%" in line :
            daily_graph()
            continue
        if "%start_time_graph%" in line :
            start_time_graph()
            continue
        if "%daily_movav%" in line :
            daily_movav_com(0)
            continue
        if "%daily_movav_vn%" in line :
            daily_movav_com(1)
            continue
        if "%month_info%" in line :
            month_info()
            continue
        if "%ranking%" in line :
            ranking()
            continue
        if "%ranking_month%" in line :
            ranking_month()
            continue
        if "%month_graph%" in line :
            month_graph_com(df_mon_pf)
            continue
        if "%month_graph_vn%" in line :
            month_graph_com(df_mon_vn)
            continue
        if "%year_graph_pf%" in line :
            year_graph_com(df_yy_pf)
            continue
        if "%year_graph_vn%" in line :
            year_graph_com(df_yy_vn)
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

# ----------------------------------------------------------
main_proc()
