import datetime
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import streamlit as st
from matplotlib import font_manager, rc

from pymongo import MongoClient
from dateutil.relativedelta import relativedelta

import requests
import json

st.set_page_config(layout="wide")
font_path = "C:/Windows/Fonts/NGULIM.TTF"
font = font_manager.FontProperties(fname=font_path).get_name()
rc('font', family=font)

client = MongoClient('mongodb://localhost:27017/')
db = client['swlab']
collection = db['dataset']


# PAPAGO
def translate_with_papago(text, source_lang, target_lang):
    #CLIENT_ID, CLIENT_SECRET = 'tiqA5T0lzVEsmHU21sEb', 'CHZg9FfD50'
    #CLIENT_ID, CLIENT_SECRET = '7xzvsdFxezzwgvI2rozB', 'BWmAlpUANb'
    CLIENT_ID, CLIENT_SECRET = 'UjtULMAjNAE7yEcVWPDO', 'moaDbbcwUL'
    url = 'https://openapi.naver.com/v1/papago/n2mt'
    headers = {
        'Content-Type': 'application/json',
        'X-Naver-Client-Id': CLIENT_ID,
        'X-Naver-Client-Secret': CLIENT_SECRET
    }

    data = {'source': source_lang, 'target':target_lang, 'text': text}

    # post 방식으로 서버 쪽으로 요청
    response = requests.post(url, json.dumps(data), headers=headers)
    #result = response.json()['message']['result']['translatedText']
    result = response.json()

    if "message" in result:
        translated_text = result["message"]["result"]["translatedText"]
        return translated_text
    else:
        return None

def get_dataset():
    dataset = collection.find()
    df = pd.DataFrame(dataset)
    df.loc[(df['site'] == "AI_hub"), 'date'] = df.loc[(df['site'] == "AI_hub"), 'updated_date'][:-2]
    df.loc[(df['site'] == "서울열린데이터광장"), 'date'] = (df.loc[(df['site'] == "서울열린데이터광장"), 'date'].str.slice(0, 10)).replace('.', '-')
    df.loc[(df['date'].isnull()), 'date'] = df.loc[(df['date'].isnull()), 'updated_date'] # date가 없는 데이터는 updated_date로 사용
    df['date'] = pd.to_datetime(df['date'],format='%Y-%m-%d', errors="coerce")
    df = df.astype(str)
    return df

