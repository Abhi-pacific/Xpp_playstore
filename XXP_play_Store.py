import pandas as pd
import streamlit as st
import plotly.express as px

class play:
    def __init__(self,raw_data):
        self.raw_data = raw_data
        # File transformation
        data_df = pd.ExcelFile(raw_data, engine='openpyxl')
        
        # Parsing the data 
        self.data = data_df.parse('Raw')
        self.emp_data = data_df.parse('Emp List')

          # Dropping the columns if they already exists
        try:
            self.data.drop(columns=['Tagging', 'Date (Case creation time)','Date (Case Updated Time)', 'Week', 'OLMS ID', 'Unique', 'F=L'],inplace=True)
        except:
            pass

        self.manipulating_Data(self.data,self.emp_data)

    def manipulating_Data(self,data,emp_data):
        self.data = data
        self.emp_data = emp_data
        self.data['Tagging'] = self.data['Type'] + '>>' + self.data['Playstore Sub Type'] + '>>' + self.data['Playstore Sub Sub Type']
        self.data['Date (Case creation time)'] = self.data['Case creation time'].astype(str).str.split(' ').str[0].str.strip()
        self.data['Date (Case Updated Time)'] = self.data['Case updated time'].astype(str).str.split(' ').str[0].str.strip()
        self.data['DateTime'] = pd.to_datetime(self.data['Date (Case Updated Time)'])

        # creating the week column
        self.data.loc[self.data['DateTime'].dt.day <= 7, 'week'] = 'week 1'
        self.data.loc[(self.data['DateTime'].dt.day > 7) & (self.data['DateTime'].dt.day <= 14), 'week'] = 'week 2'
        self.data.loc[(self.data['DateTime'].dt.day > 14) & (self.data['DateTime'].dt.day <= 21), 'week'] = 'week 3'
        self.data.loc[self.data['DateTime'].dt.day > 21, 'week'] = 'week 4'

        # Merging Data and emp_data
        self.data = self.data.merge(self.emp_data[['OLMS ID','Name']],how='left', left_on='Case First Responded by Advisor',right_on='Name')
        self.data.drop(columns=['Name'],inplace=True)


        # Creating  the Unique column
        self.data['Unique'] = self.data['Date (Case Updated Time)'].astype(str) + self.data['OLMS ID'].astype(str)


        # creating the AD count 
        # will use this for visualization later
        self.Ad_count_ad_name = self.data.pivot_table(
        index='Case First Responded by Advisor',
        columns='Date (Case Updated Time)',
        aggfunc='size',
        fill_value=0).assign(total = lambda x: x.sum(axis=1)).sort_values(by='total',ascending=False)

        # creating the Ad_count_date_creation_time Report
        # will use this for visualization later

        # we can also use Transpose here but I choose this 😎
        self.Ad_count_date_creation_time = pd.crosstab(index=[0],columns=self.data['Date (Case creation time)']).assign(total = lambda x : x.sum(axis=1)).sort_values(by='total',ascending=False)
        self.Ad_count_date_creation_time.index = ['Count'] 


        # Creating the Top-10 Report
        # will use this for visualization later

        self.top_10_Type = self.data.pivot_table(index='Type',columns='Date (Case Updated Time)',aggfunc='size',fill_value=0).assign(Total = lambda x : x.sum(axis=1)).sort_values('Total', ascending= False).head(10)
        self.top_10_Type.columns.name = "Days"
        self.total_col = pd.DataFrame(self.top_10_Type.sum(axis=0)).T
        self.total_col.index = ['Grand_total']
        self.top_10_Type = pd.concat([self.top_10_Type,self.total_col])

        # Creating the Tagging Report 
        # will use this for visualization later
        
        self.tagging = self.data.pivot_table(index='Tagging',aggfunc='size').reset_index(name='count')
        self.tagging = self.tagging.sort_values(by='count',ascending=False).head(10)
        self.tagging = self.tagging.reset_index(drop=True)

        # creating the count_of case Report
        # will use this for visualization later

        self.count_of_case = self.data.pivot_table(columns='week',index='Case Rating',aggfunc='size').assign(total = lambda x: x.sum(axis = 1))
        self.gd_count_of_case = pd.DataFrame(self.count_of_case.sum(axis=0)).T
        self.gd_count_of_case.index=['Grand total']
        self.count_of_case = pd.concat([self.count_of_case,self.gd_count_of_case])
        self.count_of_case.reset_index(inplace=True)
        self.count_of_case.columns.name = None
        self.count_of_case = self.count_of_case.rename(columns = {'index':'Rating'})
        self._ = self.count_of_case.columns.to_list()
        self.week_list = []
        for __ in self._:
            if __ not in ['Ranking','total']:
                self.week_list.append(__)



        self.data_visualization(self.Ad_count_ad_name,self.Ad_count_date_creation_time,self.top_10_Type,self.tagging, self.count_of_case)


    def data_visualization(self,Ad_count_ad_name,Ad_count_date_creation_time,top_10_Type,tagging, count_of_case):
        self.Ad_count_ad_name = Ad_count_ad_name
        self.Ad_count_date_creation_time = Ad_count_date_creation_time
        self.top_10_Type = top_10_Type
        self.tagging = tagging
        self.count_of_case = count_of_case

        st.write(f'AD count name report')
        st.dataframe(self.Ad_count_ad_name)
        st.write(f'Ad Count Date creation time report')
        st.dataframe(self.Ad_count_date_creation_time)
        st.write(f'Top 10 type report')
        st.dataframe(self.top_10_Type)
        st.write(f'Tagging report')
        st.dataframe(self.tagging)
        st.write(f'Count of cases report')
        df_melted = self.count_of_case.melt(id_vars='Rating', value_vars=self.week_list,var_name='Week', value_name='Count')
        fig = px.bar(df_melted, x='Rating', y='Count', color='Week', barmode='group', title='Weekly and Total Counts by Rating')
        tab1, tab2 = st.tabs(["Chart", "Dataframe"])
        tab1.plotly_chart(fig, height= 250)
        tab2.dataframe(self.count_of_case, height=250, use_container_width=True)
       

        
      

        
 

col1, col2, col3 = st.columns([0.1,4,1])
with col3:
    st.image('https://www.netimpactlimited.com/wp-content/uploads/2024/04/NetImpact-Logo-Final-Web-2.png')
with col2:
    st.title('XPP Play Store 📊')
raw_data = st.file_uploader(f'Please Upload the Excel file for the Play Store data')
if raw_data is not None:
    pl = play(raw_data)
   # pl.loadData(raw_data)


