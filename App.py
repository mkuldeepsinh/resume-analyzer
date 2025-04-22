

import nltk
nltk.download('stopwords')
###### Packages Used ######
import streamlit as st # core package used in this project
import pandas as pd
import base64, random
import time, datetime
import os
import socket
import platform
import geocoder
import secrets
import io, random
import plotly.express as px # to create visualisations at the admin session
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
# libraries used to parse the pdf files
from custom_resume_parser import CustomResumeParser
from pdfminer.layout import LAParams, LTTextBox
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter
from streamlit_tags import st_tags
from PIL import Image
# pre stored data for prediction purposes
from Courses import ds_course, web_course, android_course, ios_course, uiux_course, resume_videos, interview_videos

# MongoDB Connection Setup
from pymongo import MongoClient
from geopy.exc import GeocoderUnavailable


# Replace with your MongoDB connection string
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client['CV']  # Database name

###### Preprocessing functions ######

# Generates a link allowing the data in a given panda dataframe to be downloaded in csv format 
def get_csv_download_link(df, filename, text):
    csv = df.to_csv(index=False)
    ## bytes conversions
    b64 = base64.b64encode(csv.encode()).decode()      
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href

# Reads Pdf file and check_extractable
def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()

    ## close open handles
    converter.close()
    fake_file_handle.close()
    return text

# show uploaded file path to view pdf_display
def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# course recommendations which has data already loaded from Courses.py
def course_recommender(course_list):
    st.subheader("**Courses & Certificates Recommendations 👨‍🎓**")
    c = 0
    rec_course = []
    ## slider to choose from range 1-10
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 5)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course

###### Database Functions ######

# inserting miscellaneous data, fetched results, prediction and recommendation into user_data collection
def insert_data(sec_token, ip_add, host_name, dev_user, os_name_ver, latlong, city, state, country,
                act_name, act_mail, act_mob, name, email, res_score, timestamp, no_of_pages,
                reco_field, cand_level, skills, recommended_skills, courses, pdf_name):
    collection = db.user_data
    document = {
        "sec_token": sec_token,
        "ip_add": ip_add,
        "host_name": host_name,
        "dev_user": dev_user,
        "os_name_ver": os_name_ver,
        "latlong": latlong,
        "city": city,
        "state": state,
        "country": country,
        "act_name": act_name,
        "act_mail": act_mail,
        "act_mob": act_mob,
        "name": name,
        "email": email,
        "resume_score": res_score,
        "timestamp": timestamp,
        "no_of_pages": no_of_pages,
        "reco_field": reco_field,
        "cand_level": cand_level,
        "skills": skills,
        "recommended_skills": recommended_skills,
        "courses": courses,
        "pdf_name": pdf_name
    }
    collection.insert_one(document)

def insertf_data(feed_name, feed_email, feed_score, comments, Timestamp):
    collection = db.user_feedback
    document = {
        "feed_name": feed_name,
        "feed_email": feed_email,
        "feed_score": feed_score,
        "comments": comments,
        "Timestamp": Timestamp
    }
    collection.insert_one(document)

###### Setting Page Configuration (favicon, Logo, Title) ######

st.set_page_config(
   page_title="AI Resume Analyzer",
   page_icon='./Logo/recommend.png',
)

###### Main function run() ######

