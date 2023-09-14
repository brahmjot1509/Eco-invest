from flask import Flask, render_template, request, redirect, url_for, send_file
import allocate_capital
import get_rankings
import pandas as pd
import plotly
import json
import os
import insights_capital

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hwedfbuyhedbfwe3484747erh'
app.debug = True

#Home page:
@app.route('/')
def index():
    return render_template('index.html')

#Allocation page getting user input to create portfolio:
@app.route('/allocation', methods=['GET', 'POST'])
def allocation():
    if request.method == 'POST':
        return redirect(url_for("portfolio"))
    else:
        return render_template('allocation.html')

#Allocation page giving the portfolio from user input:
@app.route("/allocation/portfolio", methods=['GET', 'POST'])
def portfolio():
    #Get user input data from form:
    e_scr = request.form["E"]                         #Environmental
    s_scr = request.form["S"]                         #Social
    g_scr = request.form["G"]                         #Governance
    risk = float(request.form["risk"])                #Risk-aversion
    del_sectors = request.form.getlist("sectors")     #Sectors to delete
    del_symbs = request.form.get("symb").split(',')   #Stocks to delete

    #Get portfolio charts and metrics with user inputs from the allocation algo:
    metrics, fig_stocks, fig_sectors = allocate_capital.get_portfolio(e_scr,
                                                                      s_scr,
                                                                      g_scr,
                                                                      risk,
                                                                      del_sectors,
                                                                      del_symbs)
    #Use JSON and Plotly to display charts on the webpage:
    port_stocks = json.dumps(fig_stocks, cls=plotly.utils.PlotlyJSONEncoder)
    port_sectors = json.dumps(fig_sectors, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('portfolio.html', graph_stocks=port_stocks,
                                             graph_sectors = port_sectors,
                                             e_scr=metrics['E_scr'],
                                             s_scr=metrics['S_scr'],
                                             g_scr=metrics['G_scr'],
                                             esg_scr=metrics['ESG_scr'],
                                             ret=metrics['Ret'],
                                             vol=metrics['Vol'],
                                             beta=metrics['beta'])

#Route to allow downloading option of CSV file of allocations:
@app.route("/download")
def download_csv():
    f = os.path.join("static", "data", "portfolio.csv") 
    return send_file(f, as_attachment=True)

#Ratings search page:
@app.route("/ratings", methods=['GET', 'POST'])
def ratings():
    #Read in stock symbols and their ESG data:
    data_path = os.path.join("static", "data", "stock_data.csv")  
    data = pd.read_csv(data_path, index_col='ticker')

    #If user submits a stock symbol, show that new page with the ratings:
    if request.method == "POST":
        stock = request.form['symbol-rating']
        return redirect(url_for('stock_ratings', symbol=stock))

    #If user simply requests to see this page, show it instead:
    else:
        return render_template('ratings.html', data=data)

@app.route("/insights", methods=['GET', 'POST'])
def insights():
    #Read in stock symbols and their ESG data:
    data_path = os.path.join("static", "data", "insights.csv")  
    data = pd.read_csv(data_path, index_col='company')

    #If user submits a stock symbol, show that new page with the ratings:
    if request.method == "POST":
        stock = request.form['symbol-rating']
        return redirect(url_for('insight_ratings', symbol=stock))

    #If user simply requests to see this page, show it instead:
    else:
        return render_template('insights.html', data=data)
    
#Ratings page for each symbol searched above:
@app.route("/insights/<symbol>",methods=['GET', 'POST'])
def insight_ratings(symbol):
    #Get ESG rankings and stock info:
    if request.method == "POST":
        symbol = request.form.get("stock")
        pdflink = request.form.get("pdflink")
        return redirect(url_for('esvbert', symbol=symbol,pdflink=pdflink))
    else:
        symbolegs = insights_capital.get_data(symbol)
        return render_template('insight_ratings.html', symbolegs=symbolegs, stock=symbol)
    

@app.route("/insightses/american-express", methods=['GET'])
def insight_ratin():
    result = {
        "Water_And_Wastewater_Management": 0.926709,
        "Waste_And_Hazardous_Materials_Management": 0.841204,
        "Employee_Health_And_Safety": 0.819615,
        "Ecological_Impacts": 0.806052,
        "Critical_Incident_Risk_Management": 0.795947,
        "Human_Rights_And_Community_Relations": 0.775221,
        "Director_Removal": 0.770194,
        "Labor_Practices": 0.764706,
        "Supply_Chain_Management": 0.754043,
        "Energy_Management": 0.752816,
        "Employee_Engagement_Inclusion_And_Diversity": 0.731186,
        "Physical_Impacts_Of_Climate_Change": 0.722682,
        "GHG_Emissions": 0.714976,
        "Product_Design_And_Lifecycle_Management": 0.675337,
        "Air_Quality": 0.638558,
        "Access_And_Affordability": 0.585631,
        "Business_Ethics": 0.536834,
        "Selling_Practices_And_Product_Labeling": 0.468875,
        "Product_Quality_And_Safety": 0.457648,
        "Systemic_Risk_Management": 0.452228,
        "Customer_Privacy": 0.432529,
        "Data_Security": 0.420697,
        "Management_Of_Legal_And_Regulatory_Framework": 0.373227,
        "Customer_Welfare": 0.372367,
        "Business_Model_Resilience": 0.364371,
        "Competitive_Behavior": 0.22628
    }
    num_data = {'E_Rating': 7.6029901175215375, 'S_Rating': 6.330999078589446, 'G_Rating': 5.462593548137734, 'Total_ESG_Rating': 6.465527581416239}
    letter_data = {'E_Letter_Score': 'AA', 'S_Letter_Score': 'A', 'G_Letter_Score': 'BBB', 'Total_ESG_Letter_Score': 'A'}
    return render_template('insightsesv.html', companyName='American Express', num_data = num_data, letter_data = letter_data ,result_dict =result)

        
@app.route("/insightsesv/<symbol>")
def esvbert(symbol):
    #Get ESG rankings and stock info:
    # symbol_info = insight_ratings.run_classifier()
    pdflink = request.args.get('pdflink')
    df=insights_capital.run_classifier(pdflink)
    grouped_mean = df.groupby(['label']).mean()
    result_dict = {label: value['score'] for label, value in grouped_mean.to_dict(orient='index').items()}
    num_data= insights_capital.calculate_msci_esg_score(result_dict)
    letter_data =insights_capital.calculate_esg_ratings(num_data)
    return render_template('insightsesv.html', companyName=symbol, num_data = num_data, letter_data = letter_data,result_dict =result_dict )

#Ratings page for each symbol searched above:
@app.route("/ratings/<symbol>")
def stock_ratings(symbol):
    #Get ESG rankings and stock info:
    
    symbol_info = get_rankings.get_company(symbol)

    return render_template('stock_ratings.html', symb_info=symbol_info, stock=symbol)

#Main methodologies page to see allocation and rating methods:
@app.route("/methodologies")
def methodologies():
    return render_template('methodologies.html')

#Methodology page for allocation model:
@app.route("/methodologies/allocation")
def allocation_methodology():
    return render_template('alloc_method.html')

#Methodology page for scoring firms on ESG criteria:
@app.route("/methodologies/esg-scores")
def scoring_methodology():
    return render_template('scoring_method.html')

#Methodology page for technology tools used:
@app.route("/methodologies/tech-used")
def tech_methodology():
    return render_template('tech_method.html')

@app.route("/download_excel")
def download_excel():
    # Send the Excel file to the user
    return send_file("static/data/result.xlsx", as_attachment=True)


if __name__ == '__main__':
  app.run(port=5000)