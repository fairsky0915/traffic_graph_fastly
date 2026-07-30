# traffic_graph_fastly

1. It needs to take the bandwidth and Requests data via the API as below. And make it as JSON files.

- Bandwidth data
curl -i "https://api.fastly.com/stats/service/[Service ID]/field/bandwidth?by=day&from=1780272000&to=1782864000" -H "Fastly-Key: Fastly-API-Token" -H "Accept: application/json"

- Requests data
curl -i "https://api.fastly.com/stats/service/[Service ID]/field/requests?by=day&from=1780272000&to=1782864000" -H "Fastly-Key: Fastly-API-Token" -H "Accept: application/json"

2. Run Python with the data as below
- Creating Bandwidth Graph
python3 bandwidth-sum.py customer-bandwidth-2606.json customer-bandwidth-2506.json

- Creating Requests Graph
python3 requests-sum.py customer-requests-2606.json customer-requests-2605.json

<img width="1600" height="900" alt="band-com-copy" src="https://github.com/user-attachments/assets/5c45bd68-589b-4cf9-a98b-5e8835dd183d" />
<img width="1600" height="900" alt="requests-com-copy" src="https://github.com/user-attachments/assets/952c32bc-bc58-4d7c-bfbc-2c54ef2ad060" />
