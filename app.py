from flask import Flask, render_template, request,jsonify
from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import logging
logging.basicConfig(filename="scrapper.log" , level=logging.INFO)
import pymongo
import creds

app = Flask(__name__)

@app.route("/", methods = ['GET'])
@cross_origin()
def homepage():
    return render_template("index.html")

@app.route("/review" , methods = ['POST' , 'GET'])
@cross_origin()
def index():
    if request.method != 'POST':
        return render_template('index.html')
    try:
        searchString = request.form['content'].replace(" ","")
        flipkart_url = f"https://www.flipkart.com/search?q={searchString}"
        uClient = uReq(flipkart_url)
        flipkartPage = uClient.read()
        uClient.close()
        flipkart_html = bs(flipkartPage, "html.parser")
        bigboxes = flipkart_html.findAll("div", {"class": "_1AtVbE col-12-12"})
        del bigboxes[:3]
        box = bigboxes[0]
        productLink = "https://www.flipkart.com" + box.div.div.div.a['href']
        prodRes = requests.get(productLink)
        prodRes.encoding='utf-8'
        prod_html = bs(prodRes.text, "html.parser")
        print(prod_html)
        commentboxes = prod_html.find_all('div', {'class': "_16PBlm"})

        filename = f"{searchString}.csv"
        fw = open(filename, "w")
        headers = "Product, Customer Name, Rating, Heading, Comment \n"
        fw.write(headers)
        reviews = []
        for commentbox in commentboxes:
            try:
                #name.encode(encoding='utf-8')
                name = commentbox.div.div.find_all('p', {'class': '_2sc7ZR _2V5EHH'})[0].text

            except Exception:
                logging.info("name")

            try:
                #rating.encode(encoding='utf-8')
                rating = commentbox.div.div.div.div.text


            except Exception:
                rating = 'No Rating'
                logging.info("rating")

            try:
                #commentHead.encode(encoding='utf-8')
                commentHead = commentbox.div.div.div.p.text

            except Exception:
                commentHead = 'No Comment Heading'
                logging.info(commentHead)
            try:
                comtag = commentbox.div.div.find_all('div', {'class': ''})
                #custComment.encode(encoding='utf-8')
                custComment = comtag[0].div.text
            except Exception as e:
                logging.info(e)

            mydict = {"Product": searchString, "Name": name, "Rating": rating, "CommentHead": commentHead,
                      "Comment": custComment}
            reviews.append(mydict)
        logging.info(f"log my final result {reviews}")

        client = pymongo.MongoClient(creds.MONGO_CREDS)
        db = client['review_scrap']

        review_coll = db['review_scrap_data']
        review_coll.insert_many(reviews)

        return render_template('result.html', reviews=reviews[:-1])
    except Exception as e:
        logging.info(e)
        return 'something is wrong'


if __name__=="__main__":
    app.run("127.0.0.1", port = 8000, debug=True)