def run():
    
    # (Logo, Heading, Sidebar etc)
    img = Image.open('./Logo/RESUM.png')
    st.image(img)
    st.sidebar.markdown("# Choose Something...")
    activities = ["User", "Feedback", "About", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    link = '<b>Built with 🤍 by <a href="" style="text-decoration: none; color: #021659;">Kuldeep Vansh Harsh</a></b>' 
    st.sidebar.markdown(link, unsafe_allow_html=True)
    # st.sidebar.markdown('''
    #     <!-- site visitors -->

    #     <div id="sfct2xghr8ak6lfqt3kgru233378jya38dy" hidden></div>

    #     <noscript>
    #         <a href="https://www.freecounterstat.com" title="hit counter">
    #             <img src="https://counter9.stat.ovh/private/freecounterstat.php?c=t2xghr8ak6lfqt3kgru233378jya38dy" border="0" title="hit counter" alt="hit counter"> -->
    #         </a>
    #     </noscript>
    
    #     <p>Visitors <img src="https://counter9.stat.ovh/private/freecounterstat.php?c=t2xghr8ak6lfqt3kgru233378jya38dy" title="Free Counter" Alt="web counter" width="60px"  border="0" /></p>
    
    # ''', unsafe_allow_html=True)

    ###### CODE FOR CLIENT SIDE (USER) ######

    if choice == 'User':
        
        # Collecting Miscellaneous Information
        act_name = st.text_input('Name*')
        act_mail = st.text_input('Mail*')
        act_mob  = st.text_input('Mobile Number*')
        sec_token = secrets.token_urlsafe(12)
        host_name = socket.gethostname()
        ip_add = socket.gethostbyname(host_name)
        dev_user = os.getlogin()
        os_name_ver = platform.system() + " " + platform.release()
        g = geocoder.ip('me')
        latlong = g.latlng
        geolocator = Nominatim(user_agent="http")
        try:
            location = geolocator.reverse(latlong, language='en', timeout=10)
        except GeocoderUnavailable:
            location = "Unavailable"
        address = location.raw['address']
        cityy = address.get('city', '')
        statee = address.get('state', '')
        countryy = address.get('country', '')  
        city = cityy
        state = statee
        country = countryy

        # Upload Resume
        st.markdown('''<h5 style='text-align: left; color: #021659;'> Upload Your Resume, And Get Smart Recommendations</h5>''',unsafe_allow_html=True)
        
        ## file upload in pdf format
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            with st.spinner('Hang On While We Cook Magic For You...'):
                time.sleep(4)
        
            ### saving the uploaded resume to folder
            save_image_path = './Uploaded_Resumes/'+pdf_file.name
            pdf_name = pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)

            ### parsing and extracting whole resume 
            resume_data = CustomResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                
                ## Get the whole resume data into resume_text
                resume_text = pdf_reader(save_image_path)

                ## Showing Analyzed data from (resume_data)
                st.header("**Resume Analysis 🤘**")
                st.success("Hello "+ resume_data['name'])
                st.subheader("**Your Basic info 👀**")
                try:
                    st.text('Name: '+resume_data['name'])
                    st.text('Email: ' + resume_data['email'])
                    st.text('Contact: ' + resume_data['mobile_number'])
                    st.text('Degree: '+str(resume_data['degree']))                    
                    st.text('Resume pages: '+str(resume_data['no_of_pages']))

                except:
                    pass
                ## Predicting Candidate Experience Level 

                ### Trying with different possibilities
                cand_level = ''
                if resume_data['no_of_pages'] < 1:                
                    cand_level = "NA"
                    st.markdown( '''<h4 style='text-align: left; color: #d73b5c;'>You are at Fresher level!</h4>''',unsafe_allow_html=True)
                
                #### if internship then intermediate level
                elif 'INTERNSHIP' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',unsafe_allow_html=True)
                elif 'INTERNSHIPS' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',unsafe_allow_html=True)
                elif 'Internship' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',unsafe_allow_html=True)
                elif 'Internships' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',unsafe_allow_html=True)
                
                #### if Work Experience/Experience then Experience level
                elif 'EXPERIENCE' in resume_text:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',unsafe_allow_html=True)
                elif 'WORK EXPERIENCE' in resume_text:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',unsafe_allow_html=True)
                elif 'Experience' in resume_text:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',unsafe_allow_html=True)
                elif 'Work Experience' in resume_text:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',unsafe_allow_html=True)
                else:
                    cand_level = "Fresher"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at Fresher level!!''',unsafe_allow_html=True)

                ## Skills Analyzing and Recommendation
                st.subheader("**Skills Recommendation 💡**")
                
                ### Current Analyzed Skills
                keywords = st_tags(label='### Your Current Skills',
                text='See our skills recommendation below',value=resume_data['skills'],key = '1  ')

                ### Keywords for Recommendations
                ds_keyword = ['tensorflow','keras','pytorch','machine learning','deep Learning','flask','streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress','javascript', 'angular js', 'C#', 'Asp.net', 'flask']
                android_keyword = ['android','android development','flutter','kotlin','xml','kivy']
                ios_keyword = ['ios','ios development','swift','cocoa','cocoa touch','xcode']
                uiux_keyword = ['ux','adobe xd','figma','zeplin','balsamiq','ui','prototyping','wireframes','storyframes','adobe photoshop','photoshop','editing','adobe illustrator','illustrator','adobe after effects','after effects','adobe premier pro','premier pro','adobe indesign','indesign','wireframe','solid','grasp','user research','user experience']
                n_any = ['english','communication','writing', 'microsoft office', 'leadership','customer management', 'social media']
                ### Skill Recommendations Starts                
                recommended_skills = []
                reco_field = ''
                rec_course = ''

                ### condition starts to check skills from keywords and predict field
                for i in resume_data['skills']:
                
                    #### Data science recommendation
                    if i.lower() in ds_keyword:
                        print(i.lower())
                        reco_field = 'Data Science'
                        st.success("** Our analysis says you are looking for Data Science Jobs.**")
                        recommended_skills = ['Data Visualization','Predictive Analysis','Statistical Modeling','Data Mining','Clustering & Classification','Data Analytics','Quantitative Analysis','Web Scraping','ML Algorithms','Keras','Pytorch','Probability','Scikit-learn','Tensorflow',"Flask",'Streamlit']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '2')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(ds_course)
                        break

                    #### Web development recommendation
                    elif i.lower() in web_keyword:
                        print(i.lower())
                        reco_field = 'Web Development'
                        st.success("** Our analysis says you are looking for Web Development Jobs **")
                        recommended_skills = ['React','Django','Node JS','React JS','php','laravel','Magento','wordpress','Javascript','Angular JS','c#','Flask','SDK']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '3')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(web_course)
                        break

                    #### Android App Development
                    elif i.lower() in android_keyword:
                        print(i.lower())
                        reco_field = 'Android Development'
                        st.success("** Our analysis says you are looking for Android App Development Jobs **")
                        recommended_skills = ['Android','Android development','Flutter','Kotlin','XML','Java','Kivy','GIT','SDK','SQLite']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '4')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(android_course)
                        break

                    #### IOS App Development
                    elif i.lower() in ios_keyword:
                        print(i.lower())
                        reco_field = 'IOS Development'
                        st.success("** Our analysis says you are looking for IOS App Development Jobs **")
                        recommended_skills = ['IOS','IOS Development','Swift','Cocoa','Cocoa Touch','Xcode','Objective-C','SQLite','Plist','StoreKit',"UI-Kit",'AV Foundation','Auto-Layout']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '5')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(ios_course)
                        break

                    #### Ui-UX Recommendation
                    elif i.lower() in uiux_keyword:
                        print(i.lower())
                        reco_field = 'UI-UX Development'
                        st.success("** Our analysis says you are looking for UI-UX Development Jobs **")
                        recommended_skills = ['UI','User Experience','Adobe XD','Figma','Zeplin','Balsamiq','Prototyping','Wireframes','Storyframes','Adobe Photoshop','Editing','Illustrator','After Effects','Premier Pro','Indesign','Wireframe','Solid','Grasp','User Research']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '6')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(uiux_course)
                        break

                    #### For Not Any Recommendations
                    elif i.lower() in n_any:
                        print(i.lower())
                        reco_field = 'NA'
                        st.warning("** Currently our tool only predicts and recommends for Data Science, Web, Android, IOS and UI/UX Development**")
                        recommended_skills = ['No Recommendations']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Currently No Recommendations',value=recommended_skills,key = '6')
                        st.markdown('''<h5 style='text-align: left; color: #092851;'>Maybe Available in Future Updates</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = "Sorry! Not Available for this Field"
                        break

                ## Resume Scorer & Resume Writing Tips
                st.subheader("**Resume Tips & Ideas 🥂**")
                resume_score = 0
                
                ### Predicting Whether these key points are added to the resume
                if 'Objective' or 'Summary' in resume_text:
                    resume_score = resume_score+6
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective/Summary</h4>''',unsafe_allow_html=True)                
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add your career objective, it will give your career intension to the Recruiters.</h4>''',unsafe_allow_html=True)

                if 'Education' or 'School' or 'College'  in resume_text:
                    resume_score = resume_score + 12
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Education Details</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Education. It will give Your Qualification level to the recruiter</h4>''',unsafe_allow_html=True)

                if 'EXPERIENCE' in resume_text:
                    resume_score = resume_score + 16
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Experience</h4>''',unsafe_allow_html=True)
                elif 'Experience' in resume_text:
                    resume_score = resume_score + 16
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Experience</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Experience. It will help you to stand out from crowd</h4>''',unsafe_allow_html=True)

                if 'INTERNSHIPS'  in resume_text:
                    resume_score = resume_score + 6
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>''',unsafe_allow_html=True)
                elif 'INTERNSHIP'  in resume_text:
                    resume_score = resume_score + 6
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>''',unsafe_allow_html=True)
                elif 'Internships'  in resume_text:
                    resume_score = resume_score + 6
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>''',unsafe_allow_html=True)
                elif 'Internship'  in resume_text:
                    resume_score = resume_score + 6
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Internships. It will help you to stand out from crowd</h4>''',unsafe_allow_html=True)

                if 'SKILLS'  in resume_text:
                    resume_score = resume_score + 7
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>''',unsafe_allow_html=True)
                elif 'SKILL'  in resume_text:
                    resume_score = resume_score + 7
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>''',unsafe_allow_html=True)
                elif 'Skills'  in resume_text:
                    resume_score = resume_score + 7
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>''',unsafe_allow_html=True)
                elif 'Skill'  in resume_text:
                    resume_score = resume_score + 7
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Skills. It will help you a lot</h4>''',unsafe_allow_html=True)

                if 'HOBBIES' in resume_text:
                    resume_score = resume_score + 4
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies</h4>''',unsafe_allow_html=True)
                elif 'Hobbies' in resume_text:
                    resume_score = resume_score + 4
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Hobbies. It will show your personality to the Recruiters and give the assurance that you are fit for this role or not.</h4>''',unsafe_allow_html=True)

                if 'INTERESTS'in resume_text:
                    resume_score = resume_score + 5
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Interest</h4>''',unsafe_allow_html=True)
                elif 'Interests'in resume_text:
                    resume_score = resume_score + 5
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Interest</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Interest. It will show your interest other that job.</h4>''',unsafe_allow_html=True)

                if 'ACHIEVEMENTS' in resume_text:
                    resume_score = resume_score + 13
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements </h4>''',unsafe_allow_html=True)
                elif 'Achievements' in resume_text:
                    resume_score = resume_score + 13
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements </h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Achievements. It will show that you are capable for the required position.</h4>''',unsafe_allow_html=True)

                if 'CERTIFICATIONS' in resume_text:
                    resume_score = resume_score + 12
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Certifications </h4>''',unsafe_allow_html=True)
                elif 'Certifications' in resume_text:
                    resume_score = resume_score + 12
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Certifications </h4>''',unsafe_allow_html=True)
                elif 'Certification' in resume_text:
                    resume_score = resume_score + 12
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Certifications </h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Certifications. It will show that you have done some specialization for the required position.</h4>''',unsafe_allow_html=True)

                if 'PROJECTS' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>''',unsafe_allow_html=True)
                elif 'PROJECT' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>''',unsafe_allow_html=True)
                elif 'Projects' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>''',unsafe_allow_html=True)
                elif 'Project' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #000000;'>[-] Please add Projects. It will show that you have done work related the required position or not.</h4>''',unsafe_allow_html=True)

                st.subheader("**Resume Score 📝**")
                st.markdown(
                    """
                    <style>
                        .container {
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            justify-content: center;
                            text-align: center;
                            padding: 20px;
                        }
                        .circular-progress {
                            position: relative;
                            height: 150px;
                            width: 150px;
                            border-radius: 50%;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            margin-bottom: 15px;
                        }
                        .score-text {
                            font-size: 32px;
                            font-weight: bold;
                        }
                    </style>
                    """,
                    unsafe_allow_html=True
                )
                
                # Creating a progress bar for resume score
                st.markdown(f"""
                <div class="container">
                    <div class="circular-progress" style="background: conic-gradient(#1ed760 {round(resume_score)}%, #e0e0e0 0%);">
                        <div class="score-text">{round(resume_score)}%</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Category-based score interpretation
                if resume_score <= 20:
                    st.markdown('''<h4 style='text-align: center; color: #ff0000;'>Your resume needs significant improvement!</h4>''', unsafe_allow_html=True)
                elif 20 < resume_score <= 40:
                    st.markdown('''<h4 style='text-align: center; color: #ff4500;'>Your resume needs some improvements!</h4>''', unsafe_allow_html=True)
                elif 40 < resume_score <= 60:
                    st.markdown('''<h4 style='text-align: center; color: #ffbf00;'>Your resume is average, keep improving!</h4>''', unsafe_allow_html=True)
                elif 60 < resume_score <= 80:
                    st.markdown('''<h4 style='text-align: center; color: #4caf50;'>Your resume is good, few improvements needed!</h4>''', unsafe_allow_html=True)
                else:
                    st.markdown('''<h4 style='text-align: center; color: #1ed760;'>Your resume is excellent, you're ready to apply!</h4>''', unsafe_allow_html=True)
                
                # Resume writing video recommendation
                st.header("**Resume Tips Videos 📺**")
                resume_vid = random.choice(resume_videos)
                st.video(resume_vid)
                
                # Interview Preparation Video
                st.header("**Interview Preparation Tips 👨‍💼**")
                interview_vid = random.choice(interview_videos)
                st.video(interview_vid)
                
                # Save the data to database
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
                name = resume_data['name']
                email = resume_data['email']
                no_of_pages = resume_data['no_of_pages']
                mobile_number = resume_data['mobile_number']
                skills = resume_data['skills']
                
                if resume_score != 0:
                    if all([act_name, act_mail, act_mob]):
                        # Insert data into the database
                        insert_data(
                            sec_token=sec_token,
                            ip_add=ip_add,
                            host_name=host_name,
                            dev_user=dev_user,
                            os_name_ver=os_name_ver,
                            latlong=latlong,
                            city=city,
                            state=state,
                            country=country,
                            act_name=act_name,
                            act_mail=act_mail,
                            act_mob=act_mob,
                            name=name,
                            email=email,
                            res_score=resume_score,
                            timestamp=timestamp,
                            no_of_pages=no_of_pages,
                            reco_field=reco_field,
                            cand_level=cand_level,
                            skills=skills,
                            recommended_skills=recommended_skills,
                            courses=rec_course,
                            pdf_name=pdf_name
                        )
                        st.success('Your Resume Analysis is complete!')
                        st.balloons()
                    else:
                        st.error('Please fill all the details (Name, Email, Mobile number) to complete the analysis.')
            else:
                st.error('Something went wrong with the resume parsing. Please check your resume format and try again.')
        
        else:
            st.info('Please upload your resume to start the analysis.')

    ###### CODE FOR THE FEEDBACK SECTION ######
    elif choice == 'Feedback':
        st.header("Feedback")
        st.markdown("<h5>We value your feedback! Please let us know your experience with our Resume Analyzer.</h5>", unsafe_allow_html=True)
        
        feed_name = st.text_input('Name')
        feed_email = st.text_input('Email')
        feed_score = st.slider('Rate your experience', 1, 5, 3)
        comments = st.text_area('Comments and Suggestions')
        
        if st.button('Submit Feedback'):
            if feed_name and feed_email and comments:
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
                insertf_data(feed_name, feed_email, feed_score, comments, timestamp)
                st.success('Thank you for your feedback!')
                st.balloons()
            else:
                st.warning('Please fill all the fields before submitting your feedback.')

    ###### CODE FOR THE ABOUT SECTION ######
    elif choice == 'About':
        st.header("About")
        st.markdown("""
        ## AI Resume Analyzer
        
        This application helps you improve your resume by analyzing it and providing personalized recommendations based on industry standards.
        
        ### Features:
        - **Resume Analysis**: Upload your resume and get a detailed breakdown of its strengths and weaknesses.
        - **Skills Recommendations**: Get personalized skill recommendations based on your desired job field.
        - **Course Recommendations**: Discover courses that can help you enhance your skills.
        - **Resume Score**: Receive a score out of 100 for your resume based on key components.
        - **Improvement Tips**: Access helpful videos and resources to improve your resume and prepare for interviews.
        
        ### Technologies Used:
        - **Python**: Core programming language
        - **Streamlit**: Web framework for the application
        - **MongoDB**: Database for storing user data
        - **PyResParser**: Library for parsing resume data
        - **NLTK**: For natural language processing
        
        ### Created by:
        Kuldeep Vansh Harsh
        
        """)
        
        st.markdown("<p style='text-align: center;'><b>Thank you for using AI Resume Analyzer!</b></p>", unsafe_allow_html=True)

    ###### CODE FOR THE ADMIN SECTION ######
    elif choice == 'Admin':
        st.header("Admin Panel")
        admin_username = st.text_input("Username")
        admin_password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if admin_username == "admin" and admin_password == "admin123":  # Replace with secure authentication
                st.success("Welcome Admin!")
                
                # Admin analytics section
                st.header("Analytics Dashboard")
                
                # Pull data from MongoDB for analytics
                user_data_collection = db.user_data
                feedback_collection = db.user_feedback
                
                # Display basic statistics
                total_users = user_data_collection.count_documents({})
                total_feedback = feedback_collection.count_documents({})
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Resumes Analyzed", total_users)
                with col2:
                    st.metric("Total Feedback Received", total_feedback)
                
                # Display resume field distribution
                st.subheader("Resume Field Distribution")
                field_data = list(user_data_collection.aggregate([
                    {"$group": {"_id": "$reco_field", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]))
                
                field_names = [field["_id"] for field in field_data if field["_id"] != "NA" and field["_id"] != ""]
                field_counts = [field["count"] for field in field_data if field["_id"] != "NA" and field["_id"] != ""]
                
                if field_names and field_counts:
                    fig = px.pie(values=field_counts, names=field_names, title="Field Distribution")
                    st.plotly_chart(fig)
                else:
                    st.info("Not enough data for field distribution chart")
                
                # Display experience level distribution
                st.subheader("Experience Level Distribution")
                level_data = list(user_data_collection.aggregate([
                    {"$group": {"_id": "$cand_level", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]))
                
                level_names = [level["_id"] for level in level_data if level["_id"] != ""]
                level_counts = [level["count"] for level in level_data if level["_id"] != ""]
                
                if level_names and level_counts:
                    fig = px.bar(x=level_names, y=level_counts, title="Experience Level Distribution")
                    fig.update_layout(xaxis_title="Experience Level", yaxis_title="Count")
                    st.plotly_chart(fig)
                else:
                    st.info("Not enough data for experience level chart")
                
                # Display average resume score
                if total_users > 0:
                    avg_score = user_data_collection.aggregate([
                        {"$group": {"_id": None, "avg_score": {"$avg": "$resume_score"}}}
                    ])
                    avg_score_list = list(avg_score)
                    avg_score_value = avg_score_list[0]["avg_score"] if avg_score_list else 0

                    
                    st.subheader("Average Resume Score")
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=avg_score_value,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Average Score"},
                        gauge={'axis': {'range': [0, 100]},
                              'bar': {'color': "#1ed760"},
                              'steps': [
                                  {'range': [0, 20], 'color': "#ff0000"},
                                  {'range': [20, 40], 'color': "#ff4500"},
                                  {'range': [40, 60], 'color': "#ffbf00"},
                                  {'range': [60, 80], 'color': "#4caf50"},
                                  {'range': [80, 100], 'color': "#1ed760"}
                              ]}
                    ))
                    st.plotly_chart(fig)
                
                # Recent user data
                st.subheader("Recent Resume Submissions")
                recent_data = list(user_data_collection.find().sort("timestamp", -1).limit(10))
                
                if recent_data:
                    recent_df = pd.DataFrame([
                        {
                            "Name": data.get("name", "N/A"),
                            "Email": data.get("email", "N/A"),
                            "Field": data.get("reco_field", "N/A"),
                            "Experience": data.get("cand_level", "N/A"),
                            "Score": data.get("resume_score", 0),
                            "Timestamp": data.get("timestamp", "N/A")
                        }
                        for data in recent_data
                    ])
                    st.dataframe(recent_df)
                    
                    # Export option
                    all_data = list(user_data_collection.find())
                    if all_data:
                        all_df = pd.DataFrame([
                            {
                                "Name": data.get("name", "N/A"),
                                "Email": data.get("email", "N/A"),
                                "Field": data.get("reco_field", "N/A"),
                                "Experience": data.get("cand_level", "N/A"),
                                "Score": data.get("resume_score", 0),
                                "Timestamp": data.get("timestamp", "N/A")
                            }
                            for data in all_data
                        ])
                        
                        st.markdown(get_csv_download_link(all_df, "resume_data.csv", "Download Complete Data"), unsafe_allow_html=True)
                else:
                    st.info("No resume submissions yet")
                
                # Feedback data
                st.subheader("Recent Feedback")
                recent_feedback = list(feedback_collection.find().sort("Timestamp", -1).limit(10))
                
                if recent_feedback:
                    feedback_df = pd.DataFrame([
                        {
                            "Name": data.get("feed_name", "N/A"),
                            "Email": data.get("feed_email", "N/A"),
                            "Rating": data.get("feed_score", 0),
                            "Comments": data.get("comments", "N/A"),
                            "Timestamp": data.get("Timestamp", "N/A")
                        }
                        for data in recent_feedback
                    ])
                    st.dataframe(feedback_df)
                    
                    # Feedback rating distribution
                    st.subheader("Feedback Rating Distribution")
                    rating_data = list(feedback_collection.aggregate([
                        {"$group": {"_id": "$feed_score", "count": {"$sum": 1}}},
                        {"$sort": {"_id": 1}}
                    ]))
                    
                    ratings = [rating["_id"] for rating in rating_data]
                    rating_counts = [rating["count"] for rating in rating_data]
                    
                    if ratings and rating_counts:
                        fig = px.bar(x=ratings, y=rating_counts, title="Feedback Rating Distribution")
                        fig.update_layout(xaxis_title="Rating", yaxis_title="Count")
                        st.plotly_chart(fig)
                    
                    # Export feedback
                    all_feedback = list(feedback_collection.find())
                    if all_feedback:
                        all_feedback_df = pd.DataFrame([
                            {
                                "Name": data.get("feed_name", "N/A"),
                                "Email": data.get("feed_email", "N/A"),
                                "Rating": data.get("feed_score", 0),
                                "Comments": data.get("comments", "N/A"),
                                "Timestamp": data.get("Timestamp", "N/A")
                            }
                            for data in all_feedback
                        ])
                        
                        st.markdown(get_csv_download_link(all_feedback_df, "feedback_data.csv", "Download Feedback Data"), unsafe_allow_html=True)
                else:
                    st.info("No feedback submissions yet")
            else:
                st.error("Invalid username or password")

# Run the application
if __name__ == "__main__":
    run()