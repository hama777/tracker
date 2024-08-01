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
import math

version = "1.19"       # 24/07/30

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
pastdata = appdir + "/sleeppast.txt"
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
    read_pastdata()
    create_month_info()
    parse_template()

    ftp_upload()

#   df の作成
#   df の形式   date  起床基準の日付  date型   start 数値 分単位  end 就寝時刻 分単位  sleep 睡眠時間  
#   就寝時刻12時超に対応するため start end は 0:00 基準の分単位で持つ  ex.  24:10 なら  24*60+10 = 1450
def read_data():
    global df

    date_start = []
    date_end = []
    sleep_list = []
    index_date_list = []
    with open(datafile,encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] == "睡眠" :
                t = conv_datetime_to_minute(row[1])
                date_start.append(t)
                t = conv_datetime_to_minute(row[2])
                date_end.append(t)
                tt = row[3].replace("'","")
                tt = conv_hhmm_mm(tt) 
                sleep_list.append(tt)
                s = row[2][0:10]   # 先頭の日付部分のみ取り出す  ex. 2024-01-02
                index_date_list.append(s)

    df = pd.DataFrame(list(zip(index_date_list,date_start,date_end,sleep_list)), 
                      columns = ['date','start','end','sleep'])
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")

#  yyyy-mm-dd hh:mm 形式(str型)を分単位の数値に変換する
def conv_datetime_to_minute(dt) :
    hh = int(dt[11:13])   # hh 部分を取り出す
    mm = int(dt[14:])     # mm 部分を取り出す
    return hh * 60 + mm

def read_pastdata():
    global df_past
    df_past = pd.read_csv(pastdata,  sep='\t')

def daily_graph() :
    for index , row in df.tail(30).iterrows() :    
        str_date = index.strftime("%d")
        stime = int(row['sleep'])
        #hh = int(stime / 60)
        #mm = stime % 60

        out.write(f"['{str_date}',[{conv_time_to_graph_str(stime)}]],")
        #out.write(f"['{str_date}',[{hh},{mm},0]],")

#   月別平均睡眠時間グラフ
def month_graph() :
    for index , row in df_past.iterrows() :  
        yy = int(row['yymm'].split("/")[0]) - 2000
        mon = int(row['yymm'].split("/")[1]) 
        hh = int(row['sleep_ave'].split(":")[0])
        mm = int(row['sleep_ave'].split(":")[1])
        tm = hh * 60 + mm 
        out.write(f"['{yy}{mon:02}',[{hh},{mm},0]],")

    for dt in month_info_list :    
        yymm = dt[0]
        #tm = dt[1]
        #hh = int(tm) // 60
        #mm = int(tm) % 60
        yy = yymm.year - 2000
        mon = yymm.month
        out.write(f"['{yy}{mon:02}',[{conv_time_to_graph_str(dt[1])}]],")

#   月別平均就寝時刻グラフ
def month_start_time_graph() :
    for index , row in df_past.iterrows() :  
        if type(row['start_ave']) is not str :
            continue 
        yy = int(row['yymm'].split("/")[0]) - 2000
        mon = int(row['yymm'].split("/")[1]) 
        hh = int(row['start_ave'].split(":")[0])
        mm = int(row['start_ave'].split(":")[1])
        if hh < 8 :
            hh = hh + 24
        tm = hh * 60 + mm 
        out.write(f"['{yy}{mon:02}',[{hh},{mm},0]],")

    for dt in month_info_list :
        yymm = dt[0]
        yy = yymm.year - 2000
        mon = yymm.month
        #start  = dt[4]        # 月平均就寝時刻
        #hh  = start // 60 
        #mm  = start % 60 
        out.write(f"['{yy}{mon:02}',[{conv_time_to_graph_str(dt[4])}]],")   # dt[4] = 月平均就寝時刻

#   月別平均起床時刻グラフ
def month_end_time_graph() :
    for index , row in df_past.iterrows() :  
        if type(row['end_ave']) is not str :
            continue 
        yy = int(row['yymm'].split("/")[0]) - 2000
        mon = int(row['yymm'].split("/")[1]) 
        hh = int(row['end_ave'].split(":")[0])
        mm = int(row['end_ave'].split(":")[1])
        out.write(f"['{yy}{mon:02}',[{hh},{mm},0]],")

    for dt in month_info_list :
        yymm = dt[0]
        yy = yymm.year - 2000
        mon = yymm.month
        #start  = dt[7]             # 月平均起床時刻
        #hh  = start // 60 
        #mm  = start % 60 
        out.write(f"['{yy}{mon:02}',[{conv_time_to_graph_str(dt[7])}]],")   # dt[7] 月平均起床時刻 

def start_time_graph() :
    for index , row in df.tail(90).iterrows() :    
        str_date = f'{index.strftime("%m")}/{index.strftime("%d")}'
        out.write(f"['{str_date}',[{conv_time_to_graph_str(row['start'])}]],")

