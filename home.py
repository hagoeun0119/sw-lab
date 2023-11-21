import datetime
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import streamlit as st
from matplotlib import font_manager, rc

from pymongo import MongoClient
from dateutil.relativedelta import relativedelta

st.set_page_config(layout="wide")
font_path = "C:/Windows/Fonts/NGULIM.TTF"
font = font_manager.FontProperties(fname=font_path).get_name()
rc('font', family=font)

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
                selected_dataset = selected_dataset.sort_values('view')
                self.selected_list.append('조회수순')
            if self.latest_time:
                selected_dataset = selected_dataset.sort_values('date')
                self.selected_list.append('최신순')
            if self.download:
                selected_dataset = selected_dataset.sort_values('download')
                self.selected_list.append('다운로드순')
            
            st.write(''.join(self.selected_list))
            st.write(selected_dataset)
            st.write(f"검색된 데이터셋 개수: 총 {len(selected_dataset)}개")
            
    def search_by_date(self):
        date = self.sidebar.radio(
            "**📆 기간으로 데이터셋 검색**",
            ["전체", "최근 한 달", "최근 6개월", "최근 1년"])
        self.sidebar.text("\n")
        today = datetime.datetime.now()

        if date == "전체":
            self.selected_list.append(date)
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
        self.selected_sites = selected_sites  # 클래스 변수로 선택된 사이트 저장
        
        for selected_site in selected_sites:
            select_by_site_dataset = self.entire_dataset.query('site==@selected_site')
            self.search_by_site_dataset = pd.merge(select_by_site_dataset["_id"], self.search_by_site_dataset)
            self.selected_list.append(selected_site)
            
    def search_by_title(self):
        title =self.sidebar.text_input("**📙 제목으로 검색**")
        self.sidebar.text("\n")
        self.title = title  # 클래스 변수로 선택된 사이트 저장
        
        if title:
            self.selected_list.append(title)
            self.serach_by_title_dataset = self.entire_dataset.query('title.str.contains(@title)')

    # TODO multiselect or text_input
    def search_by_algorithm(self):
        algorithm = self.sidebar.text_input("**🤖 알고리즘으로 검색**")
        self.sidebar.text("\n")
        self.algorithm = algorithm
        
        if algorithm:
            self.selected_list.append(algorithm)
            self.search_by_algorithm_dataset = self.entire_dataset.query('algorithm.str.contains(@algorithm)')

    # TODO add category
    def search_by_category(self):
        category = self.sidebar.multiselect("**📁 카테고리로 검색**", ["경제", "기타"])
        self.sidebar.text("\n")
        self.category = category  # 클래스 변수로 선택된 사이트 저장

        if category:
            self.selected_list.append(category)
            self.search_by_category_dataset = self.entire_dataset.query('category.str.contains(@category)')

    def search_by_sort(self):
        self.view = self.sidebar.checkbox("**조회순으로 검색**")
        self.latest_time = self.sidebar.checkbox("**최신순으로 검색**")
        self.download = self.sidebar.checkbox("**다운로드순으로 검색**")

    # 데이터 시각화
    def visualize_site_counts(self, dataset, selected_sites=None, title=None, algorithm=None, category=None):
        filtered_dataset = dataset.copy()

        if self.selected_sites:
            filtered_dataset = filtered_dataset[filtered_dataset['site'].isin(self.selected_sites)]
        if self.title:
            filtered_dataset = filtered_dataset[filtered_dataset['title'].str.contains(self.title)]
        if self.algorithm:
            filtered_dataset = filtered_dataset[filtered_dataset['algorithm'].str.contains(self.algorithm)]
        if self.category:
            filtered_dataset = filtered_dataset[filtered_dataset['category'].isin(self.category)]

        site_counts = filtered_dataset['site'].value_counts()
        fig_site_counts, ax_site_counts = plt.subplots(figsize=(10, 6))
        site_counts.plot(kind='bar', color='skyblue', ax=ax_site_counts)
        ax_site_counts.set_ylabel('데이터셋 개수', fontsize=12)
        ax_site_counts.tick_params(axis='x', labelrotation=45)

        st.pyplot(fig_site_counts)
        st.table(site_counts.reset_index().rename(columns={"index": "사이트", "site": "데이터셋 개수"}))

        return fig_site_counts

    def visualize_top_categories(self, dataset, selected_sites=None, title=None, algorithm=None, category=None):
        filtered_dataset = dataset[(dataset['category'] != 'NA') & (dataset['category'] != 'other')]
        
        if self.selected_sites:
            filtered_dataset = filtered_dataset[filtered_dataset['site'].isin(self.selected_sites)]
        if self.title:
            filtered_dataset = filtered_dataset[filtered_dataset['title'].str.contains(self.title)]
        if self.algorithm:
            filtered_dataset = filtered_dataset[filtered_dataset['algorithm'].str.contains(self.algorithm)]
        if self.category:
            filtered_dataset = filtered_dataset[filtered_dataset['category'].isin(self.category)]

        top_categories = filtered_dataset['category'].value_counts().head(20)

        fig_top_category_counts, ax_top_category_counts = plt.subplots(figsize=(10, 6))
        top_categories.plot(kind='bar', color='lightgreen', ax=ax_top_category_counts)
        ax_top_category_counts.set_ylabel('데이터셋 개수', fontsize=12)
        ax_top_category_counts.tick_params(axis='x', labelrotation=45, labelsize=8)

        st.pyplot(fig_top_category_counts)
        st.table(top_categories.reset_index().rename(columns={"index": "카테고리", "category": "데이터셋 개수"}))

        return fig_top_category_counts

# main
st.title("📈 메타데이터셋 검색 시스템")
st.text("")
st.text("")
st.markdown("###### 크롤링한 날짜 : 2023.10.02")
st.markdown('---')
sidebar = sidebar()
dataset = sidebar.entire_dataset

col1, col2 = st.columns(2)

with col1:
    st.subheader("사이트별 데이터셋 개수")
    sidebar.visualize_site_counts(dataset, sidebar.selected_sites, sidebar.title, sidebar.algorithm, sidebar.category)

with col2:
    st.subheader("상위 카테고리별 데이터셋 개수")
    sidebar.visualize_top_categories(dataset, sidebar.selected_sites, sidebar.title, sidebar.algorithm, sidebar.category)

st.markdown('---')
st.subheader('전체 데이터셋')
st.write(dataset.drop('_id', axis=1))
st.write(f"총 데이터셋 개수: 총 {len(dataset)}개")