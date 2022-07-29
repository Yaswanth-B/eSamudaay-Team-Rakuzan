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
  
def main():
    #st.title("Business name")
    # html_temp = """
    # <div style="background-color:tomato;padding:10px">
    # <h2 style="color:white;text-align:center;"> Test text</h2>
    # </div>
    # """
    # st.markdown(html_temp,unsafe_allow_html=True)
    hack = eSamudaay('output.json')
    
    business_list = hack.get_business_names()
    option = st.selectbox('Select a Business', business_list)
    st.title(option)
    hack.get_company(option)
    fig=plt.figure(figsize=(15,8))
    st.header('All products')
    proddf = hack.get_product_data()
    proddf = proddf.set_index('sku_id')
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
    
    
