import requests
import urllib.parse
from datetime import datetime

def send_otp_sms(name, mobile, point, otp):
    content = f"Hello {name} ID:OTP: {otp}, You Account has been Updated Successfully. Your Current Point is {point:.2f}. OTP: {otp}. Thank you for Shopping @ Kurinji"
    encoded_msg = urllib.parse.quote(content)
    dtTimeNow = urllib.parse.quote(datetime.now().strftime('%m/%d/%Y %I:%M:%S %p'))

    url = (
        "https://www.smsintegra.net/api/smsapi.aspx"
        "?uid=zaagaa.com"
        "&pwd=vicky123"
        f"&mobile={mobile}"
        f"&msg={encoded_msg}"
        "&sid=KURINJ"
        "&type=0"
        f"&dtTimeNow={dtTimeNow}"
        "&entityid=1601100000000002855"
        "&tempid=1607100000000118145"
    )

    try:
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ SMS Error: {e}")
        return False
