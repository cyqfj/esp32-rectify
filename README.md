# esp32-rectify
Deviation correction machine controller developed based on esp32 and microWebSvr(https://github.com/jczic/MicroWebSrv)


1. Develop esp32 using microsython firmware to establish a web server

2. Connect to esp32 via mobile or PC:

XX.XX.XX.XX:8081

3. HTML has applied canvas to display simple working conditions and actions

4. Due to the use of threads in microWebSvr and the inability to access multiple terminals simultaneously, modifications have been made to microWebSvr,

Replacing threads with timers and coroutines can meet the demand for simultaneous access. Additionally, considering the possibility of using udp in the future

No asynchronous io used

screen shot
https://gitee.com/cyqfj/esp32-rectify/blob/main/screen-shot.png
