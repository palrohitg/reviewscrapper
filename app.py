from flask import Flask, render_template, request, redirect
from bs4 import BeautifulSoup as soup
from flask_cors import CORS, cross_origin
import requests 
import pymongo 
import pandas as pd 
import numpy as np
import os 
import shutil
import random
import string

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# path for csv files 
CSVs_path = os.path.join('static', 'CSVs')


# Global Varibles 
base_URL = "https://flipkart.com"
# dbConn = pymongo.MongoClient("mongodb+srv://mongodbuser:mongodbpassword@cluster0-lsptd.mongodb.net/test?retryWrites=true&w=majority")
# db_name = "flipkart"
# db = dbConn[db_name]

dic = {
     "title" : [],
     "review" : [],
     "user_name" : [],
     "rating" : []
} 


def get_prod_HTML(productLink=None) : 
    '''
    make the url request and fetch the data (HTML)
    '''
    prod_page_HTML = requests.get(productLink)
    return soup(prod_page_HTML.text, "html.parser")


def get_product_links(bigBoxes=None):
	'''
	returns the product link so we make the request to particular products
	'''
	# temporary list to return the results
	temp = []
	# iterate over list of bigBoxes
	for box in bigBoxes:
		try:
			# if prod name and list present then append them in temp
			temp.append(base_URL + box.div.div.a["href"])
		except:
			pass
	return temp



def comment_box_page_review_link(prod_page_HTML=None) :
    '''
    fetch the content of the pages and return the link of page that contain all reviews 
    '''
    # find all reviews link that redirect to review pages
    all_review_link_div = prod_page_HTML.find("div", {"class" : "_3UAT2v"})
    # review page links 
    reviews_link = base_URL + all_review_link_div.find_parent()['href'] 
    return reviews_link

 
def extract_reviews(review_link, no_of_review = 10, page_length = 10) :

    # Base Case 
    if (page_length == 0 or no_of_review == 0) :
        return dic


    prod_review_page_HTML = get_prod_HTML(review_link)
    all_review_divs = prod_review_page_HTML.findAll("div", {"class": "K0kLPL"})
    print(all_review_divs)

    for one_box in all_review_divs :
            """
                store the info in dictionary
            """
            if (no_of_review == 0) :
                break
            try :
                title = one_box.div.p.get_text()
                dic['title'].append(title)
            except :
                dic['title'].append("No Title")
            try :
                review = one_box.find(class_ = "_6K-7Co").get_text() 
                dic['review'].append(review)
            except :
                try : 
                    review = one_box.find(class_ = "").get_text()
                    dic['review'].append(review)  
                except : 
                    dic['review'].append("No Review")
            try :
                user_name = one_box.find(class_ = "_2V5EHH").get_text()
                dic['user_name'].append(user_name)
            except :
                dic['user_name'].append("No Username")
            try :
                rating = one_box.find(class_ = "_3LWZlK").get_text()
                dic['rating'].append(rating)
            except :
                dic['rating'].append("No rating") 
            no_of_review = no_of_review - 1
            print(no_of_review)

            
    next_review_link = ""
    # where next and page button is present
    list_length = len(prod_review_page_HTML.find_all("a", {"class" : "_1LKTO3"}))
        
    if(list_length == 1) :
        '''
        Get the link of next button if len=1
        we are at home page
        '''
        route_url = prod_review_page_HTML.find_all("a", {"class" : "_1LKTO3"})[0]['href']
        next_review_link = base_URL + route_url   
    elif(list_length == 2):
        '''
        we have two button prev and next 
        '''
        route_url = prod_review_page_HTML.find_all("a", {"class" : "_1LKTO3"})[1]['href']
        next_review_link = base_URL + route_url
    
    return extract_reviews(next_review_link,no_of_review, page_length - 1)
        

# def cleanCSV() :
#     shutil.rmtree(CSVs_path) 
#     os.mkdir(CSVs_path)
def clean_CSV_files():
    if os.listdir(CSVs_path) != list() :
        files = os.listdir(CSVs_path)
        for fileName in files : 
            print(fileName)
            os.remove(os.path.join(CSVs_path, fileName))
    
def random_string() :
    letters = string.ascii_lowercase
    randomString = ''.join(random.choice(letters) for i in range(10))
    return randomString


# search product name then we have to create the collection
@app.route("/")
@cross_origin()
def home() :
    return render_template("index.html")


@app.route("/result", methods = ["GET", "POST"]) 
def result() : 
    
    if request.method == "POST" :
        search_string = request.form['searchString'] # need to make a collections name = search_string
        search_string = search_string.replace(" ", "") # input = "real me" then "realme"  

        try : 

                # Concate the base-URL + Search Product Ex: https://flipkart/search?q=productName
                url = base_URL + "/search?q=" + str(search_string)
                # print(url)
                
                prod_page_HTML = get_prod_HTML(url)
                # print("product html is process")

                product_link_boxes = prod_page_HTML.find_all("div", {"class":"_13oc-S"})
                # print("big boxes link is proces") _13oc-S
                # Store the product link in list of search product 
                
                product_link_list = get_product_links(product_link_boxes)

                # iterate over the strings and find the link url 
                for link in product_link_list[: 1] : 
                    # get the html or each links 
                    prod_page_HTML = get_prod_HTML(link)
                    review_link = comment_box_page_review_link(prod_page_HTML)
                    extract_reviews(review_link)
                
                print("review scrapped......")
                
                # cleanCSV()

                data = pd.DataFrame.from_dict(dic) 
                # Store the file in csv folder
                data.to_csv("static/CSVs/" + search_string + ".csv", index=False) 
                dic.clear()
                return render_template('result.html', reviews = data, file_name = search_string + ".csv")
       
        except Exception as error: 
           
            error = "Our review scrapper cann't scraps this product could you checkout"
            return render_template('index.html', error=error)
    else :
        return redirect('/')

@app.route("/result-by-link", methods = ["GET", "POST"])
def resultByLink() : 
    if request.method == "POST" :
        try :
            link = request.form['searchStringLink']
            clean_CSV_files()
            no_of_review = int(request.form['noOfReview'])
            print(no_of_review)

            prod_page_HTML = get_prod_HTML(link)
            # print(prod_page_HTML)
            review_link = comment_box_page_review_link(prod_page_HTML)
            print(review_link)
            extract_reviews(review_link, no_of_review)
            # print(dic)
            data = pd.DataFrame.from_dict(dic)
            # print(data)

            fileName = random_string()

            data.to_csv("static/CSVs/" + fileName + ".csv", index=False) 
            dic.clear()

            return render_template('result.html', reviews = data, file_name =  fileName + ".csv")
       
        except Exception as error: 
            error = "Our review scrapper cann't scraps this product could you checkout another product item :)"
            return render_template('index.html', error=error)
    else :
        return redirect('/')

@app.route("/about")
def about() :
    return render_template("about.html")
# handle the non existing urls 
@app.errorhandler(404)
def page_not_found(e):
    return redirect("/")

if __name__ == "__main__":
    app.jinja_env.auto_reload = True
    app.run(debug=True, host='0.0.0.0')
    # app.run(host='127.0.0.1', port=8000)
