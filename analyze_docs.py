import json

def analyze():
    try:
        with open("docs.json", "r") as f:
            data = json.load(f)
            
        items = data.get("item", [])
        print(f"Found {len(items)} endpoints.")
        
        for item in items:
            name = item.get("name")
            request = item.get("request", {})
            url = request.get("url", "")
            method = request.get("method", "")
            print(f"\nEndpoint: {name} [{method} {url}]")
            
            # Check Body
            body = request.get("body", {}).get("raw", "")
            if body:
                print(f"  Body: {body[:100]}...")
                
            # Check Responses
            responses = item.get("response", [])
            print(f"  Example Responses: {len(responses)}")
            for resp in responses:
                print(f"    - {resp.get('name')}: {str(resp.get('body'))[:100]}...")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze()
