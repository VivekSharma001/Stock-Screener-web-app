import os, csv
import talib
import yfinance as yf
import pandas 
from flask import Flask, escape, request, render_template, session, redirect, url_for
from patterns import candlestick_patterns
import numpy as np
import mplfinance as mpf
import matplotlib.pyplot as plt
import plotly.graph_objs as go


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    pattern  = request.args.get('pattern')

    stocks = {}

    with open('datasets/symbols.csv') as f:
        for row in csv.reader(f):
            stocks[row[0]] = {'company': row[1]}

    if pattern:
        for filename in os.listdir('datasets/daily'):
            df = pandas.read_csv('datasets/daily/{}'.format(filename), encoding= 'unicode_escape')
            pattern_function = getattr(talib, pattern)
            symbol = filename.split('.')[0]


            try:
                df["MA"] = df["Close"].rolling(21).mean()
                df.dropna()
                df["trend"] = np.where(df["Close"] > df["MA"], "Up-Trend", "Down-trend")

                rsi = talib.RSI(df['Close'])
                df['rsi'] = rsi


                stocks[symbol]["trend"] = df["trend"].tail(1).values[0]
                stocks[symbol]["rsi"] = df["rsi"].tail(1).values[0]


                results = pattern_function(df['Open'], df['High'], df['Low'], df['Close'])
                last = results.tail(1).values[0]

                if last > 0:
                    stocks[symbol][pattern] = 'Bullish'
                elif last < 0:
                    stocks[symbol][pattern] = 'Bearish'
                else:
                    stocks[symbol][pattern] = None   
                
            except Exception as e:
                print('failed on filename: ', filename)
            

    return render_template('index.html',stocks=stocks, pattern=pattern, candlestick_patterns=candlestick_patterns)


@app.route('/snapshot')
def snapshot():
    with open('datasets/symbols.csv') as f:
        for line in f:
            try:
                if "," not in line:
                    continue
                symbol = line.split(",")[0] + ".NS"
                data = yf.download(symbol, start="2023-03-03")
                data.to_csv('datasets/daily/{}.csv'.format(symbol))

                fig = go.Figure(
                go.Candlestick(
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close']
                    )
                )
                fig.write_image(f'static/{symbol}_candlestick_chart.png')

            except:
                print("Failed Download...")
            
            
    return {
        "code": "success"
    }