class sidebar:
    def __init__(self):
        self.entire_dataset = get_dataset()
        self.selected_list = []
        self.search_by_sort_list = []
        self.sidebar = st.sidebar
        self.search_by_date_dataset = self.entire_dataset
        self.search_by_site_dataset = self.entire_dataset
        self.serach_by_title_dataset = self.entire_dataset
        self.search_by_algorithm_dataset = self.entire_dataset
        self.search_by_category_dataset = self.entire_dataset
        self.search_by_date()
        self.search_by_site()
        self.search_by_title()
        self.search_by_algorithm()
        self.search_by_category()
        self.search_by_sort()

        if self.sidebar.button("검색"):
            merge_dataset = pd.merge(self.search_by_date_dataset['_id'], self.search_by_site_dataset['_id'])
            merge_dataset = pd.merge(self.serach_by_title_dataset['_id'], merge_dataset)
            merge_dataset = pd.merge(self.search_by_category_dataset['_id'], merge_dataset)
            merge_dataset = pd.merge(self.search_by_algorithm_dataset['_id'], merge_dataset)
            selected_dataset = pd.merge(merge_dataset, self.entire_dataset)
            selected_dataset = selected_dataset.drop('_id', axis=1)

            if self.view:
                self.search_by_sort_list.append(('view', True))
                self.selected_list.append('조회수순')
            if self.latest_time:
                self.search_by_sort_list.append(('date', False))
                self.selected_list.append('최신순')
            if self.download:
                self.search_by_sort_list.append(('download', False))
                self.selected_list.append('다운로드순')
        
            if len(self.search_by_sort_list) == 1:
                selected_dataset = selected_dataset.sort_values(by=[self.search_by_sort_list[0][0]], ascending=[self.search_by_sort_list[0][1]])
            elif len(self.search_by_sort_list) == 2:
                selected_dataset = selected_dataset.sort_values(by=[self.search_by_sort_list[0][0], self.search_by_sort_list[1][0]], ascending=[self.search_by_sort_list[0][1], self.search_by_sort_list[1][1]])
            elif len(self.search_by_sort_list) == 3:
                selected_dataset = selected_dataset.sort_values(by=[self.search_by_sort_list[0][0], self.search_by_sort_list[1][0], self.search_by_sort_list[2][0]], 
                                                                ascending=[self.search_by_sort_list[0][1], self.search_by_sort_list[1][1], self.search_by_sort_list[2][1]])
            
            if self.selected_list:
                st.info(', '.join(self.selected_list) + '을 포함한 데이터셋 검색')
            st.dataframe(selected_dataset)
            st.write(f"검색된 데이터셋 개수: 총 {len(selected_dataset)}개")
            
    def search_by_date(self):
        date = self.sidebar.radio(
            "**📆 기간으로 데이터셋 검색**",
            ["전체", "최근 한 달", "최근 6개월", "최근 1년"])
        self.sidebar.text("\n")
        today = datetime.datetime.now()

        if date == "전체":
            self.search_by_date_dataset = self.entire_dataset
        elif date == "최근 한 달":
            self.selected_list.append(date)
            current_one_month = today - relativedelta(months = 1)
            self.search_by_date_dataset = self.entire_dataset.query('date >= @current_one_month and date <= @today')
        elif date == "최근 6개월":
            self.selected_list.append(date)
            current_six_month = today - relativedelta(months = 6)
            self.search_by_date_dataset = self.entire_dataset.query('date >= @current_six_month and date <= @today')
        elif date == "최근 1년":
            self.selected_list.append(date)
            current_one_year = today - relativedelta(years = 1)
            self.search_by_date_dataset = self.entire_dataset.query('date >= @current_one_year and date <= @today')
        
            # # date_select_frame = df_dataset[df_dataset['date'].isin(pd.date_range(str(select_date[0]), str(select_date[1])))]
            # date_select_frame['date'] = date_select_frame['date'].dt.strftime('%Y-%m-%d')

    def search_by_site(self):
        selected_sites = self.sidebar.multiselect("**🌍 데이터셋 사이트 검색**", ["공공데이터포털", "서울열린데이터광장", "AI_hub", "Kaggle", "Data.gov"])
        self.sidebar.text("\n")
        
        for selected_site in selected_sites:
            select_by_site_dataset = self.entire_dataset.query('site==@selected_site')
            self.search_by_site_dataset = pd.merge(select_by_site_dataset["_id"], self.search_by_site_dataset)
            self.selected_list.append(selected_site)
            
    def search_by_title(self):
        title =self.sidebar.text_input("**📙 제목으로 검색**")
        self.sidebar.text("\n")
        
        if title:
            self.selected_list.append(title)
            self.serach_by_title_dataset = self.entire_dataset.query('title.str.contains(@title)')

    # TODO multiselect or text_input
    def search_by_algorithm(self):
        algorithm = self.sidebar.text_input("**🤖 알고리즘으로 검색**")
        self.sidebar.text("\n")
        
        if algorithm:
            self.selected_list.append(algorithm)
            self.search_by_algorithm_dataset = self.entire_dataset.query('algorithm.str.contains(@algorithm)')

    # TODO add category
    def search_by_category(self):
        selected_category = self.sidebar.multiselect("**📁 카테고리로 검색**", ["교육", "재정금융", "사회복지", "식품건강", "보건의료", "재난안전", "교통물류", "환경기상", "과학기술", "농축축산", "법률"])
        self.sidebar.text("\n")

        category_papago = []
        for selected in selected_category:
            category_papago.append(translate_with_papago(selected, "ko", "en"))
        self.category = category_papago  # 클래스 변수로 선택된 사이트 저장

        if selected_category:
            for index in range(len(selected_category)):
                category_query = selected_category[index] + '|' + category_papago[index]
                select_by_category_dataset = self.entire_dataset.query('category.str.contains(@category_query, case=False)')
                self.search_by_category_dataset = pd.merge(select_by_category_dataset["_id"], self.search_by_category_dataset)
                self.selected_list.append(selected_category[index])

    def search_by_sort(self):
        self.view = self.sidebar.checkbox("**조회순으로 검색**")
        self.latest_time = self.sidebar.checkbox("**최신순으로 검색**")
        self.download = self.sidebar.checkbox("**다운로드순으로 검색**")


st.title("📈 메타데이터셋 검색 시스템")
sidebar = sidebar()


