
import numpy as np
import pandas as pd
import streamlit as st
import pandas as pd
import requests
import json
import numpy as np
pip install seaborn
import seaborn as sns
from fastapi import FastAPI, Response, status
from pydantic import BaseModel
from datetime import datetime
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
from streamlit_option_menu import option_menu


class eSamudaay:

    def __init__(self, filepath):

        self.filepath = filepath
        self.urldict = None
        with open(self.filepath) as json_file:
            self.urldict = json.load(json_file)
        self.business = ''
        self.url = ''
        self.data = None
        self.reasons = []

    def get_company(self, business):
        self.business = business
        self.url = self.urldict[self.business]
        self.fetch_data()
        self.process_data()

    def fetch_data(self):

        response = requests.request("GET", self.url)
        url_return = json.loads(response.text)

        self.data = pd.DataFrame(url_return)

    def process_reasons(self):
        possible_reasons = list(self.data['failure_reasons'])

        given_reasons = []
        for reason in possible_reasons:
            if type(reason) == list:
                given_reasons.extend(reason)
            elif type(reason) == str:
                given_reasons.append(reason)

        given_reasons = set(given_reasons)

        self.reasons = list(given_reasons)

    def expand(self, x):
        if x['failure_reasons'] != None:
            for reason in self.reasons:
                if reason in x['failure_reasons']:
                    x[reason] = 1

        return x

    def process_data(self):
        self.process_reasons()
        self.data[self.reasons] = 0
        self.data = self.data.apply(self.expand, axis=1)

    def get_inventory(self):
        return self.data['product_name'].value_counts()

    def get_business_names(self):
        return list(self.urldict.keys())

    def get_product_data(self):
        attributes = ['sku_id', 'product_name', 'failure_reasons']
        product_data = self.data[attributes]
        return product_data

    def issues(self):
        return self.data[self.reasons].sum().to_dict()

    def product_stats(self):
        inventory = self.get_inventory()
        products_sum = self.data.drop(
            ['sku_id', 'failure_reasons'], axis=1).groupby(by='product_name').sum()
        product_stats = pd.DataFrame()
        for reason in self.reasons:
            product_stats['%' + reason] = products_sum[reason]/inventory * 100
        product_stats = product_stats.reset_index()
        product_stats = product_stats.rename(columns={'index': 'product_name'})
        product_stats.fillna(0, inplace = True)
        return product_stats
    def get_error_rate(self):
        total_inventory = self.get_inventory().sum()
        total_errors = self.data.drop(['sku_id', 'failure_reasons', ], axis=1).groupby(by='product_name').sum().sum(
            axis=1).sum()
        if total_inventory != 0:
            error_rate = total_errors / total_inventory
            return error_rate
        else:
            return 0

    def get_classification(self):
        error_rate = self.get_error_rate()
        if error_rate < 1:
            return 1
        elif error_rate == 1:
            return 2
        else:
            return 3



def return_business_details(business_name):
    with open('output.json') as json_file:
        urldict = json.load(json_file)
    url = urldict[business_name]
    url = url[:-7]
    response = requests.request("GET", url)
    data = json.loads(response.text)
    business_details = {}
    business_details['address'] = []
    if (data['address']):
        if 'geo_addr' in data['address']:
            if (data['address']['geo_addr']):
                for key in data['address']['geo_addr'].keys():
                    business_details['address'].append(
                        data['address']['geo_addr'][key])
            else:
                business_details['address'].append('No data available')
        else:
            business_details['address'].append('No data available')
    else:
        business_details['address'].append('No data available')

    business_details['address'] = ",".join(business_details['address'])

    business_details['avg_ratings'] = 0
    if (data['ratings_info']):
        if 'ratings_avg' in data['ratings_info']:
            business_details['avg_ratings'] = data['ratings_info']['ratings_avg']

    business_details['ratings_count'] = 0
    if (data['ratings_info']):
        if 'ratings_count' in data['ratings_info']:
            business_details['ratings_count'] = data['ratings_info']['ratings_count']

    business_details['social_links'] = data['social_links']
    return business_details


def main():
    
    hack = eSamudaay('output.json')

    

    with st.sidebar:
        st.write("Main Menu")
        st.markdown("[Select business](#name-of-program)",
                    unsafe_allow_html=True)
        st.markdown("[Search Products](#product-search-bar)",
                    unsafe_allow_html=True)
        st.markdown("[About Team](#about-the-team)", unsafe_allow_html=True)

    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

    st.header("Rakuzan Analysis")
    business_list = hack.get_business_names()
    option = st.selectbox('Select a Business', business_list,index=55)
    
    hack.get_company(option)
    fig = plt.figure(figsize=(15, 8))
    classification = hack.get_classification()
    st.subheader("Comments")
    if classification == 1:
        error_rate = hack.get_error_rate()
        st.subheader(f"Issues per product: {error_rate:.2f}\nVery few problems per product")
    elif classification == 2:
        error_rate = hack.get_error_rate()
        st.subheader(f"Issues per product: {error_rate:.2f}\nSome changes are needed. Every product has an issue.")
    else:
        error_rate = hack.get_error_rate()
        st.subheader(f"Issues per product: {error_rate:.2f}\nMajor changes need. Too many issues per product")
    st.header('All products')
    proddf = hack.product_stats()
    

    subset = [col for col in proddf.columns if col != 'product_name']
    
    st.dataframe(proddf.style.format(subset = subset, formatter = "{:.2f}"))
    
   

    st.header('Product Search Bar')
    prodlist = list(proddf['product_name'])
    
    prodoption = st.selectbox('Select a Product', prodlist)
    st.dataframe(proddf[proddf['product_name'] == prodoption].style.format(subset=subset, formatter="{:.2f}"))
    st.header("Business Analysis")
    st.header('Bar chart')
    

    fig = plt.figure(figsize=(10, 4))
    sns.barplot(hack.get_inventory().head(7).index,
                hack.get_inventory().head(7).sort_values(ascending=False).values)
    plt.xticks(rotation=15)
    plt.xlabel("Product Name")
    plt.ylabel("No. of Complaints")
    plt.title("Products with highest Complaints \n (Priority Resolution List)")
    st.pyplot(fig)

    st.header('Pie chart')
    pieval = hack.issues()

    labels = pieval.keys()
    sizes = pieval.values()

    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, labels=labels,
            autopct='%1.1f%%')
    ax1.axis('equal')
    plt.title("Failure Reason Distribution for overall business")
    st.pyplot(fig1)
    st.header("About the Team")
    data = [['Yaswanth Biruduraju', 'MIT Manipal'], ['Nishad Khade', 'MIT Manipal'], 
    ['Garvit Gopalani', 'MIT Manipal'], ['Mihir Agarwal', 'MIT Manipal'],
    ['Prakhar Tripathi', 'MIT Manipal']]
  
    teamdetailsdf = pd.DataFrame(data, columns=['Name', 'Institute'])
    
    st.write(teamdetailsdf)

if __name__ == '__main__':
    main()
