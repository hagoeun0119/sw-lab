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
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.loc[(df['site'] == "AI_hub"), 'date'] = df.loc[(df['site'] == "AI_hub"), 'updated_date'][:-2]
    df.loc[(df['site'] == "서울열린데이터광장"), 'date'] = (df.loc[(df['site'] == "서울열린데이터광장"), 'date'].str.slice(0, 10)).replace('.', '-')
    df.loc[(df['date'].isnull()), 'date'] = df.loc[(df['date'].isnull()), 'updated_date'] # date가 없는 데이터는 updated_date로 사용
    df['date'] = pd.to_datetime(df['date'],format='%Y-%m-%d', errors="coerce")
    df['updated_date'] = pd.to_datetime(df['updated_date'],format='%Y-%m-%d', errors="coerce")
    df['created_date'] = pd.to_datetime(df['created_date'],format='%Y-%m-%d', errors="coerce")
    df['updated_date'] = df['updated_date'].dt.strftime('%Y-%m-%d')
    df['created_date'] = df['created_date'].dt.strftime('%Y-%m-%d')
    df['download'] = pd.to_numeric(df['download'], errors='coerce')
    df['view'] = pd.to_numeric(df['view'], errors='coerce')
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

        self.site_mapping = {
            '공공데이터포털': 'Public Data Portal',
            '서울열린데이터광장': 'Seoul Open Data Plaza',
            'AI hub' : 'AI_hub',
            'Kaggle' : 'Kaggle',
            'Data.gov' : 'Data.gov'
        }
        
        self.category_mapping = {
            '교육': 'Education',
            '재정금융': 'Finance',
            '식품건강': 'Food Health',
            '문화관광': 'Culture Travel',
            '보건의료': 'Healthcare',
            '재난안전': 'Disaster Safety',
            '교통물류': 'Transportation',
            '환경기상': 'Environment',
            '과학기술': 'Science Technology',
            '농축축산': 'Agriculture',
            '사회복지': 'Social Welfare', 
            '법률': 'Law'
        }

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

            if self.view:
                self.search_by_sort_list.append(('view', False))
                self.selected_list.append('By Views')
            if self.latest_time:
                self.search_by_sort_list.append(('date', True))
                self.selected_list.append('Last updated')
            if self.download:
                self.search_by_sort_list.append(('download', False))
                self.selected_list.append('By Downloads')

            if len(self.search_by_sort_list) == 1:
                selected_dataset = selected_dataset.sort_values(by=[self.search_by_sort_list[0][0]], ascending=[self.search_by_sort_list[0][1]]) 
            elif len(self.search_by_sort_list) == 2:
                selected_dataset = selected_dataset.sort_values(by=[self.search_by_sort_list[0][0], self.search_by_sort_list[1][0]], ascending=[self.search_by_sort_list[0][1], self.search_by_sort_list[1][1]])
            elif len(self.search_by_sort_list) == 3:
                selected_dataset = selected_dataset.sort_values(by=[self.search_by_sort_list[0][0], self.search_by_sort_list[1][0], self.search_by_sort_list[2][0]], 
                                                                ascending=[self.search_by_sort_list[0][1], self.search_by_sort_list[1][1], self.search_by_sort_list[2][1]])
            if self.selected_list:
                st.info('Search Keyword: ' + ', '.join(self.selected_list))

            selected_dataset = selected_dataset.drop('_id', axis=1)
            selected_dataset = selected_dataset.astype(str)
            selected_dataset['download'] = pd.to_numeric(selected_dataset['download'], errors='coerce')
            selected_dataset['view'] = pd.to_numeric(selected_dataset['view'], errors='coerce')
            selected_dataset.reset_index(drop=True, inplace=True)

            st.dataframe(selected_dataset)
            st.write(f"Total number of datasets: {len(selected_dataset)}")
            self.result_dataset = selected_dataset
        else:
            self.result_dataset = self.entire_dataset
            
    def search_by_date(self):
        date = self.sidebar.radio(
            "**📆 Search by Period**",
            ["Total", "Last month", "Last 6 months", "Last year"])
        self.sidebar.text("\n")
        today = datetime.datetime.now()

        if date == "Total":
            self.search_by_date_dataset = self.entire_dataset
        elif date == "Last month":
            self.selected_list.append(date)
            current_one_month = today - relativedelta(months = 1)
            self.search_by_date_dataset = self.entire_dataset.query('date >= @current_one_month and date <= @today')
        elif date == "Last 6 months":
            self.selected_list.append(date)
            current_six_month = today - relativedelta(months = 6)
            self.search_by_date_dataset = self.entire_dataset.query('date >= @current_six_month and date <= @today')
        elif date == "Last year":
            self.selected_list.append(date)
            current_one_year = today - relativedelta(years = 1)
            self.search_by_date_dataset = self.entire_dataset.query('date >= @current_one_year and date <= @today')

    def search_by_site(self):
        selected_sites = self.sidebar.multiselect("**🌍 Search Dataset Site**", ["Public Data Portal", "Seoul Open Data Plaza", "AI_hub", "Kaggle", "Data.gov"])
        self.sidebar.text("\n")
        self.selected_sites = selected_sites  # 클래스 변수로 선택된 사이트 저장
        
        reversed_site_mapping = dict(map(reversed, self.site_mapping.items()))
        for index in range(len(self.selected_sites)):
            self.selected_sites[index] = reversed_site_mapping[self.selected_sites[index]]
            self.selected_list.append(self.site_mapping[self.selected_sites[index]])
        self.search_by_site_dataset = self.entire_dataset[self.entire_dataset['site'].isin(self.selected_sites)]
        
    def search_by_title(self):
        title = self.sidebar.text_input("**📙 Search by title**")
        self.ko_title = translate_with_papago(title, "en", "ko")
        self.en_title = translate_with_papago(title, "ko", "en")
        self.sidebar.text("\n")
        self.title = title  # 클래스 변수로 선택된 사이트 저장
        
        if title:
            title_query = self.ko_title + '|' + self.en_title
            self.selected_list.append(title)
            self.serach_by_title_dataset = self.entire_dataset.query('title.str.contains(@title_query, case=False)')

    def search_by_algorithm(self):
        algorithm = self.sidebar.text_input("**🤖 Search by algorithm**")
        self.sidebar.text("\n")
        self.algorithm = algorithm
        
        if algorithm:
            self.selected_list.append(algorithm)
            self.search_by_algorithm_dataset = self.entire_dataset.query('algorithm.str.contains(@algorithm, case=False)')

    def search_by_category(self):
        selected_category = self.sidebar.multiselect("**📁 Find with Category**", ["Education", "Finance", "Healthcare", "Food Health", "Social Welfare", "Disaster Safety", "Culture Travel", "Transportation", "Environment", "Science Technology", "Agriculture", "Law"])
        self.sidebar.text("\n")
        self.category = selected_category  # 클래스 변수로 선택된 사이트 저장
        self.category_ko = [] 

        reversed_category_mapping = dict(map(reversed, self.category_mapping.items()))
        for index in range(len(selected_category)):
            self.category_ko.append(reversed_category_mapping[self.category[index]])

        if selected_category:               
            en_category_dataset = self.entire_dataset[self.entire_dataset['category'].isin(self.category)]
            ko_category_dataset = self.entire_dataset[self.entire_dataset['category'].isin(self.category_ko)]
            self.search_by_category_dataset = pd.concat([en_category_dataset, ko_category_dataset])
            self.selected_list.append(selected_category[index])
        else:
            self.category = list(self.category_mapping.values())
            self.category_ko = list(self.category_mapping.keys())

    def search_by_sort(self):
        self.view = self.sidebar.checkbox("**By Views**")
        self.latest_time = self.sidebar.checkbox("**Last updated**")
        self.download = self.sidebar.checkbox("**By Downloads**")

    # 데이터 시각화
    def visualize_site_counts(self, dataset, selected_sites=None, title=None, algorithm=None, category=None):

        self.result_dataset['site'] = self.result_dataset['site'].map(self.site_mapping) # 사이트 영어로 변환

        if  len(self.result_dataset['site']) != 0:
            site_counts = self.result_dataset['site'].value_counts()
            fig_site_counts, ax_site_counts = plt.subplots(figsize=(10, 6))
            site_counts.plot(kind='bar', color='skyblue', ax=ax_site_counts)
            ax_site_counts.set_ylabel('Number of datasets', fontsize=15)
            ax_site_counts.tick_params(axis='x', labelrotation=45)

            st.pyplot(fig_site_counts)
            st.table(site_counts.reset_index().rename(columns={"index": "사이트", "site": "데이터셋 개수"}))
            return fig_site_counts

    def visualize_top_categories(self, dataset, selected_sites=None, title=None, algorithm=None, category=None):

        if  len(self.result_dataset['category']) != 0:      
            en_category_dataset = self.result_dataset[self.result_dataset['category'].isin(self.category)]
            ko_category_dataset = self.result_dataset[self.result_dataset['category'].isin(self.category_ko)]
            ko_category_dataset['category'] = ko_category_dataset['category'].map(self.category_mapping)
            filter_dataset = pd.concat([en_category_dataset, ko_category_dataset])

            top_categories = filter_dataset['category'].value_counts()
            fig_top_category_counts, ax_top_category_counts = plt.subplots(figsize=(10, 6))
            top_categories.plot(kind='bar', color='lightgreen', ax=ax_top_category_counts)
            ax_top_category_counts.set_ylabel('Number of datasets', fontsize=12)
            ax_top_category_counts.tick_params(axis='x', labelrotation=45, labelsize=8)

            st.pyplot(fig_top_category_counts)
            st.table(top_categories.reset_index().rename(columns={"index": "카테고리", "category": "데이터셋 개수"}))

            return fig_top_category_counts

# main
st.title("📈 Meta-Dataset Searching System")
st.text("")
st.text("")
st.markdown("###### Crawling Date : 2023.11.25")
st.markdown('---')
sidebar = sidebar()
dataset = sidebar.entire_dataset

# col1, col2 = st.columns(2)

# with col1:
#     st.subheader("Number of datasets per site")
#     sidebar.visualize_site_counts(dataset, sidebar.selected_sites, sidebar.title, sidebar.algorithm, sidebar.category)

# with col2:
#     st.subheader("Number of datasets by category")
#     sidebar.visualize_top_categories(dataset, sidebar.selected_sites, sidebar.title, sidebar.algorithm, sidebar.category)

st.subheader("Number of datasets per site")
site_graph = sidebar.visualize_site_counts(dataset, sidebar.selected_sites, sidebar.title, sidebar.algorithm, sidebar.category)

st.subheader("Number of datasets by category")
category_graph = sidebar.visualize_top_categories(dataset, sidebar.selected_sites, sidebar.title, sidebar.algorithm, sidebar.category)

st.markdown('---')
st.subheader('Total Datasets')
st.write(dataset.drop('_id', axis=1))
dataset = dataset.astype(str)
st.write(f"Total number of datasets: {len(dataset)}")