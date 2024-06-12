# Archived Logs Service

Log archive available timing depends on the __device’s time-zone__.The timing for handling log archives varies depending on the time zone of the device.

<table>
  <tr>
    <th>Region</th>
    <th>Processed Time</th>
  </tr>
  <tr>
    <td>Europe (UTC+0 to UTC+5)</th>
    <td>UTC 1:00</th>
  </tr>
  <tr>
    <td>Asia-Pacific (UTC+6 to UTC+14)</th>
    <td>UTC 13:00</th>
  </tr>
  <tr>
    <td>Others (UTC-12 to UTC-1)</th>
    <td>UTC 19:00</th>
  </tr>
</table>

__Note: these times are for handling log archives and do not necessarily indicate when the archive process is completed__. Use the following command to download logs from SecuReporter.
 


<details>
 <summary><code>POST</code><code>/open-api/v1/archive-logs/download</code></summary>

### Description
 Download archive logs which user-selected period for a single day within the past 31 days (excluding the current day).

### Usage Limitation
You can make up to 50 API request per `Open API Token` per Zyxel Device per hour

### Body Parameters

<table>
  <tr>
    <th>Name</th>
    <th>Type</th>
    <th>Data Type</th>
    <th>Description</th>
  </tr>
  <tr>
    <td>device_date</th>
    <td>required</th>
    <td>String</th>
    <td>format yyyy-MM-dd</th>
  </tr>
</table>

### Success Response

<table>
  <tr>
    <th>Response code</th>
    <th>Content Type</th>
    <th>Response</th>
  </tr>
  <tr>
    <td>200</th>
    <td>application/x-tar</th>
    <td>file-like object in binary mode</th>
  </tr>
</table>

### Example cURL

> ```shell
> curl -X POST https://secureporter.cloudcnm.zyxel.com/open-api/v1/archive-logs/download \
> -H "Content-Type: application/json" \
> -H "X-Authorization: Bearer your-open-api-token" \
> -d "{\"device_date\":\"2024-01-01\"}" \
> -o /Users/Downloads/archive.tar 
> ```

</details>
