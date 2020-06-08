from flask import Flask, render_template, request
from bs4 import BeautifulSoup as bs
from flask_cors import CORS, cross_origin
import requests 
import pymongo 
import pandas as pd 
import numpy as np

app = Flask(__name__)
# Global path varibles

# Global Varibles 
base_url = "https://flipkart.com"
dbConn = pymongo.MongoClient("mongodb+srv://mongodbuser:mongodbpassword@cluster0-lsptd.mongodb.net/test?retryWrites=true&w=majority")
db_name = "flipkart"
db = dbConn[db_name]

dic = {
     "title" : [],
     "review" : [],
     "user_name" : []
} 

def extract_reviews(reviews_link, page_length, search_string) :
    """ Extract the ten pages reviews of each products """

    if( page_length == 0 ):
        return dic

    # connections to collection
    search_string_col_name = db[search_string]
    
    u_client = requests.get(reviews_link)
    soup = bs(u_client.content, "html.parser")
    
    # First page reviews links
    mydivs = soup.findAll("div", {"class": "_1gY8H-"})

    for one_box in mydivs :
        """ store the infomation 
            in dictionary
        """
        title = one_box.div.p.get_text()
        dic['title'].append(title)
        review = one_box.find(class_ = "").get_text()
        dic['review'].append(review)
        user_name = one_box.find(class_ = "_3sxSiS").get_text()
        dic['user_name'].append(user_name)
        
        # creating Document
        document = {"title" : title, "review" : review, "user_name" : user_name}
        search_string_col_name.insert_one(document)
        
    next_review_link = ""    
    # where next and page button is present
    list_length = len(soup.find_all("a", {"class" : "_3fVaIS"}))
    
    if(list_length == 1) :
        route_url = soup.find_all("a", {"class" : "_3fVaIS"})[0]['href']
        # print(route_url)
        # print(type(route_url))
        # route_url = soup.find_all("a", {"class" : "_3fVaIS"})['href']
        next_review_link = base_url + route_url
        print(next_review_link)    
    elif(list_length == 2):
        route_url = soup.find_all("a", {"class" : "_3fVaIS"})[1]['href']
        next_review_link = base_url + route_url
        print(next_review_link)
        
    return extract_reviews(next_review_link, page_length-1, search_string)

def review_url(first_box_url, search_string) :
    
    u_client = requests.get(first_box_url)
    soup = bs(u_client.content, "html.parser")
    review_link_div = soup.find("div", {"class" : "swINJg"})
    reviews_link = base_url + review_link_div.find_parent()['href'] # Actually review link to extract the information
    print(reviews_link, search_string)
    return extract_reviews(reviews_link, 10, search_string)

def search_first_box_url(url, search_string) :
    
    u_client = requests.get(url)
    soup = bs(u_client.content, "html.parser")
    first_box_url = ""
    try :
        first_box_url = base_url + soup.find(class_ = "_31qSD5")['href'] # For vertical design
        print(first_box_url)
    except  Exception :
        first_box_url = base_url + soup.find(class_ = "Zhf2z-")['href'] # For horizontal design
        print(first_box_url)
    return review_url(first_box_url, search_string)



# search product name then we have to create the collections

@app.route("/", methods = ["GET", "POST"])
@cross_origin()
def home() :
    if request.method == "POST" :
        search_string = request.form['searchString'] # need to make a collections name = search_string
        search_string = search_string.replace(" ", "") 

        try : 
            if db[search_string].count_documents({}) > 0 :   # return the results
                reviews = db[search_string].find({})
                return render_template("result.html", reviews = reviews, file_name = search_string + ".csv")

            else : # Crawl from the sites
                url = base_url + "/search?q=" + str(search_string)
                print(url)
                dic_result = search_first_box_url(url, search_string)
                df = pd.DataFrame(dic_result)
                df.to_csv("static/CSVs/" + search_string + ".csv", index=False) # store into the csv folder
                reviews = db[search_string].find({})
                return render_template('result.html', reviews = reviews, file_name = search_string + ".csv")
        except Exception:
            print("Rarely going to happens")
    
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug = True)
