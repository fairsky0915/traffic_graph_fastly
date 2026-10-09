# Fastly Traffic Graph

This tool creates comparison graphs for Fastly traffic statistics using data retrieved from the Fastly Stats API.

The following comparisons are supported:

- Bandwidth MoM (Month-over-Month)
- Bandwidth YoY (Year-over-Year)
- Requests MoM (Month-over-Month)
- Requests YoY (Year-over-Year)

## Requirements

Python 3 and matplotlib are required.

Install matplotlib if necessary:

    python3 -m pip install matplotlib


## 1. Retrieve Data from the Fastly API

Retrieve daily statistics from the Fastly Stats API and save the results as JSON files.

### Bandwidth Data

    curl -s "https://api.fastly.com/stats/service/[Service-ID]/field/bandwidth?by=day&from=[START-TIMESTAMP]&to=[END-TIMESTAMP]" \
      -H "Fastly-Key: [Fastly-API-Token]" \
      -H "Accept: application/json" \
      | jq '{data: [.data[] | {start_time, bandwidth}]}' \
      > customer-bandwidth-2606.json

Example:

    curl -s "https://api.fastly.com/stats/service/[Service-ID]/field/bandwidth?by=day&from=1780272000&to=1782864000" \
      -H "Fastly-Key: [Fastly-API-Token]" \
      -H "Accept: application/json" \
      | jq '{data: [.data[] | {start_time, bandwidth}]}' \
      > customer-bandwidth-2606.json


### Requests Data

    curl -s "https://api.fastly.com/stats/service/[Service-ID]/field/requests?by=day&from=[START-TIMESTAMP]&to=[END-TIMESTAMP]" \
      -H "Fastly-Key: [Fastly-API-Token]" \
      -H "Accept: application/json" \
      | jq '{data: [.data[] | {start_time, requests}]}' \
      > customer-requests-2606.json

Example:

    curl -s "https://api.fastly.com/stats/service/[Service-ID]/field/requests?by=day&from=1780272000&to=1782864000" \
      -H "Fastly-Key: [Fastly-API-Token]" \
      -H "Accept: application/json" \
      | jq '{data: [.data[] | {start_time, requests}]}' \
      > customer-requests-2606.json


## 2. JSON File Naming

The recommended filename format is:

    [customer]-[metric]-YYMM.json

Examples:

    customer-bandwidth-2606.json
    customer-bandwidth-2605.json
    customer-bandwidth-2506.json

    customer-requests-2606.json
    customer-requests-2605.json
    customer-requests-2506.json

Where:

- `2606` = June 2026
- `2605` = May 2026
- `2506` = June 2025


## 3. Create Graphs

The four graph types are now handled by a single script:

    traffic-graph.py

Command syntax:

    python3 traffic-graph.py [metric] [comparison] [current.json] [previous.json]

Available metrics:

    bandwidth
    requests

Available comparison types:

    mom
    yoy


## 4. Bandwidth Graph

### Month-over-Month (MoM)

Compare June 2026 with May 2026:

    python3 traffic-graph.py bandwidth mom \
      customer-bandwidth-2606.json \
      customer-bandwidth-2605.json


### Year-over-Year (YoY)

Compare June 2026 with June 2025:

    python3 traffic-graph.py bandwidth yoy \
      customer-bandwidth-2606.json \
      customer-bandwidth-2506.json


## 5. Requests Graph

### Month-over-Month (MoM)

Compare June 2026 with May 2026:

    python3 traffic-graph.py requests mom \
      customer-requests-2606.json \
      customer-requests-2605.json


### Year-over-Year (YoY)

Compare June 2026 with June 2025:

    python3 traffic-graph.py requests yoy \
      customer-requests-2606.json \
      customer-requests-2506.json


## 6. Graph Information

The generated graph includes:

- Total traffic for each period
- Increase or decrease compared with the previous period
- Percentage change
- Daily traffic
- Peak traffic date
- Peak traffic value
- Comparison period labels

Bandwidth is displayed in PB (Petabytes).

Requests are displayed in Billions.


## Example Workflow

Retrieve Bandwidth data:

    curl -s "https://api.fastly.com/stats/service/[Service-ID]/field/bandwidth?by=day&from=1780272000&to=1782864000" \
      -H "Fastly-Key: [Fastly-API-Token]" \
      -H "Accept: application/json" \
      | jq '{data: [.data[] | {start_time, bandwidth}]}' \
      > customer-bandwidth-2606.json

Retrieve Requests data:

    curl -s "https://api.fastly.com/stats/service/[Service-ID]/field/requests?by=day&from=1780272000&to=1782864000" \
      -H "Fastly-Key: [Fastly-API-Token]" \
      -H "Accept: application/json" \
      | jq '{data: [.data[] | {start_time, requests}]}' \
      > customer-requests-2606.json

Create a Bandwidth YoY graph:

    python3 traffic-graph.py bandwidth yoy \
      customer-bandwidth-2606.json \
      customer-bandwidth-2506.json

Create a Requests MoM graph:

    python3 traffic-graph.py requests mom \
      customer-requests-2606.json \
      customer-requests-2605.json

<img width="1600" height="900" alt="band-com-copy" src="https://github.com/user-attachments/assets/5c45bd68-589b-4cf9-a98b-5e8835dd183d" />
<img width="1600" height="900" alt="requests-com-copy" src="https://github.com/user-attachments/assets/952c32bc-bc58-4d7c-bfbc-2c54ef2ad060" />
