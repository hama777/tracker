#!/usr/bin/python
# -*- coding: utf-8 -*-

from ast import If
import os
import csv
import datetime
import pandas as pd
import locale
from ftplib import FTP_TLS
from datetime import date,timedelta

version = "1.06"       # 24/06/11

# TODO:  pixela

debug = 0     #  1 ... debug
appdir = os.path.dirname(os.path.abspath(__file__))

dataname = "/CSVFile.csv"
datafile = appdir + "/save.txt"
datadir = appdir
templatefile = appdir + "/sleep_templ.htm"
resultfile = appdir + "/sleep.htm"
conffile = appdir + "/tracker.conf"
logfile = appdir + "\\tracker.log"
pastdata = appdir + "/pastdata.txt"
rawdata = appdir + "/rawdata.txt"
past_pf_dic = []   #  過去の月別時間 pf   辞書  キー  hhmm   値  分
month_info_list = []   # 月ごとのリスト  要素は 年月 平均時間  平均就寝時刻  平均起床時刻

ftp_host = ftp_user = ftp_pass = ftp_url =  ""
df = ""
out = ""
logf = ""
pixela_url = ""
pixela_token = ""

def main_proc():
    global  logf,ftp_url

    locale.setlocale(locale.LC_TIME, '')

    date_settings()
    read_config()
    ftp_url = ftp_url.replace("index.htm","sleep.htm")
    read_data()
    create_month_info()
    parse_template()

    ftp_upload()

