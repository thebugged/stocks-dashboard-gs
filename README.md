<div align="center">
  <br />
    <a href="https://stocks-dashboard-gs.streamlit.app/" target="_blank">
      <img src="" alt="Banner">
    </a>
  <br />

  <div>
    <img src="https://img.shields.io/badge/-Python-black?style=for-the-badge&logoColor=white&logo=python&color=3776AB" alt="python" />
    <img src="https://img.shields.io/badge/-Pandas-black?style=for-the-badge&logoColor=white&logo=pandas&color=150458" alt="pandas" />
    <img src="https://img.shields.io/badge/-Plotly-black?style=for-the-badge&logoColor=white&logo=plotly&color=3F4F75" alt="plotly" />
    <img src="https://img.shields.io/badge/-Google_Cloud-black?style=for-the-badge&logoColor=white&logo=google-cloud&color=4285F4" alt="google cloud" />
</div>


  <h3 align="center">Stocks Dashboard</h3>

   <div align="center">
     A stocks dashboard app created in Python using Streamlit with insights on populat stocks. 
    </div>
</div>
<br/>



## Setup & Installation
**Prerequisites**

Ensure the following are installed
- [Git](https://git-scm.com/)
- [Python](https://www.python.org/downloads/)
  
To set up this project locally, follow these steps:

1. Clone the repository:
```shell
git clone https://github.com/thebugged/stocks-dashboard-gs.git
```

2. Change into the project directory: 
```shell
cd stocks-dashboard-gs
```

3. Install the required dependencies: 
```shell
pip install -r requirements.txt
```
<br/>

## Running the application
1. Run the command: 
```shell
streamlit run main.py
```

The application will be available in your browser at http://localhost:8501.


For the stock data the `Last Trade Time` &  `Date` columns may need to be genrated again. Run the following in the function cells respectively:
```shell
=GOOGLEFINANCE(A2, "tradetime")
=(GOOGLEFINANCE("AAPL", "all", DATE(2023, 1, 1), today()))
```


[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://stocks-dashboard-gs.streamlit.app/)


