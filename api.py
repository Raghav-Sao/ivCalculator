from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from scipy.stats import norm
import datetime
# To calculate IV
import mibian
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024

def newtons_method(f, fprime, R = 0, max_iter = 1000, tol=1e-3, args = [], debug = False):
    count = 0
    epsilon = 1
    f_return = []
    fprime_return = []
    
    while epsilon >= tol:
        count += 1
        if count >= max_iter:
            print('Exiting on runaway loop.')
            return (R, count)
        
        old_R = R
        
        function_value = f(R, args = args)
        function_derivative = fprime(R, args = args)
        ind = np.where(function_derivative <= 0)
        ind = ind[0]
       
        R = -function_value / function_derivative + R
        
        if ind.size > 0:
            R[ ind ] = R[ ind ] * 0.5 + R[ ind ]
            
        if np.isscalar(R):
            epsilon = np.abs( (R - old_R) /old_R )
        else:
            epsilon = np.linalg.norm( R - old_R, np.Inf)
        
        if debug == True:
            f_return.append(function_value)
            fprime_return.append(function_derivative)
        
    return R, count
    
def call_price(sigma, S, K, r, t):
    d1 = np.multiply( 1. / sigma * np.divide(1., np.sqrt(t)),
        np.log(S/K) + (r + sigma**2 / 2.) * t  )
    d2 = d1 - sigma * np.sqrt(t)
    
    C = np.multiply(S, norm.cdf(d1)) - \
        np.multiply(norm.cdf(d2) * K, np.exp(-r * t))
    return C

def put_price(sigma, S, K, r, t):
    d1 = np.multiply( 1. / sigma * np.divide(1., np.sqrt(t)),
        np.log(S/K) + (r + sigma**2 / 2.) * t  )
    d2 = d1 - sigma * np.sqrt(t)
    
    P = -np.multiply(S, norm.cdf(-d1)) + \
        np.multiply(norm.cdf(-d2) * K, np.exp(-r * t))
    return P

def call_objective_function(sigma, args):
    S = args[0]
    K = args[1]
    r = args[2]
    t = args[3]
    price = args[4]
    
    return call_price(sigma, S, K, r, t) - price

def put_objective_function(sigma, args):
    S = args[0]
    K = args[1]
    r = args[2]
    t = args[3]
    price = args[4]
    
    return put_price(sigma, S, K, r, t) - price

def calculate_vega(sigma, args):
    S = args[0]
    K = args[1]
    r = args[2]
    t = args[3]
    
    d1 = np.multiply( 1. / sigma * np.divide(1., np.sqrt(t)),
        np.log(S/K) + (r + sigma**2 / 2.) * t  )
    d2 = d1 - sigma * np.sqrt(t)
    
    return S * norm.pdf(d1) * np.sqrt(t)

    return np.where(f_value > 0)


@app.route('/iv/', methods=['POST'])
def post_something():
    try:
        reqData = request.get_json()
        print(reqData)
        strike = reqData['strike']
        currentPrice = reqData['currentPrice']
        optionPrice = reqData['optionPrice']
        iRate = reqData['iRate']
        time = reqData['time']
        optionType = reqData['optionType'] or 'CE';
        # strike = 17800
        print(strike, strike)
        # currentPrice = 17700
        # optionPrice = (105 + 106) / 2  
        # iRate = 0.0293 
        # time = 6/365
    except Exception as e:
        print(e)
        return jsonify({
            "ERROR": "eeplease pass all params: strike, currentPrice,optionPrice, iRate, time "
        })

    args = (strike, currentPrice, iRate, 6/365, optionPrice)
    # sigma, count = newtons_method(call_objective_function if optionType == "CE" else put_objective_function, calculate_vega, 0.50, args = args)
    sigma, count = newtons_method(put_objective_function, calculate_vega, 0.50, args = args)
    # print(param)
    # You can add the test cases you made in the previous function, but in our case here you are just testing the POST functionality
    if strike and currentPrice and iRate and time and optionPrice:
        return jsonify({
            "iv": sigma,
            "count": count
        })
    else:
        return jsonify({
            strike,currentPrice, iRate,time,optionPrice,
           
        })

@app.route('/new-iv/', methods=['POST'])
def newIv():
    try:
        resData = {}
        reqData = request.get_json()
        print("before")
        for optionData in reqData:
            strike = optionData['strike']
            currentPrice = optionData['currentPrice']
            optionPrice = optionData['optionPrice']
            iRate = optionData['iRate']
            key = optionData['key']
            time = optionData['time']
            exactTime = optionData['exactTime']
            optionType = optionData['optionType'] or 'CE';
            c = mibian.BS([currentPrice, strike, iRate, time],callPrice=optionPrice) if optionType == 'CE' else mibian.BS([currentPrice, strike, iRate, time],putPrice=optionPrice)
            cExact = mibian.BS([currentPrice, strike, iRate, exactTime],callPrice=optionPrice) if optionType == 'CE' else mibian.BS([currentPrice, strike, iRate, time],putPrice=optionPrice)
            # optionData["iv"] = round(c.impliedVolatility, 2)
            resData[key] = {
                "iv": round(c.impliedVolatility, 2),
                "exactIv": round(cExact.impliedVolatility, 2)
            }
            print(round(c.impliedVolatility, 2))
            print(round(cExact.impliedVolatility, 2), "d")
        print("done")
        return jsonify({
            "resData":  resData
        })

    except Exception as e:
        print(e)
        return jsonify({
            "error": "eeplease pass all params: strike, currentPrice,optionPrice, iRate, time "
        })



@app.route('/')
def index():
    print("here")
    # A welcome message to test our server
    return "<h1>Welcome to our medium-greeting-api!</h1>"


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    port = 8000
    # try:
    #     port = process.env.PORT
    # except:
    #     print("error port")
    
    app.run( port=port)

