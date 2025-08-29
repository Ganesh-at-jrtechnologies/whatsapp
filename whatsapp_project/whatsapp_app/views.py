from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import time
import requests
from .models import PartyMaster
from django.conf import settings

TEXTMEBOT_API_KEY = settings.TEXTMEBOT_API_KEY




@csrf_exempt
def dashboard(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        # Pass vendor details to sender
        results = send_whatsapp(data)
        return JsonResponse({"status": "done", "results": results})

    return render(request, "index.html")


def send_whatsapp(vendors):
    """Send WhatsApp messages one by one with vendor-specific details"""
    results = []

    for vendor in vendors:
        vendor_name = vendor.get("Vendor_Name")
        vendor_id = vendor.get("Vendor_Id")
        phone = vendor.get("Phone")
        bill_no = vendor.get("Bill_Id")
        bill_amount = vendor.get("Bill_Amount")
        pending_amount = vendor.get("Pending_Amount")

        if not phone:
            continue

        recipient = f"91{phone}"  # add country code
        message = (
            f"Dear {vendor_name},\n\n"
            f"Vendor ID: {vendor_id}\n"
            f"Bill No: {bill_no}\n"
            f"Bill Amount: {bill_amount}\n"
            f"Pending Amount: {pending_amount}"
        )

        url = "https://api.textmebot.com/send.php"
        params = {
            "recipient": recipient,
            "apikey": TEXTMEBOT_API_KEY,
            "text": message,
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            try:
                resp_data = response.json()
            except ValueError:
                resp_data = {"raw_response": response.text}

            results.append({
                "recipient": recipient,
                "status_code": response.status_code,
                "response": resp_data,
            })
        except requests.RequestException as e:
            results.append({
                "recipient": recipient,
                "status_code": "failed",
                "error": str(e),
            })

        time.sleep(6)  # ⚠️ still blocking (Celery is better for scaling)

    return results

@csrf_exempt
def party_master(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            for party in data:
                hul_code = party.get('HUL Code','N/A')
                party_master_code = party.get('Party Master Code','N/A')
                party_name = party.get('Party Name','N/A')
                beat = party.get('Beat','N/A')
                address = party.get('Address','N/A')
                phone = party.get('Phone','N/A')
                PartyMaster.objects.create(
                    party_master_code = party_master_code,
                    party_name = party_name,
                    phone = phone,
                    beat = beat,
                    hul_code = hul_code,
                    address = address
                )
            
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    party_codes = PartyMaster.objects.values_list('party_master_code', flat=True)
    # Convert to Python list
    party_codes_list = list(party_codes)
    context ={'party_codes_list':party_codes_list}
    return render(request, "party_master.html",context)

@csrf_exempt
def party_outstanding(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print(data)
            return JsonResponse({"error": "Invalid JSON"})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        # Pass vendor details to sender
        # results = send_whatsapp(data)
        # return JsonResponse({"status": "done", "results": results})

    # GET request - provide party data with phone numbers
    party_data = list(PartyMaster.objects.values('party_master_code', 'phone'))
    # print(party_data)

    context = {'party_codes_list': party_data}
    return render(request, "party_outstanding.html", context)


def list_party_master(request):
    # GET request - provide party data with phone numbers
    party_data = list(PartyMaster.objects.values('party_master_code', 'phone','party_name'))

    context = {'party_codes_list': party_data}
    return render(request, "list_party_master.html", context)