def read_data():
    global df

    date_start = []
    date_end = []
    process_list = []
    index_date_list = []
    with open(datafile,encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] == "睡眠" :
                tt = row[1][11:]     #  時刻部分のみ取り出す  ex. 23:26:00
                date_start.append(tt)
                tt = row[2][11:]
                date_end.append(tt)
                tt = row[3].replace("'","")
                tt = conv_hhmm_mm(tt) 
                process_list.append(tt)
                s = row[2][0:10]   # 先頭の日付部分のみ取り出す  ex. 2024-01-02
                index_date_list.append(s)

    df = pd.DataFrame(list(zip(index_date_list,date_start,date_end,process_list)), 
                      columns = ['date','start','end','sleep'])
    df["start"] = pd.to_datetime(df["start"])
    df["end"] = pd.to_datetime(df["end"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")

    #print(df)

def daily_graph() :
    #print(df.tail(30))
    for index , row in df.tail(30).iterrows() :    
        str_date = index.strftime("%d")
        stime = int(row['sleep'])
        hh = int(stime / 60)
        mm = stime % 60

        out.write(f"['{str_date}',[{hh},{mm},0]],")
        #out.write(f"['{str_date}',{row['sleep']}],")

def month_graph() :
    #print(df.tail(30))
    for dt in month_info_list :    
        yymm = dt[0]
        tm = dt[1]
        yy = yymm.year
        mon = yymm.month

        out.write(f"['{yy}/{mon}',{tm}],")
        #out.write(f"['{str_date}',{row['sleep']}],")

def start_time_graph() :
    for index , row in df.tail(90).iterrows() :    
        str_date = f'{index.strftime("%m")}/{index.strftime("%d")}'
        hh  = row['start'].strftime("%H")
        mm  = row['start'].strftime("%M")
        #print(str_date,hh,mm)
        out.write(f"['{str_date}',[{hh},{mm},0]],")

def end_time_graph() :
    for index , row in df.tail(90).iterrows() :    
        str_date = f'{index.strftime("%m")}/{index.strftime("%d")}'
        hh  = row['end'].strftime("%H")
        mm  = row['end'].strftime("%M")
        #print(str_date,hh,mm)
        out.write(f"['{str_date}',[{hh},{mm},0]],")

def ranking_sleep_time_max() :
    sort_df = df.copy()
    sort_df = sort_df.sort_values('sleep',ascending=False)
    ranking_sleep_time_com(sort_df)

def ranking_sleep_time_min() :
    sort_df = df.copy()
    sort_df = sort_df.sort_values('sleep',ascending=True)
    ranking_sleep_time_com(sort_df)

def ranking_sleep_time_com(sort_df) :
    i = 0 
    for index , row in sort_df.head(10).iterrows() :  
        i = i + 1 
        str_date = f'{index.strftime("%m")}/{index.strftime("%d")}'
        stime = int(row['sleep'])
        hh = int(stime / 60)
        mm = stime % 60
        out.write(f"<tr><td align='right'>{i}</td><td align='right'>{hh}:{mm:02}</td><td>{str_date}</td></tr>")
    

# 月ごとの情報 month_info_list を作成する
# month_info_list は月ごとのリスト  要素は 年月 平均時間  平均就寝時刻  平均起床時刻
def create_month_info() :
    global month_info_list
    yymm_list = []
    sleep_list = []
    max_sleep = []
    start_list = []
    end_list = []
    max_start = []
    max_end = []
    min_sleep = []
    min_start = []
    min_end = []
    m_ave = df.resample(rule = "ME").mean().to_dict()
    m_max = df.resample(rule = "ME").max().to_dict()
    m_min = df.resample(rule = "ME").min().to_dict()
    for d, tm in m_ave['sleep'].items():
        yymm_list.append(d)
        sleep_list.append(tm)
    for _, tm in m_ave['start'].items():
        start_list.append(tm)
    for _, tm in m_ave['end'].items():
        end_list.append(tm)
    for _, tm in m_max['sleep'].items():
        max_sleep.append(tm)
    for _, tm in m_max['start'].items():
        max_start.append(tm)
    for _, tm in m_max['end'].items():
        max_end.append(tm)
    for _, tm in m_min['sleep'].items():
        min_sleep.append(tm)
    for _, tm in m_min['start'].items():
        min_start.append(tm)
    for _, tm in m_min['end'].items():
        min_end.append(tm)

    for yymm,sp,max_sp,min_sp,s,max_s,min_s,e,max_e,min_e in zip(yymm_list,sleep_list,max_sleep,min_sleep,
                                        start_list,max_start,min_start,
                                        end_list,max_end,min_end  ) :
        mlist = [yymm,sp,max_sp,min_sp,s,max_s,min_s,e,max_e,min_e]
        month_info_list.append(mlist)

    #print(month_info_list)

def month_info_table() :
    for dt in month_info_list :
        yymm = dt[0]
        yy = yymm.year - 2000
        mon = yymm.month
        sleep  = int(dt[1])
        max_sleep  = int(dt[2])
        min_sleep  = int(dt[3])
        start  = dt[4].time()
        max_start  = dt[5].time()
        min_start  = dt[6].time()
        end  = dt[7].time()
        max_end  = dt[8].time()
        min_end  = dt[9].time()
        #print(yy,mm,sleep,start,end)
        out.write(f'<tr><td>{yy}/{mon:02}</td><td  align="right">{sleep//60}:{sleep%60:02}</td>'
                  f'<td  align="right">{max_sleep//60}:{max_sleep%60:02}</td>'
                  f'<td  align="right">{min_sleep//60}:{min_sleep%60:02}</td>'
                  f'<td>{start.hour}:{start.minute:02}</td>'
                  f'<td>{max_start.hour}:{max_start.minute:02}</td><td>{min_start.hour}:{min_start.minute:02}</td>'
                  f'<td>{end.hour}:{end.minute:02}</td>'
                  f'<td>{max_end.hour}:{max_end.minute:02}</td><td>{min_end.hour}:{min_end.minute:02}</td></tr>\n')

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
        if "%month_graph%" in line :
            month_graph()
            continue
        if "%start_time_graph%" in line :
            start_time_graph()
            continue
        if "%end_time_graph%" in line :
            end_time_graph()
            continue
        if "%daily_movav%" in line :
            daily_movav_com(0)
            continue
        if "%daily_movav_vn%" in line :
            daily_movav_com(1)
            continue
        if "%month_info%" in line :
            month_info_table()
            continue
        if "%rank_sleep_max% " in line :
            ranking_sleep_time_max()
            continue
        if "%rank_sleep_min% " in line :
            ranking_sleep_time_min()
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