def end_time_graph() :
    for index , row in df.tail(90).iterrows() :    
        str_date = f'{index.strftime("%m")}/{index.strftime("%d")}'
        out.write(f"['{str_date}',[{conv_time_to_graph_str(row['end'])}]],")

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
        if index.date() == lastdate :      # 最終データなら赤字にする
            str_date = f'<span class=red>{str_date}</span>'

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
    std_sleep = []
    std_start = []
    std_end = []
    m_ave = df.resample(rule = "ME").mean().to_dict()
    m_max = df.resample(rule = "ME").max().to_dict()
    m_min = df.resample(rule = "ME").min().to_dict()
    m_std = df.resample(rule = "ME").min().to_dict()
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
    for _, tm in m_std['sleep'].items():
        std_sleep.append(tm)
    for _, tm in m_std['start'].items():
        std_start.append(tm)
    for _, tm in m_std['end'].items():
        std_end.append(tm)

    for yymm,sp,max_sp,min_sp,s,max_s,min_s,e,max_e,min_e,std_sp,std_s,std_e in zip(yymm_list,sleep_list,max_sleep,min_sleep,
                                        start_list,max_start,min_start,
                                        end_list,max_end,min_end,std_sleep,std_start,std_end  ) :
        mlist = [yymm,sp,max_sp,min_sp,s,max_s,min_s,e,max_e,min_e,std_sp,std_s,std_e]
        month_info_list.append(mlist)

def month_info_table() :
    for dt in month_info_list :
        yymm = dt[0]
        yy = yymm.year - 2000
        mon = yymm.month
        sleep  = int(dt[1])
        max_sleep  = int(dt[2])
        min_sleep  = int(dt[3])
        start  = conv_time_to_str(dt[4])
        max_start  = conv_time_to_str(dt[5])
        min_start  = conv_time_to_str(dt[6])
        end  = conv_time_to_str(dt[7])
        max_end  = conv_time_to_str(dt[8])
        min_end  = conv_time_to_str(dt[9])
        std_sleep =  dt[10]
        std_start =  dt[11]
        std_end =  dt[12]
        out.write(f'<tr><td>{yy}/{mon:02}</td><td  align="right">{sleep//60}:{sleep%60:02}</td>'
                  f'<td  align="right">{std_sleep}</td>'
                  f'<td  align="right">{min_sleep//60}:{min_sleep%60:02}</td>'
                  f'<td  align="right">{max_sleep//60}:{max_sleep%60:02}</td>'
                  f'<td  align="right">{start}</td>'
                  f'<td  align="right">{std_start}</td>'
                  f'<td>{min_start}</td><td>{max_start}</td>'
                  f'<td  align="right">{end}</td>'
                  f'<td  align="right">{std_end}</td>'
                  f'<td>{min_end}</td><td>{max_end}</td></tr>\n')
    all_statistics()

def all_statistics() :
    sleep_ave = int(df['sleep'].mean())
    min_sleep = df['sleep'].min()
    max_sleep = df['sleep'].max()
    start  = conv_time_to_str(int(df['start'].mean()))
    min_start = conv_time_to_str(df['start'].min())
    max_start = conv_time_to_str(df['start'].max())
    end  = conv_time_to_str(int(df['end'].mean()))
    min_end  = conv_time_to_str(df['end'].min())
    max_end  = conv_time_to_str(df['end'].max())
    out.write(f'<tr><td class=all>全体</td><td class=all align="right">{sleep_ave//60}:{sleep_ave%60:02}</td>'
              f'<td class=all align="right">--</td>'
              f'<td class=all align="right">{min_sleep//60}:{min_sleep%60:02}</td>'
              f'<td class=all align="right">{max_sleep//60}:{max_sleep%60:02}</td>'
              f'<td class=all align="right">{start}</td>'
              f'<td class=all align="right">--</td>'
              f'<td class=all>{min_start}</td><td class=all>{max_start}</td>'
              f'<td class=all align="right">{end}</td>'
              f'<td class=all align="right">--</td>'
              f'<td class=all>{min_end}</td><td class=all>{max_end}</td></tr>\n')

#   時刻 int を形式 hh:mm の文字列に変換する
def conv_time_to_str(timedata) :
    hh = int(timedata) // 60
    mm = int(timedata) % 60
    s = f'{hh}:{mm:02}'
    return s

#   時刻 int をグラフ用の形式 hh,mm,0 の文字列に変換する
def conv_time_to_graph_str(timedata) :
    hh = int(timedata) // 60
    mm = int(timedata) % 60
    s = f'{hh},{mm},0'
    return s

def date_settings():
    global  today_date,today_mm,today_dd,today_yy,lastdate,today_datetime
    today_datetime = datetime.datetime.today()
    today_date = datetime.date.today()
    today_mm = today_date.month
    today_dd = today_date.day
    today_yy = today_date.year
    lastdate = today_date - timedelta(days=1)


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
        if "%month_start_graph%" in line :
            month_start_time_graph()
            continue
        if "%month_end_graph%" in line :
            month_end_time_graph()
            continue
        if "%start_time_graph%" in line :
            start_time_graph()
            continue
        if "%end_time_graph%" in line :
            end_time_graph()
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
