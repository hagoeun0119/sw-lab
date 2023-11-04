import datetime
import streamlit as st

class sidebar:

    def period_search(self):
        start_date = datetime.date(2000, 1, 1)
        today = datetime.datetime.now()
        today_date = datetime.date(today.year, today.month, today.day)

        st.sidebar.date_input(
            "**📆 기간으로 데이터셋 검색**",
            (start_date, today_date),
            start_date,
            today_date,
            format="YYYY.MM.DD",
        )
        st.sidebar.text("\n")

    def select_site(self):
        site = st.sidebar.multiselect("**🌍 국내/국외 사이트 선택**", ["공공데이터포털", "서울열린데이터광장", "AI Hub", "Kaggle", "Data.gov"])
        st.sidebar.text("\n")

    def include_word(self):
        word = st.sidebar.multiselect("**📗 포함 단어 입력**", ["단어1", "단어2", "단어3", "단어4", "단어5"])
        st.sidebar.text("\n")

    def exclude_word(self):
        word = st.sidebar.multiselect("**📙 제외 단어 입력**", ["단어1", "단어2", "단어3", "단어4", "단어5"])

st.title("📈 데이터셋 검색")

sidebar = sidebar()
sidebar.period_search()
sidebar.select_site()
sidebar.include_word()
sidebar.exclude_word()



