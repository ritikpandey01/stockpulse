import requests
import json
import math

url = "http://127.0.0.1:8000/api/analyze"
payload = {"symbol": "AAPL", "period": "1mo", "interval": "1d"}

try:
    print("Testing /api/analyze with 1mo period...")
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("Success! Data parsed.")
        
        chart_data = data.get("chart_data", [])
        print(f"Chart data points extracted: {len(chart_data)}")
        if chart_data:
            print("First row:", chart_data[0])
            print("Last row:", chart_data[-1])
            
            # Check for NaN in JS string notation
            raw_text = response.text
            if "NaN" in raw_text:
                print("WARNING: 'NaN' leaked into the JSON serialization payload!")
            else:
                print("CLEAN: No 'NaN' values found in the response payload. It's perfectly completely clean for LightweightCharts.")
        
        indicator_data = data.get("indicator_data", [])
        print(f"Indicator points: {len(indicator_data)}")
        
    else:
        print("Error content:")
        print(response.text)
        
except Exception as e:
    print("Failed to run test:", e)
