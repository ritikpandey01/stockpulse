import requests

url = "http://127.0.0.1:8000/api/analyze"
payload = {
    "symbol": "AAPL",
    "period": "1mo",
    "interval": "1d",
    "timeframe": "1d"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Success!")
        print("Chart data points:", len(data.get("chart_data", [])))
        print("First chart data point:", data.get("chart_data", [])[0] if data.get("chart_data") else "None")
    else:
        print("Error:", response.text)
except Exception as e:
    print("Exception:", e)
