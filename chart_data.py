import requests
import json
import time
import uuid
from datetime import datetime

def generate_headers(client_id="K57626335"):
    """Generate headers with proper authentication tokens"""
    timestamp = int(time.time() * 1000)
    request_id = f"{client_id}_{timestamp}_{str(uuid.uuid4())}_{timestamp}"
    
    return {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "applicationname": "spark-web",
        "content-type": "application/json",
        "origin": "https://www.angelone.in",
        "priority": "u=1, i",
        "referer": "https://www.angelone.in/",
        "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "x-consumer": "SPARK_WEB",
        "x-requestid": request_id,
        "x-source": "https://www.angelone.in",
        "x-tokentype": "non_trade_access_token"
    }

def get_trading_data(symbol="3.500180", duration=5, bars=376):
    """
    Fetch trading data from AngelOne Charts API
    """
    # Generate current timestamp in the required format
    current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000+05:30")
    
    # Prepare the request payload
    payload = {
        "action": "Req",
        "topic": symbol,
        "rtype": "OHLCV",
        "period": "I",
        "type": "m",
        "duration": duration,
        "bars": bars,
        "to": current_time,
        "sort": "ASC"
    }
    
    # Get headers with authentication
    headers = generate_headers()
    
    # First make a request to the logger endpoint (seems to be required for auth)
    logger_url = "https://charts.angelone.in/charts/v1/logger/default"
    logger_payload = [{
        "sessionId": str(uuid.uuid4()),
        "clientId": "K57626335",
        "type": "fe",
        "level": "info",
        "message": "getBars called",
        "timestamp": int(time.time() * 1000),
        "userAgent": headers["user-agent"]
    }]
    
    try:
        # First make the logger request
        logger_response = requests.post(
            logger_url,
            headers=headers,
            json=logger_payload,
            timeout=10
        )
        
        if logger_response.status_code != 200:
            print(f"Logger request failed: {logger_response.status_code}")
            return None
        
        # Then make the actual data request
        data_url = "https://charts.angelone.in/charts/v2/bse/equity"
        response = requests.post(
            data_url,
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Data request failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Request error: {str(e)}")
        return None

def save_to_json(data, filename="trading_data.json"):
    """Save trading data to a JSON file"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Data saved to {filename}")

def main():
    print("Fetching trading data from AngelOne...")
    
    # Fetch real-time data
    trading_data = get_trading_data()
    
    if trading_data:
        # Save to JSON file
        save_to_json(trading_data)
        
        # Print some sample data
        print("\nSample Data:")
        if isinstance(trading_data, dict) and 'd' in trading_data:
            for i, item in enumerate(trading_data['d'][:5]):
                print(f"{i+1}. {item}")
        else:
            print("Received data:", trading_data)
    else:
        print("Failed to fetch trading data")

if __name__ == "__main__":
    main()