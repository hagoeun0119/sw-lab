import datetime
import pandas as pd
import streamlit as st
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['swlab']
collection = db['dataset']

def get_dataset():
    dataset = collection.find()
    df = pd.DataFrame(dataset)
    df = df.drop('_id', axis=1)
    df.loc[(df['site'] == "AI_hub"), 'date'] = df.loc[(df['site'] == "AI_hub"), 'updated_date'][:-2]
    df.loc[(df['site'] == "서울열린데이터광장"), 'date'] = (df.loc[(df['site'] == "서울열린데이터광장"), 'date'].str.slice(0, 10)).replace('.', '-')
    df.loc[(df['date'].isnull()), 'date'] = df.loc[(df['date'].isnull()), 'updated_date'] # date가 없는 데이터는 updated_date로 사용
    df['date'] = pd.to_datetime(df['date'],format='%Y-%m-%d', errors="coerce")
    return df

class sidebar:

    def period_search(self):
        start_date = datetime.date(2000, 1, 1)
        today = datetime.datetime.now()
        today_date = datetime.date(today.year, today.month, today.day)

        select_date = st.sidebar.date_input(
            "**📆 기간으로 데이터셋 검색**",
            (start_date, today_date),
            start_date,
            today_date,
            format="YYYY-MM-DD",
        )
        st.sidebar.text("\n")
        
        if len(select_date) == 2:
            find_sites = df_dataset[df_dataset['date'].isin(pd.date_range(str(select_date[0]), str(select_date[1])))]
            find_sites['date'] = find_sites['date'].dt.strftime('%Y-%m-%d')
            find_sites.reset_index(drop=True)
            st.dataframe(find_sites)  

    def select_site(self):
        selected_sites = st.sidebar.multiselect("**🌍 국내/국외 사이트 선택**", ["공공데이터포털", "서울열린데이터광장", "AI_hub", "Kaggle", "Data.gov"])
        st.sidebar.text("\n")
        find_sites = pd.DataFrame()
        for selected_site in selected_sites:
            data = df_dataset.query('site==@selected_site')
            find_sites = pd.concat([find_sites, data])
        if len(find_sites) != 0:
            find_sites.reset_index(drop=True)
            st.dataframe(find_sites)  

    def include_word(self):
        word = st.sidebar.multiselect("**📗 포함 단어 입력**", ["단어1", "단어2", "단어3", "단어4", "단어5"])
        st.sidebar.text("\n")

    def exclude_word(self):
        word = st.sidebar.multiselect("**📙 제외 단어 입력**", ["단어1", "단어2", "단어3", "단어4", "단어5"])

st.title("📈 데이터셋 검색")

df_dataset = get_dataset()

sidebar = sidebar()
sidebar.period_search()
sidebar.select_site()
sidebar.include_word()
sidebar.exclude_word()



