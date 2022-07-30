import numpy as np
import pandas as pd
import streamlit as st 
import pandas as pd
import requests
import json
import numpy as np
from fastapi import FastAPI, Response, status
from pydantic import BaseModel
from datetime import datetime
import matplotlib.pyplot as plt
import streamlit.components.v1 as components  # Import Streamlit
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
    self.data = self.data.apply(self.expand, axis = 1)


  def get_inventory(self):
    return self.data['product_name'].value_counts().head(7)
  
  
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
    products_sum = self.data.drop(['sku_id', 'failure_reasons'], axis = 1).groupby(by = 'product_name').sum()
    product_stats = pd.DataFrame()
    for reason in self.reasons:
      product_stats['%' + reason] = products_sum[reason]/inventory * 100
    product_stats = product_stats.reset_index()
    product_stats = product_stats.rename( columns = {'index': 'product_name'})
    product_stats.fillna(0, inplace = True)
    return product_stats

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
          business_details['address'].append(data['address']['geo_addr'][key])
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
    #st.title("Business name")
    # html_temp = """
    # <div style="background-color:tomato;padding:10px">
    # <h2 style="color:white;text-align:center;"> Test text</h2>
    # </div>
    # """
    # st.markdown(html_temp,unsafe_allow_html=True)
    hack = eSamudaay('output.json')
    #components.html(""" <div class= "area" > <ul class= "circles" ><li></li><li></li><li></li><li></li><li></li><li></li><li></li><li></li><li></li><li></li></ul></div> """)
    with open('style.css') as f:
      st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    business_list = hack.get_business_names()
    option = st.selectbox('Select a Business', business_list)
    st.title(option)
    hack.get_company(option)
    fig=plt.figure(figsize=(15,8))
    st.header('All products')
    proddf = hack.product_stats()
    #proddf = proddf.set_index('sku_id')
    st.write(proddf)
    st.header('Product Search Bar')
    prodlist = list(proddf['product_name'])
    #prodname = st.text_input('Enter product', 'Product name')
    prodoption = st.selectbox('Select a Product', prodlist)
    st.write(proddf[proddf['product_name']==prodoption])
    st.header('Bar chart')
    st.bar_chart(hack.get_inventory(), 400, 500)
    st.header('Pie chart')
    pieval = hack.issues()
    
    labels = pieval.keys()
    sizes = pieval.values()
    

    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, labels=labels)
    ax1.axis('equal')  

    st.pyplot(fig1)

if __name__=='__main__':
    main()
    
    
