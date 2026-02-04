
import json

raw_data = """
183	9MOBILE	CORPORATE GIFTING	₦365.0	1.0 GB	30 days
184	9MOBILE	CORPORATE GIFTING	₦548.0	1.5 GB	30 days
185	9MOBILE	CORPORATE GIFTING	₦720.0	2.0 GB	30 days
186	9MOBILE	CORPORATE GIFTING	₦1095.0	3.0 GB	30 days
188	9MOBILE	CORPORATE GIFTING	₦1825.0	5.0 GB	30 days
189	9MOBILE	CORPORATE GIFTING	₦3650.0	10.0 GB	30 days
221	9MOBILE	CORPORATE GIFTING	₦182.0	500.0 MB	30 days
229	9MOBILE	CORPORATE GIFTING	₦7300.0	20.0 GB	Monthly
265	9MOBILE	CORPORATE GIFTING	₦1460.0	4.0 GB	30 month
281	AIRTEL	SME	₦60.0	150.0 MB	1 day
367	AIRTEL	CORPORATE GIFTING	₦345.0	1.0 GB	3 days (Social)
374	AIRTEL	SME	₦345.0	1.0 GB	3 days (Social)
375	AIRTEL	CORPORATE GIFTING	₦545.0	500.0 MB	7 days
376	AIRTEL	CORPORATE GIFTING	₦1545.0	2.0 GB	30 days
377	AIRTEL	CORPORATE GIFTING	₦2045.0	3.0 GB	30days
379	AIRTEL	CORPORATE GIFTING	₦8045.0	25.0 GB	30days
380	AIRTEL	CORPORATE GIFTING	₦15045.0	60.0 GB	30days
381	AIRTEL	CORPORATE GIFTING	₦4045.0	10.0 GB	30 days
382	AIRTEL	SME	₦645.0	1.5 GB	2 days
383	AIRTEL	SME	₦800.0	2.0 GB	2 days
384	AIRTEL	SME	₦1545.0	5.0 GB	7 days
385	AIRTEL	CORPORATE GIFTING	₦1545.0	5.0 GB	7 days
386	AIRTEL	CORPORATE GIFTING	₦800.0	2.0 GB	2 days
387	AIRTEL	CORPORATE GIFTING	₦645.0	1.5 GB	2 days
404	AIRTEL	SME	₦245.0	600.0 MB	2 says
405	AIRTEL	SME	₦145.0	300.0 MB	2 days
406	AIRTEL	CORPORATE GIFTING	₦245.0	600.0 MB	2 days
412	AIRTEL	SME	₦3050.0	10.0 GB	30 days
425	AIRTEL	CORPORATE GIFTING	₦1045.0	1.5 GB	7 days
427	AIRTEL	CORPORATE GIFTING	₦2545.0	4.0 GB	30 days
428	AIRTEL	CORPORATE GIFTING	₦800.0	1.0 GB	7 days
429	AIRTEL	CORPORATE GIFTING	₦3045.0	8.0 GB	30 days
194	GLO	CORPORATE GIFTING	₦425.0	1.0 GB	30days
195	GLO	CORPORATE GIFTING	₦850.0	2.0 GB	30days
196	GLO	CORPORATE GIFTING	₦1275.0	3.0 GB	30days
197	GLO	CORPORATE GIFTING	₦2125.0	5.0 GB	30days
200	GLO	CORPORATE GIFTING	₦4250.0	10.0 GB	30days
203	GLO	CORPORATE GIFTING	₦215.0	500.0 MB	14 days
225	GLO	CORPORATE GIFTING	₦90.0	200.0 MB	14 days
275	GLO	SME	₦192.0	750.0 MB	1
276	GLO	SME	₦290.0	1.5 GB	1 days
277	GLO	SME	₦480.0	2.5 GB	2 days
278	GLO	SME	₦1930.0	10.0 GB	7 days
396	GLO	SME	₦275.0	1.0 GB	3 days
397	GLO	SME	₦825.0	3.0 GB	3 days
398	GLO	SME	₦1375.0	5.0 GB	3 days
399	GLO	CORPORATE GIFTING	₦325.0	1.0 GB	7 days
400	GLO	CORPORATE GIFTING	₦975.0	3.0 GB	7 days
401	GLO	CORPORATE GIFTING	₦1625.0	5.0 GB	7 days
215	MTN	GIFTING	₦490.0	1.0 GB	1 days
218	MTN	GIFTING	₦990.0	3.2 GB	2 days
219	MTN	GIFTING	₦2460.0	6.0 GB	7 days
300	MTN	GIFTING	₦17640.0	75.0 GB	30 days
302	MTN	GIFTING	₦3430.0	11.0 GB	7 days
310	MTN	SME2	₦1680.0	3.0 GB	30 days
320	MTN	SME	₦196.0	230.0 MB	1 day
321	MTN	SME	₦735.0	1.2 GB	7 days (Pulse)
327	MTN	SME	₦2450.0	6.0 GB	7 days
328	MTN	GIFTING	₦735.0	2.0 GB	2 days
329	MTN	GIFTING	₦882.0	2.5 GB	2 days
334	MTN	SME	₦441.0	750.0 MB	3 days
335	MTN	SME	₦1470.0	2.0 GB	30 days
336	MTN	SME	₦1980.0	3.0 GB	30 days
339	MTN	SME	₦6370.0	16.5 GB	30 days +10 Mins call
340	MTN	SME	₦785.0	1.0 GB	7 days
343	MTN	GIFTING	₦4900.0	14.5 GB	(XtraSpecial) 30 days
345	MTN	GIFTING	₦5390.0	12.5 GB	30 days +2gb YT
346	MTN	GIFTING	₦4410.0	10.0 GB	30 days(+10mins+2gb YT)
348	MTN	GIFTING	₦98.0	110.0 MB	1 day
349	MTN	GIFTING	₦2450.0	3.5 GB	30 days +5mins +2gb Night
350	MTN	SME	₦490.0	500.0 MB	7 days
358	MTN	GIFTING	₦1470.0	1.2 GB	30 days +N1500 for call+100SM
360	MTN	SME	₦980.0	1.5 GB	7 days
361	MTN	SME	₦588.0	1.5 GB	2 days
362	MTN	GIFTING	₦490.0	500.0 MB	1 days
366	MTN	SME2	₦2800.0	5.0 GB	30 days
369	MTN	GIFTING	₦7350.0	20.0 GB	30 days
370	MTN	GIFTING	₦10780.0	36.0 GB	30 days
371	MTN	GIFTING	₦3430.0	7.0 GB	30 days
372	MTN	SME	₦3100.0	5.0 GB	30 days
403	MTN	SME2	₦1120.0	2.0 GB	30days
407	MTN	SME	₦1485.0	3.5 GB	7 days
408	MTN	SME	₦3465.0	11.0 GB	7 days
409	MTN	SME2	₦560.0	1.0 GB	7 days
414	MTN	GIFTING	₦33950.0	165.0 GB	30 days
415	MTN	GIFTING	₦785.0	1.0 GB	7 days
416	MTN	SME2	₦400.0	500.0 MB	5 day
417	MTN	SME2	₦610.0	1.0 GB	30 days
419	MTN	SME	₦235.0	1.0 GB	1 day
420	MTN	SME	₦580.0	2.5 GB	1 day
423	MTN	GIFTING	₦235.0	1.0 GB	1 day
424	MTN	GIFTING	₦580.0	2.5 GB	1 day
"""

