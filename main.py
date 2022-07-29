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


  def expand(x, reasons):
    if x['failure_reasons']:
      for reason in reasons:
        if reason in x['failure_reasons']:
          x[reason] = 1
    else:
      x[reasons] = 0
    return x


  def process_data(self):
    self.process_reasons()
    self.data[self.reasons] = 0
    self.data.apply(eSamudaay.expand, axis = 1, args = (self.reasons))


  def get_inventory(self):
    return self.data['product_name'].value_counts()
  
  
  def get_business_names(self):
    return list(self.urldict.keys())
  
def main():
    st.title("Business name")
    # html_temp = """
    # <div style="background-color:tomato;padding:10px">
    # <h2 style="color:white;text-align:center;"> Test text</h2>
    # </div>
    # """
    # st.markdown(html_temp,unsafe_allow_html=True)
    hack = eSamudaay('output.json')
    
    business_list = hack.get_business_names()
    option = st.selectbox('Select a Business', business_list)
    hack.get_company(option)
    st.write(hack.get_inventory())
     

if __name__=='__main__':
    main()
    