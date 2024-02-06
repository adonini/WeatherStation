import time
from datetime import datetime
import asyncio
from opcua_utils import OPCUAConnection


async def main():
    while True:
        # Connect to OPC UA server as client and get the values
        ws = OPCUAConnection()
        data = await ws.connectANDread()

        if data:
            # Convert the date and time to a datetime object
            date_time_str = data['Date'] + data['Time']
            date_time = datetime.strptime(date_time_str, '%Y%m%d%H%M%S')

            # Create the text content
            text_content = f"<?xml version='1.0'?>\n" \
                f"<fitsheader>\n" \
                f"   <fitsitem name='WeatherStation.LST.date' value='{date_time.strftime('%Y-%m-%d %H:%M:%S')}'/>\n" \
                f"   <fitsitem name='WeatherStation.LST.LocalMastAirTemp' value='{data['Air Temperature']}'/>\n" \
                f"   <fitsitem name='WeatherStation.LST.LocalMastHumidity' value='{data['Relative Humidity']}'/>\n" \
                f"   <fitsitem name='WeatherStation.LST.LocalMastWindSpeed' value='{data['Mean Wind Speed']}'/>\n" \
                f"   <fitsitem name='WeatherStation.LST.LocalMastWindDirection' value='{data['Mean Wind Direction']}'/>\n" \
                f"   <fitsitem name='WeatherStation.LST.LocalMastPressure' value='{data['Absolute Air Pressure']}'/>\n" \
                f"</fitsheader>"

            # Write the text content to a file
            with open("WS10.txt", "w") as file:
                file.write(text_content)

            # sleep 50s before next pulling
            time.sleep(50)


if __name__ == "__main__":
    asyncio.run(main())