net_ids = {"MTN": "1", "GLO": "2", "9MOBILE": "3", "AIRTEL": "4"}

lines = raw_data.strip().split('\n')
output = "DATA_PLANS = [\n"
for line in lines:
    parts = line.split('\t')
    if len(parts) < 6:
        continue
        
    pid = parts[0].strip()
    network = parts[1].strip()
    p_type = parts[2].strip()
    amount_str = parts[3].strip().replace('₦', '').replace(',', '')
    size = parts[4].strip()
    validity = parts[5].strip()
    
    try:
        amount = float(amount_str)
    except:
        amount = 0.0

    # Determine type slug
    type_slug = "sme"
    if "GIFTING" in p_type.upper():
        if "CORPORATE" in p_type.upper():
            type_slug = "corporate"
        else:
            type_slug = "gifting"
    elif "SME2" in p_type.upper():
        type_slug = "sme2"
    
    network_slug = network.lower().replace(" ", "")
    
    # Internal ID construction
    # Adding pid to avoid collision if size/type same
    internal_id = f"{network_slug}-{type_slug}-{size.lower().replace(' ', '')}-{pid}"
    
    # Name construction
    name = f"{network} {p_type.title()} {size} {validity}"

    # Selling price margin: +10 if < 1000, +20 if > 1000? 
    # For now, I'll match amount + 10.
    selling_price = amount + 10
    if amount == 0: selling_price = 0

    output += "    {\n"
    output += f'        "id": "{internal_id}",\n'
    output += f'        "network": "{network_slug}",\n'
    output += f'        "type": "{type_slug}",\n'
    output += f'        "name": "{name}",\n'
    output += f'        "size": "{size}",\n'
    output += f'        "validity": "{validity}",\n'
    output += f'        "cost_price": {amount},\n'
    output += f'        "selling_price": {selling_price},\n' 
    output += f'        "datastation_network_id": "{net_ids.get(network, "0")}",\n'
    output += f'        "datastation_plan_id": "{pid}"\n'
    output += "    },\n"

output += "]\n\n"
output += """def get_plan_by_id(plan_id):
    for p in DATA_PLANS:
        if p["id"] == plan_id:
            return p
    return None
"""

with open("plans/data_plans.py", "w", encoding='utf-8') as f:
    f.write(output)

print("Done")
