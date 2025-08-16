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
        self.container_1 = st.container()
        self.container_2 = st.container()
        self.container_3 = st.container()
        self.container_4 = st.container()

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
        self.unique_Case_First_Responded_by_Advisor = self.data['Case First Responded by Advisor'].dropna().unique()
        

        # Let user select names to filter
        with self.container_1:
            self.selected_names = st.multiselect("Select advisor name: ", options=self.unique_Case_First_Responded_by_Advisor, default=self.unique_Case_First_Responded_by_Advisor)



        # Filter based on selected names
        self.filtered_data = self.data[self.data['Case First Responded by Advisor'].isin(self.selected_names)]
        self.Ad_count_ad_name = self.filtered_data.pivot_table(
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
        self.week_unique = self.data['week'].dropna().unique()


        # User select the filter on week
        with self.container_2:
            self.selected_week_A = st.multiselect('Select the week number for Top-10 Report :',options=self.week_unique,default=self.week_unique)


        self.custom_week_data = self.data[self.data['week'].isin(self.selected_week_A)]
        self.top_10_Type = self.custom_week_data.pivot_table(index='Type',columns='Date (Case Updated Time)',aggfunc='size',fill_value=0).assign(Total = lambda x : x.sum(axis=1)).sort_values('Total', ascending= False).head(10)
        self.top_10_Type.columns.name = "Days"
        self.total_col = pd.DataFrame(self.top_10_Type.sum(axis=0)).T
        self.total_col.index = ['Grand_total']
        self.top_10_Type = pd.concat([self.top_10_Type,self.total_col])

        # Sub Type top 10

        with self.container_3:
            self.selected_week_B = st.multiselect('Select the week number for Sub type Top-10 Report :',options=self.week_unique,default=self.week_unique)
        self.custom_week_data_sub = self.data[self.data['week'].isin(self.selected_week_B)]
        self.sub_top_10_Type = self.custom_week_data_sub.pivot_table(index='Playstore Sub Type',columns='Date (Case Updated Time)',aggfunc='size',fill_value=0).assign(Total = lambda x : x.sum(axis=1)).sort_values('Total', ascending= False).head(10)
        self.sub_top_10_Type.columns.name = "Days"
        self.sub_total_col = pd.DataFrame(self.sub_top_10_Type.sum(axis=0)).T
        self.sub_total_col.index = ['Grand_total']
        self.sub_top_10_Type = pd.concat([self.sub_top_10_Type,self.sub_total_col])

         # Sub-sub Type top 10
        with self.container_4:
             self.selected_week_C = st.multiselect('Select the week number for Sub-Sub type Top-10 Report :',options=self.week_unique,default=self.week_unique)
        self.custom_week_data_sub_sub = self.data[self.data['week'].isin(self.selected_week_C)]
        self.sub_sub_top_10_Type = self.custom_week_data_sub_sub.pivot_table(index='Playstore Sub Sub Type',columns='Date (Case Updated Time)',aggfunc='size',fill_value=0).assign(Total = lambda x : x.sum(axis=1)).sort_values('Total', ascending= False).head(10)
        self.sub_sub_top_10_Type.columns.name = "Days"
        self.sub_sub_total_col = pd.DataFrame(self.sub_sub_top_10_Type.sum(axis=0)).T
        self.sub_sub_total_col.index = ['Grand_total']
        self.sub_sub_top_10_Type = pd.concat([self.sub_sub_top_10_Type,self.sub_sub_total_col])

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
        for i in self._:
            if i not in ['Ranking','total']:
                self.week_list.append(str(i))



        self.data_visualization(self.Ad_count_ad_name,self.Ad_count_date_creation_time,self.top_10_Type,self.sub_top_10_Type,self.sub_sub_top_10_Type,self.tagging, self.count_of_case)


    def data_visualization(self,Ad_count_ad_name,Ad_count_date_creation_time,top_10_Type,sub_top_10_Type,sub_sub_top_10_Type,tagging, count_of_case):
        self.Ad_count_ad_name = Ad_count_ad_name
        self.Ad_count_date_creation_time = Ad_count_date_creation_time
        self.top_10_Type = top_10_Type
        self.sub_sub_total_col = sub_top_10_Type
        self.sub_sub_top_10_Type = sub_sub_top_10_Type
        self.tagging = tagging
        self.count_of_case = count_of_case

        with self.container_1:
            st.write(f'AD count name report')
            st.dataframe(self.Ad_count_ad_name)
            st.write(f'Ad Count Date creation time report')
            st.dataframe(self.Ad_count_date_creation_time)
        with self.container_2:
            st.write(f'Top 10 type report')
            st.dataframe(self.top_10_Type)
        with self.container_3:
            st.write(f' Sub Top 10 type report')
            st.dataframe(self.sub_top_10_Type)
        with self.container_4:
            st.write(f'Sub Sub Top 10 type report')
            st.dataframe(self.sub_sub_top_10_Type)
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


