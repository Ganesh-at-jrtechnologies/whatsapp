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
    # PartyMaster.objects.filter(phone = "9908796859").update(phone = "6305979503")
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        # Pass vendor details to sender
        results = send_whatsapp(data)
        return JsonResponse({"status": "done", "results": results})

    return render(request, "test_whatsapp.html")
# @csrf_exempt
# def dashboard(request):
#     return render(request, "index.html")


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
            print(data)
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

            return JsonResponse({"success": "Invalid JSON"})
            
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    party_codes = PartyMaster.objects.values_list('party_master_code', flat=True)
    # Convert to Python list
    party_codes_list = list(party_codes)
    context ={'party_codes_list':party_codes_list}
    return render(request, "add_party.html",context)

def send_whatsapp_to_party(party_data: dict):
    """Send WhatsApp messages one by one with vendor-specific details"""
    results = []

    recipient = f"91{party_data.get('Phone')}" if party_data.get("Phone") else "916305979503"

    message = (
        f"Dear {party_data.get('Party_name','')},\n\n"
        f"Party Code: {party_data.get('Party_code','')}\n"
    )

    # Add bill details
    for bill in party_data.get("Bills", []):
        message += (
            f"Bill No: {bill.get('Bill Number', 'N/A')}\n"
            f"Bill Date: {bill.get('Bill Date', 'N/A')}\n"
            f"Bill Amount: {bill.get('Bill Amount', 0)}\n"
            f"O/S Amount: {bill.get('O/S Amount', 0)}\n\n"
        )

    # Add totals
    message += (
        f"Grand Total: {party_data.get('Grand_total', 0)}\n"
        f"Total O/S: {party_data.get('Total_os', 0)}\n"
    )
    if not party_data.get("Phone"):
        message += (
        f"\n\nPh :{party_data.get("Phone")} is not a valid whatsapp number"
        f"\n may be the party details is not entered in party master"
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

    return results


@csrf_exempt
def party_outstanding(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            all_results = []

            for p in data.get("data", []):
                party_data = {
                    "Party_code": p.get("PartyCode", ""),
                    "Party_name": p.get("PartyName", ""),
                    "Phone": p.get("phone", "6305979503"),  # fallback phone
                    # "Phone": "6305979503",  # fallback phone
                    "Bills": p.get("Bills", []),
                    "Grand_total": p.get("GRAND TOTAL", 0),
                    "Total_os": p.get("TOTAL O/S", 0),
                }

                result = send_whatsapp_to_party(party_data)
                all_results.extend(result)

                time.sleep(6)  # 6s delay between each

            return JsonResponse({"status": "done", "results": all_results})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    # GET request - provide party data with phone numbers
    party_data = list(PartyMaster.objects.values("party_master_code", "phone"))
    context = {"party_codes_list": party_data}
    return render(request, "party_outstanding.html", context)


def list_party_master(request):
    # GET request - provide party data with phone numbers
    party_data = list(PartyMaster.objects.values('party_master_code', 'phone','party_name'))

    context = {'party_codes_list': party_data}
    return render(request, "list_party_master.html", context)


