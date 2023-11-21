import datetime
import pandas as pd
import streamlit as st
from pymongo import MongoClient
from dateutil.relativedelta import relativedelta

client = MongoClient('mongodb://localhost:27017/')
db = client['swlab']
collection = db['dataset']

def get_dataset():
    dataset = collection.find()
    df = pd.DataFrame(dataset)
    df.loc[(df['site'] == "AI_hub"), 'date'] = df.loc[(df['site'] == "AI_hub"), 'updated_date'][:-2]
    df.loc[(df['site'] == "서울열린데이터광장"), 'date'] = (df.loc[(df['site'] == "서울열린데이터광장"), 'date'].str.slice(0, 10)).replace('.', '-')
    df.loc[(df['date'].isnull()), 'date'] = df.loc[(df['date'].isnull()), 'updated_date'] # date가 없는 데이터는 updated_date로 사용
    df['date'] = pd.to_datetime(df['date'],format='%Y-%m-%d', errors="coerce")
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

        if self.sidebar.button("버튼"):
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
                self.search_by_sort_list.append(('download', True))
                self.selected_list.append('다운로드순')
        
            if len(self.search_by_sort_list) == 1:
                selected_dataset = selected_dataset.sort_values(by=[self.search_by_sort_list[0][0]], ascending=[self.search_by_sort_list[0][1]])
            elif len(self.search_by_sort_list) == 2:
                selected_dataset = selected_dataset.sort_values(by=[self.search_by_sort_list[0][0], self.search_by_sort_list[1][0]], ascending=[self.search_by_sort_list[0][1], self.search_by_sort_list[1][1]])
            elif len(self.search_by_sort_list) == 3:
                selected_dataset = selected_dataset.sort_values(by=[self.search_by_sort_list[0][0], self.search_by_sort_list[1][0], self.search_by_sort_list[2][0]], 
                                                                ascending=[self.search_by_sort_list[0][1], self.search_by_sort_list[1][1], self.search_by_sort_list[2][1]])
            
            st.write(''.join(self.selected_list))
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
        selected_sites = self.sidebar.multiselect("**🌍 사이트 검색**", ["공공데이터포털", "서울열린데이터광장", "AI_hub", "Kaggle", "Data.gov"])
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
        category = self.sidebar.multiselect("**📁 카테고리로 검색**", ["경제", "기타"])
        self.sidebar.text("\n")

        if category:
            self.selected_list.append(category)
            self.search_by_category_dataset = self.entire_dataset.query('category.str.contains(@category)')

    def search_by_sort(self):
        self.view = self.sidebar.checkbox("**조회순으로 검색**")
        self.latest_time = self.sidebar.checkbox("**최신순으로 검색**")
        self.download = self.sidebar.checkbox("**다운로드순으로 검색**")


st.title("📈 메타데이터셋 검색 시스템")
sidebar = sidebar()


